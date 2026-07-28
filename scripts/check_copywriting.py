#!/usr/bin/env python3
import argparse
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = [
    *sorted(ROOT.glob("*.md")),
    *sorted((ROOT / "docs").rglob("*.md")),
]
CONFIG_FILES = [ROOT / "mkdocs.yml"]

CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
ASCII_WORD = r"A-Za-z0-9"
MIXED_SCRIPT = re.compile(
    rf"(?:[{CJK}][{ASCII_WORD}]|[{ASCII_WORD}][{CJK}])"
)
NUMBER_UNIT = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"\d+(?:\.\d+)?"
    r"(?:TiB|GiB|MiB|KiB|TB|GB|MB|KB|"
    r"Gbps|Mbps|Kbps|gbps|mbps|kbps|GHz|MHz|kHz|Hz|"
    r"FLOPS|IOPS|QPS|fps|dpi|px|pt|bytes?|bits?|"
    r"ms|μs|us|ns|min|kg|km|cm|mm)"
    r"(?![A-Za-z0-9_.-])"
)
FULLWIDTH_CLOSING = "，。！？；：、）》】〕”’"
FULLWIDTH_OPENING = "（《【〔“‘"
SPACE_BEFORE_PUNCTUATION = re.compile(
    rf"(?<=[^|\s])[ \t]+(?=[{FULLWIDTH_CLOSING}])"
)
SPACE_AFTER_PUNCTUATION = re.compile(
    rf"(?<=[{FULLWIDTH_CLOSING}])[ \t]+(?=[^|\s])"
)
SPACE_AFTER_OPENING = re.compile(
    rf"(?<=[{FULLWIDTH_OPENING}])[ \t]+(?=\S)"
)

FENCE = re.compile(r"^\s*(```+|~~~+)")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
INLINE_MATH = re.compile(r"(?<!\\)(\${1,2})(.+?)(?<!\\)\1")
PAREN_MATH = re.compile(r"\\\(.+?\\\)|\\\[.+?\\\]")
MARKDOWN_LINK = re.compile(
    r"(!?)\[([^\]]*)\]\((?:[^()\\]|\\.|\([^)]*\))*\)(?:\{[^}]*\})?"
)
REFERENCE_LINK = re.compile(r"(!?)\[([^\]]*)\]\[[^\]]+\]")
AUTOLINK = re.compile(r"<(?:https?://|mailto:)[^>]+>")
RAW_URL = re.compile(r"(?:https?://|www\.)[^\s<>)]+")
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
SVG_NON_TEXT = re.compile(r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>")
ATTRIBUTE_LIST = re.compile(r"\{[^{}]*\}")
HTML_ENTITY = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]+|#\d+|#x[0-9A-Fa-f]+);")
PATH = re.compile(
    r"(?P<prefix>^|[\s（《【〔“‘，。！？；：、])"
    r"(?P<path>(?:\.{0,2}/|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./-]+)"
)
ANCHOR = re.compile(r"(?<![A-Za-z0-9])#[A-Za-z][A-Za-z0-9_-]*")
MARKDOWN_MARKUP = re.compile(r"[*_~^=]+")
REFERENCE_DEFINITION = re.compile(r"^\s*\[[^\]]+\]:\s+\S+")
PLACEHOLDER = "\ue000"
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "body",
    "br",
    "dd",
    "details",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
PROTECTED_TAGS = {
    "code",
    "math",
    "mjx-container",
    "pre",
    "script",
    "style",
    "sup",
    "svg",
    "template",
}


def protected(_: re.Match[str]) -> str:
    return PLACEHOLDER


def inline_code_boundary(match: re.Match[str]) -> str:
    content = match.group(2)
    if re.search(r"[A-Za-z0-9]", content):
        return "A"
    return PLACEHOLDER


def path_boundary(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}A"


