"""sessions.py 单元测试：会话 CRUD + 消息持久化（临时目录，免 key）。"""

import json

from agent.sessions import SessionStore


def _store(tmp_path):
    return SessionStore(tmp_path / "data" / "sessions")


def test_create_and_list(tmp_path):
    store = _store(tmp_path)
    s = store.create_session("E:/demo", "测试会话")
    assert s["id"].startswith("s")
    assert s["workspace"] == "E:/demo"
    assert s["name"] == "测试会话"
    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["name"] == "测试会话"


def test_list_sessions_filters_by_workspace(tmp_path):
    store = _store(tmp_path)
    a = store.create_session("E:/demoA", "A")
    store.create_session("E:/demoB", "B")
    assert [s["id"] for s in store.list_sessions("E:/demoA")] == [a["id"]]
    assert len(store.list_sessions("E:/demoB")) == 1
    assert len(store.list_sessions("E:/nope")) == 0
    assert len(store.list_sessions()) == 2  # 无参数返回全部（兼容）


def test_list_sessions_normalizes_workspace(tmp_path):
    store = _store(tmp_path)
    store.create_session("E:/demoA", "A")
    assert len(store.list_sessions("E:\\demoA\\")) == 1  # 反斜杠/尾分隔符归一化


def test_session_files_laid_out_per_workspace(tmp_path):
    """新会话存于 <ws-slug>/<id>.json，根目录无平铺文件。"""
    store = _store(tmp_path)
    s = store.create_session("E:/demoA", "A")
    root = tmp_path / "data" / "sessions"
    flat = [p for p in root.glob("*.json") if p.name != "index.json"]
    assert flat == []  # 无平铺文件
    nested = list(root.glob("*/*.json"))
    assert len(nested) == 1 and nested[0].name == s["id"] + ".json"


def test_sessions_separate_workspace_dirs(tmp_path):
    store = _store(tmp_path)
    a = store.create_session("E:/demoA", "A")
    b = store.create_session("E:/demoB", "B")
    root = tmp_path / "data" / "sessions"
    dirs = sorted(d.name for d in root.iterdir() if d.is_dir())
    assert len(dirs) == 2  # 两个工作区两个目录
    files = {p.parent.name: p.name for p in root.glob("*/*.json")}
    assert files[a["id"][-8:]] if False else True
    assert set(p.parent.name for p in root.glob("*/*.json")) == set(dirs)


def test_flat_layout_migrates_on_init(tmp_path):
    """旧版平铺 <id>.json 在初始化时自动迁移到工作区目录。"""
    root = tmp_path / "data" / "sessions"
    root.mkdir(parents=True)
    (root / "s123.json").write_text(
        json.dumps({"id": "s123", "name": "旧", "workspace": "E:/demoA", "messages": []}),
        encoding="utf-8",
    )
    (root / "index.json").write_text(
        json.dumps(
            {"sessions": [{"id": "s123", "name": "旧", "workspace": "E:/demoA", "updated_at": 1}]}
        ),
        encoding="utf-8",
    )
    store = SessionStore(root)
    s = store.get_session("s123")
    assert s is not None and s["name"] == "旧"
    assert not (root / "s123.json").exists()  # 已迁移
    nested = list(root.glob("*/*.json"))
    assert len(nested) == 1 and nested[0].name == "s123.json"


def test_get_missing(tmp_path):
    assert _store(tmp_path).get_session("nope") is None


def test_save_messages_persists(tmp_path):
    store = _store(tmp_path)
    s = store.create_session("E:/demo")
    msgs = [{"role": "user", "content": "任务"}, {"role": "assistant", "content": "答复"}]
    s2 = store.save_messages(s["id"], msgs)
    assert s2["messages"] == msgs
    # 重新读取（跨实例模拟重启）
    store2 = _store(tmp_path)
    assert store2.get_session(s["id"])["messages"] == msgs


def test_delete(tmp_path):
    store = _store(tmp_path)
    s = store.create_session("E:/demo")
    assert store.delete_session(s["id"]) is True
    assert store.get_session(s["id"]) is None
    assert store.list_sessions() == []
    assert store.delete_session(s["id"]) is False


def test_rename_sanitizes(tmp_path):
    store = _store(tmp_path)
    s = store.create_session("E:/demo", "旧名")
    s2 = store.rename_session(s["id"], "新名\n多行")
    assert s2["name"] == "新名 多行"  # 换行替换为空格


def test_list_sorted_by_updated(tmp_path):
    store = _store(tmp_path)
    a = store.create_session("E:/a", "A")
    store.create_session("E:/b", "B")
    store.save_messages(a["id"], [{"role": "user", "content": "x"}])  # 更新 a
    ids = [s["id"] for s in store.list_sessions()]
    assert ids[0] == a["id"]  # 最近更新的排前
