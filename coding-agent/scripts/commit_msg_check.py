"""commit-msg 钩子：要求提交信息包含阶段名。

用法：由 scripts/install_hooks.py 安装为 .git/hooks/commit-msg；
git 会把提交信息文件路径作为第一个参数传入。
退出码 0 = 通过；1 = 拦截。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STAGE_RE = re.compile(r"阶段\s?\d|stage\s?\d", re.IGNORECASE)


def main() -> int:
    if len(sys.argv) < 2:
        print("commit-msg：缺少提交信息文件参数")
        return 1
    msg = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").strip()
    if not msg:
        print("提交信息为空")
        return 1
    if not STAGE_RE.search(msg):
        print(f"提交信息需包含阶段名（如「阶段2：工具层」）：{msg!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
