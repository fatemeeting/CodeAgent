"""skills.py 单元测试：SKILL.md 解析 / 三级合并 / 匹配（临时目录，免 key）。"""

from pathlib import Path

import pytest

from agent.skills import (
    Skill,
    _load_dir,
    delete_workspace_skill,
    load_skills,
    match_skills,
    save_workspace_skill,
    skill_prompt,
    skill_summary,
    update_workspace_skill,
    valid_skill_name,
    workspace_skills_dir,
)


def _write_skill(root: Path, name: str, front: str, body: str = "指南正文") -> None:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(front + "\n" + body, encoding="utf-8")


def test_load_dir_parses_frontmatter(tmp_path):
    _write_skill(
        tmp_path,
        "demo",
        "---\nname: demo\ndescription: 演示技能\nkeywords: 演示, demo\nmodes: agent, chat\n---",
        "正文内容",
    )
    skills = _load_dir(tmp_path, "workspace")
    assert "demo" in skills
    s = skills["demo"]
    assert s.description == "演示技能"
    assert s.keywords == ["演示", "demo"]
    assert s.modes == ["agent", "chat"]
    assert s.body == "正文内容"
    assert s.source == "workspace"


def test_load_dir_supports_bracket_keywords(tmp_path):
    _write_skill(
        tmp_path,
        "bracket",
        "---\nkeywords: [测试, pytest]\ndescription: 测试技能\n---",
    )
    skills = _load_dir(tmp_path, "x")
    assert skills["bracket"].keywords == ["测试", "pytest"]


def test_load_dir_tolerates_bom(tmp_path):
    """Windows 记事本/Set-Content 的 UTF-8 BOM 应被容忍（utf-8-sig）。"""
    d = tmp_path / "bom"
    d.mkdir()
    (d / "SKILL.md").write_bytes(
        b"\xef\xbb\xbf" + "---\ndescription: BOM技能\n---\n正文".encode("utf-8")
    )
    skills = _load_dir(tmp_path, "x")
    assert skills["bom"].description == "BOM技能"
    assert skills["bom"].body == "正文"


def test_load_dir_skips_empty_and_missing(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    (d / "SKILL.md").write_text("", encoding="utf-8")  # 空技能跳过
    (tmp_path / "nodir").mkdir()  # 无 SKILL.md 的目录跳过
    skills = _load_dir(tmp_path, "x")
    assert "empty" not in skills
    assert "nodir" not in skills


def test_load_skills_merge_priority(monkeypatch, tmp_path):
    """工作区 > SKILLS_DIR > 内置（同名就近覆盖）。"""
    env = tmp_path / "env"
    ws = tmp_path / "ws"
    _write_skill(env, "demo", "---\ndescription: 外部版本\n---")
    _write_skill(ws / ".codeagent" / "skills", "demo", "---\ndescription: 工作区版本\n---")
    monkeypatch.setenv("SKILLS_DIR", str(env))
    skills = load_skills(workdir=str(ws))
    assert skills["demo"].description == "工作区版本"
    assert skills["demo"].source == "workspace"
    # 仅外部技能也可见
    _write_skill(env, "only-env", "---\ndescription: 仅外部\n---")
    skills2 = load_skills(workdir=str(ws))
    assert "only-env" in skills2 and skills2["only-env"].source == "env"


def test_match_skills_scores_and_caps(tmp_path):
    a = Skill(name="a", description="", keywords=["pytest"], body="A")
    b = Skill(name="b", description="", keywords=["测试"], body="B")
    c = Skill(name="c", description="", keywords=["无关"], body="C")
    skills = {"a": a, "b": b, "c": c}
    matched = match_skills(skills, "请为项目编写 pytest 测试")
    assert [s.name for s in matched] == ["a", "b"]  # 得分排序 + 上限 2（共 2 个命中）
    assert match_skills(skills, "随便聊聊") == []


def test_match_skills_mode_filter(tmp_path):
    agent_only = Skill(name="a", description="", keywords=["编辑"], body="A", modes=["agent"])
    chat_ok = Skill(name="b", description="", keywords=["编辑"], body="B", modes=["agent", "chat"])
    skills = {"a": agent_only, "b": chat_ok}
    matched = match_skills(skills, "编辑文件", mode="chat")
    assert [s.name for s in matched] == ["b"]  # chat 模式排除 agent-only


def test_skill_prompt_joins():
    s = Skill(name="demo", description="演示", body="正文")
    out = skill_prompt([s])
    assert "已装载技能" in out and "技能：demo" in out and "正文" in out
    assert skill_prompt([]) == ""


def test_skill_summary_and_workspace_dir(tmp_path):
    skills = {"b": Skill(name="b", description="B"), "a": Skill(name="a", description="A")}
    summary = skill_summary(skills)
    assert [s["name"] for s in summary] == ["a", "b"]  # 按名排序
    ws = str(workspace_skills_dir(str(tmp_path))).replace("\\", "/")
    assert ws.endswith(".codeagent/skills")


# ---------- 迭代 9 · 9.3：工作区级 CRUD 助手 ----------

def test_valid_skill_name():
    assert valid_skill_name("python-testing")
    assert valid_skill_name("a")
    assert valid_skill_name("x" * 40)
    assert not valid_skill_name("")
    assert not valid_skill_name("../evil")
    assert not valid_skill_name("a/b")
    assert not valid_skill_name("a\\b")
    assert not valid_skill_name("..")
    assert not valid_skill_name("x" * 41)
    assert not valid_skill_name("中文名")


def test_workspace_skill_save_update_delete(tmp_path):
    summary = save_workspace_skill(tmp_path, "demo", "演示", ["pytest"], ["agent", "chat"], "正文")
    assert summary["name"] == "demo" and summary["source"] == "workspace"
    assert summary["description"] == "演示" and summary["modes"] == ["agent", "chat"]
    md = tmp_path / ".codeagent" / "skills" / "demo" / "SKILL.md"
    assert md.is_file() and "正文" in md.read_text(encoding="utf-8")
    # 重名新建报错
    with pytest.raises(ValueError):
        save_workspace_skill(tmp_path, "demo", "重复")
    # 更新覆盖；不存在报错
    updated = update_workspace_skill(tmp_path, "demo", "新描述", [], ["agent"], "新正文")
    assert updated["description"] == "新描述"
    assert "新正文" in md.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        update_workspace_skill(tmp_path, "ghost", "x")
    # 删除后二次删除返回 False
    assert delete_workspace_skill(tmp_path, "demo") is True
    assert not md.exists()
    assert delete_workspace_skill(tmp_path, "demo") is False


def test_workspace_skill_invalid_names(tmp_path):
    for bad in ["", "../evil", "a/b", "..", "x" * 41, "中文"]:
        with pytest.raises(ValueError):
            save_workspace_skill(tmp_path, bad, "x")
    assert delete_workspace_skill(tmp_path, "../evil") is False  # 越界删除拒绝