def visible_markdown(line: str) -> str:
    if REFERENCE_DEFINITION.match(line):
        return ""
    text = AUTOLINK.sub(protected, line)
    text = MARKDOWN_LINK.sub(
        lambda match: (
            f"{PLACEHOLDER}{match.group(2)}{PLACEHOLDER}"
            if match.group(1)
            else match.group(2)
        ),
        text,
    )
    text = REFERENCE_LINK.sub(
        lambda match: (
            f"{PLACEHOLDER}{match.group(2)}{PLACEHOLDER}"
            if match.group(1)
            else match.group(2)
        ),
        text,
    )
    text = INLINE_CODE.sub(inline_code_boundary, text)
    text = INLINE_MATH.sub(protected, text)
    text = PAREN_MATH.sub(protected, text)
    text = RAW_URL.sub(protected, text)
    text = PATH.sub(path_boundary, text)
    text = ANCHOR.sub(protected, text)
    text = ATTRIBUTE_LIST.sub(protected, text)
    text = HTML_ENTITY.sub(protected, text)
    text = HTML_TAG.sub("", text)
    text = MARKDOWN_MARKUP.sub("", text)
    return text


def visible_svg(line: str) -> str:
    text = SVG_NON_TEXT.sub(PLACEHOLDER, line)
    return PLACEHOLDER.join(re.findall(r">([^<>]+)<", text))


def find_issues(text: str) -> list[str]:
    issues: list[str] = []
    if MIXED_SCRIPT.search(text):
        issues.append("中文与英文或数字之间缺少空格")
    if NUMBER_UNIT.search(text):
        issues.append("数字与普通单位之间缺少空格")
    if (
        SPACE_BEFORE_PUNCTUATION.search(text)
        or SPACE_AFTER_PUNCTUATION.search(text)
        or SPACE_AFTER_OPENING.search(text)
    ):
        issues.append("全角标点旁存在多余空格")
    return issues


def check_markdown(path: Path) -> list[str]:
    errors: list[str] = []
    fence: str | None = None
    math_block = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fence_match = FENCE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence:
            continue
        stripped = line.strip()
        if stripped in {"$$", r"\[", r"\]"}:
            math_block = not math_block
            continue
        if math_block:
            continue
        for issue in find_issues(visible_markdown(line)):
            errors.append(f"{path.relative_to(ROOT)}:{number}: {issue}")
    return errors


def check_plain(path: Path, transform: Callable[[str], str]) -> list[str]:
    errors: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for issue in find_issues(transform(line)):
            errors.append(f"{path.relative_to(ROOT)}:{number}: {issue}")
    return errors


class VisibleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.protected_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag in PROTECTED_TAGS:
            self.protected_depth += 1
            self.chunks.append(PLACEHOLDER)
        elif self.protected_depth == 0 and "md-tag" in classes:
            self.chunks.append(PLACEHOLDER)
        elif self.protected_depth == 0 and tag in BLOCK_TAGS:
            self.chunks.append(PLACEHOLDER)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag in PROTECTED_TAGS:
            self.protected_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        if tag in PROTECTED_TAGS:
            if self.protected_depth:
                self.protected_depth -= 1
            self.chunks.append(PLACEHOLDER)
        elif self.protected_depth == 0 and tag in BLOCK_TAGS:
            self.chunks.append(PLACEHOLDER)

    def handle_data(self, data: str) -> None:
        if self.protected_depth == 0 and data.strip():
            self.chunks.append(data)


def check_rendered_html(site_dir: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    files = sorted(site_dir.rglob("*.html"))
    for path in files:
        parser = VisibleHTMLParser()
        parser.feed(path.read_text(encoding="utf-8"))
        text = "".join(parser.chunks)
        for issue in find_issues(text):
            errors.append(f"{path.relative_to(ROOT)}: {issue}")
    return errors, len(files)


parser = argparse.ArgumentParser()
parser.add_argument(
    "--site-dir",
    type=Path,
    help="同时检查 MkDocs 生成的 HTML",
)
args = parser.parse_args()

errors: list[str] = []
for file in MARKDOWN_FILES:
    errors.extend(check_markdown(file))
for file in CONFIG_FILES:
    errors.extend(check_plain(file, visible_markdown))

rendered_count = 0
if args.site_dir:
    site_dir = args.site_dir if args.site_dir.is_absolute() else ROOT / args.site_dir
    if not site_dir.is_dir():
        errors.append(f"{site_dir}: 生成站点目录不存在")
    else:
        rendered_errors, rendered_count = check_rendered_html(site_dir)
        errors.extend(rendered_errors)

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

total = len(MARKDOWN_FILES) + len(CONFIG_FILES)
suffix = f"，{rendered_count} 个生成页面" if args.site_dir else ""
print(f"文案排版检查通过：{total} 个读者可见源文件{suffix}")
