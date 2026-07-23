#!/usr/bin/env python3
from pathlib import Path
import ast
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "docs").rglob("*.md"))
FENCE = re.compile(r"^```python(?:\s+.*)?$")
snippets: list[tuple[Path, int, str]] = []

for path in FILES:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = 0
    block: list[str] = []
    in_python = False
    skip = False
    for number, line in enumerate(lines, 1):
        if not in_python and FENCE.match(line):
            in_python = True
            start = number
            block = []
            skip = number > 1 and lines[number - 2].strip() == "<!-- compile:skip -->"
        elif in_python and line == "```":
            if not skip:
                snippets.append((path, start, "\n".join(block) + "\n"))
            in_python = False
        elif in_python:
            block.append(line)

errors: list[str] = []
for path, line, source in snippets:
    try:
        ast.parse(source)
    except SyntaxError as error:
        errors.append(f"{path.relative_to(ROOT)}:{line + (error.lineno or 1)}: {error.msg}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Python 检查通过：{len(snippets)} 个代码块")
