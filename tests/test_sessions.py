"""sessions.py 单元测试：会话 CRUD + 消息持久化（临时目录，免 key）。"""

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
