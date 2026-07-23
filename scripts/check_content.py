#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
FENCE = re.compile(r"^```")
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "macOS home path": re.compile(r"/Users/[^/\s]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
}
errors: list[str] = []

for path in FILES:
    lines = path.read_text(encoding="utf-8").splitlines()
    open_fence = 0
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            open_fence = 0 if open_fence else number
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                errors.append(f"{path.relative_to(ROOT)}:{number}: 检测到 {name} 模式")
    if open_fence:
        errors.append(f"{path.relative_to(ROOT)}:{open_fence}: 代码块未闭合")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"内容检查通过：{len(FILES)} 个 Markdown 文件")
