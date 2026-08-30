"""技能系统：SKILL.md 解析与匹配（零新依赖）。

技能 = 目录 + SKILL.md（轻量 frontmatter：name/description/keywords/modes + 指南正文）。
三级目录（就近覆盖，按 name 去重）：
- 内置：项目 skills/<name>/SKILL.md（只读，随发行）
- SKILLS_DIR 外部目录（只读，跨项目共享，环境变量配置）
- 工作区级：<workdir>/.codeagent/skills/<name>/SKILL.md（可写，用户增删改，文件树可见）
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MAX_SKILL_BODY = 4000  # 注入正文上限（防提示膨胀）
MAX_MATCH = 2  # 自动匹配最多注入的技能数
MAX_NAME_LEN = 40  # 技能名上限

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
_SKILL_NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")


@dataclass
class Skill:
    name: str
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    body: str = ""
    source: str = "builtin"  # builtin | env | workspace
    modes: list[str] = field(default_factory=lambda: ["agent"])  # 可用模式（默认仅 agent）
    error: str = ""  # 解析失败信息（列表标注用）


def _split_list(raw: str) -> list[str]:
    """解析逗号分隔或 [a, b] 形式的列表字段。"""
    v = (raw or "").strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [w.strip() for w in re.split(r"[,，]", v) if w.strip()]


def _parse_skill(dir_path: Path, source: str) -> Skill | None:
    md = dir_path / "SKILL.md"
    if not md.is_file():
        return None
    try:
        text = md.read_text(encoding="utf-8-sig")  # utf-8-sig 容忍 Windows BOM
    except OSError:
        return None
    meta: dict[str, str] = {}
    body = text.strip()
    m = _FRONTMATTER_RE.match(text)
    if m:
        body = m.group(2).strip()
        for line in m.group(1).splitlines():
            line = line.strip()
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
    description = meta.get("description", "").strip()
    keywords = _split_list(meta.get("keywords", ""))
    modes = _split_list(meta.get("modes", "agent")) or ["agent"]
    body = body[:MAX_SKILL_BODY]
    if not description and not keywords and not body:
        return None  # 空技能跳过
    return Skill(
        name=dir_path.name,
        description=description,
        keywords=keywords,
        body=body,
        source=source,
        modes=modes,
    )


def _load_dir(root: Path, source: str) -> dict[str, Skill]:
    found: dict[str, Skill] = {}
    if not root.is_dir():
        return found
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        skill = _parse_skill(child, source)
        if skill is not None:
            found[skill.name] = skill
    return found


def workspace_skills_dir(workdir: str | Path) -> Path:
    """工作区级技能目录（用户可增删改，文件树可见）。"""
    return Path(workdir) / ".codeagent" / "skills"


def load_skills(workdir: str | Path = ".") -> dict[str, Skill]:
    """三级目录合并：内置 < SKILLS_DIR < 工作区（就近覆盖）。"""
    builtin = Path(__file__).resolve().parent.parent / "skills"
    merged = _load_dir(builtin, "builtin")
    env_dir = os.environ.get("SKILLS_DIR", "").strip()
    if env_dir:
        merged.update(_load_dir(Path(env_dir), "env"))
    merged.update(_load_dir(workspace_skills_dir(workdir), "workspace"))
    return merged


def match_skills(skills: dict[str, Skill], task: str, mode: str = "agent") -> list[Skill]:
    """按关键词/描述匹配，得分排序，最多 MAX_MATCH 个；仅返回与 mode 兼容的技能。

    注意：当前产品策略为「技能仅显式指定装载」，本函数不接入 run()，
    保留作为后续「推荐技能」功能的预留。
    """
    text = task.lower()
    scored: list[tuple[int, str]] = []
    for name, skill in skills.items():
        if mode not in skill.modes:
            continue
        score = 0
        for kw in skill.keywords:
            if kw and kw.lower() in text:
                score += 3
        for word in skill.description.split():
            if len(word) >= 2 and word.lower() in text:
                score += 1
        if score > 0:
            scored.append((score, name))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [skills[name] for _, name in scored[:MAX_MATCH]]


def skill_prompt(skills: list[Skill]) -> str:
    """把已装载技能拼成 system 注入片段。"""
    if not skills:
        return ""
    parts = ["\n\n# 已装载技能（按其规范执行）"]
    for s in skills:
        parts.append(f"## 技能：{s.name}\n{s.description}\n\n{s.body}")
    return "\n".join(parts)


def skill_summary(skills: dict[str, Skill]) -> list[dict[str, Any]]:
    """技能列表摘要（GET /skills 用）：name/description/keywords/modes/source。"""
    return [
        {
            "name": s.name,
            "description": s.description,
            "keywords": s.keywords,
            "modes": s.modes,
            "source": s.source,
        }
        for s in sorted(skills.values(), key=lambda x: x.name)
    ]


def valid_skill_name(name: str) -> bool:
    """技能名校验：仅字母/数字/下划线/连字符，1–40 字符（防路径穿越）。"""
    return bool(_SKILL_NAME_RE.match(name or ""))


def _format_skill_md(
    name: str,
    description: str,
    keywords: list[str],
    modes: list[str],
    body: str,
) -> str:
    """把表单字段序列化为 SKILL.md 文本（UTF-8，无 BOM）。"""
    kw = ", ".join(keywords)
    mode_str = ", ".join(modes) if modes else "agent"
    body_text = body.strip()[:MAX_SKILL_BODY]
    lines = ["---", f"name: {name}", f"description: {description}", f"keywords: {kw}", f"modes: {mode_str}", "---"]
    if body_text:
        lines.append("")
        lines.append(body_text)
    return "\n".join(lines) + "\n"


def _workspace_skill_dir(workdir: str | Path, name: str) -> Path:
    """工作区技能目录（带名称校验 + 越界防护）。"""
    if not valid_skill_name(name):
        raise ValueError("技能名仅限字母、数字、-、_，长度 1–40")
    root = workspace_skills_dir(workdir).resolve()
    target = (root / name).resolve()
    if not target.is_relative_to(root):
        raise ValueError("非法技能路径")
    return target


def save_workspace_skill(
    workdir: str | Path,
    name: str,
    description: str = "",
    keywords: list[str] | None = None,
    modes: list[str] | None = None,
    body: str = "",
) -> dict[str, Any]:
    """新建工作区级技能（写入 <workdir>/.codeagent/skills/<name>/SKILL.md）。"""
    target = _workspace_skill_dir(workdir, name)
    if target.exists():
        raise ValueError(f"技能已存在：{name}")
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        _format_skill_md(name, description, list(keywords or []), list(modes or []) or ["agent"], body),
        encoding="utf-8",
    )
    skill = _parse_skill(target, "workspace")
    if skill is None:
        raise ValueError("技能写入失败")
    return skill_summary({skill.name: skill})[0]


def update_workspace_skill(
    workdir: str | Path,
    name: str,
    description: str = "",
    keywords: list[str] | None = None,
    modes: list[str] | None = None,
    body: str = "",
) -> dict[str, Any]:
    """更新工作区级技能（覆盖 SKILL.md；仅允许工作区级目录）。"""
    target = _workspace_skill_dir(workdir, name)
    if not (target / "SKILL.md").is_file():
        raise ValueError(f"技能不存在：{name}")
    (target / "SKILL.md").write_text(
        _format_skill_md(name, description, list(keywords or []), list(modes or []) or ["agent"], body),
        encoding="utf-8",
    )
    skill = _parse_skill(target, "workspace")
    if skill is None:
        raise ValueError("技能写入失败")
    return skill_summary({skill.name: skill})[0]


def delete_workspace_skill(workdir: str | Path, name: str) -> bool:
    """删除工作区级技能目录；仅限工作区技能根内、名称合法才动手。"""
    if not valid_skill_name(name):
        return False
    root = workspace_skills_dir(workdir).resolve()
    target = (root / name).resolve()
    if not target.is_relative_to(root) or not target.is_dir():
        return False
    shutil.rmtree(target)
    return True
