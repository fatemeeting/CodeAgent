"""确定性 pre-commit 检查：拦截 .env 入库、扫描疑似 API Key、检查 gate 文件存在。

用法：由 scripts/install_hooks.py 安装为 .git/hooks/pre-commit。
退出码 0 = 通过；1 = 拦截。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# DeepSeek / OpenAI 的 key 形如 "sk-" + 长字符串；占位符（如 16 个 x）不会被 {24,} 命中
SECRET_RE = re.compile(r"sk-[A-Za-z0-9]{24,}")
GATE_FILES = ["SPEC.md", "CHECKLIST.md", "AGENTS.md"]


def _run_git(args: list[str]) -> str:
    out = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return out.stdout.strip()


def _repo_root() -> Path:
    # scripts/gate_check.py 位于仓库根的 scripts/ 下，用 __file__ 定位与 CWD 无关
    return Path(__file__).resolve().parent.parent


def staged_files() -> list[str]:
    return [ln for ln in _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACM"]).splitlines() if ln]


def main() -> int:
    root = _repo_root()
    files = staged_files()
    problems: list[str] = []

    # 1) .env 绝不能入库
    for f in files:
        if Path(f).name == ".env" or f.endswith(".env"):
            problems.append(f".env 文件被暂存，禁止提交：{f}")

    # 2) 疑似密钥扫描（跳过 *.example 模板）
    for f in files:
        p = root / f
        if not p.is_file() or p.name.endswith(".example"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if SECRET_RE.search(line):
                problems.append(f"疑似 API Key：{f}:{i}")

    # 3) gate 文件存在
    for gf in GATE_FILES:
        if not (root / gf).is_file():
            problems.append(f"缺少 gate 文件：{gf}")

    if problems:
        print("pre-commit 检查未通过：")
        for p in problems:
            print("  -", p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
