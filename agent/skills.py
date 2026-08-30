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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MAX_SKILL_BODY = 4000  # 注入正文上限（防提示膨胀）
MAX_MATCH = 2  # 自动匹配最多注入的技能数

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


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
        text = md.read_text(encoding="utf-8")
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
