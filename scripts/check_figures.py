#!/usr/bin/env python3
"""Validate figure provenance, assets, placements, references, and rendered HTML."""

from __future__ import annotations

import argparse
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Optional
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FIGURES = DOCS / "assets" / "figures"
MANIFEST = FIGURES / "manifest.json"
NOTICE = ROOT / "FIGURE_NOTICE.md"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FIGURE_BLOCK = re.compile(
    r"<figure\b(?P<attrs>[^>]*)>(?P<body>.*?)</figure>", re.DOTALL
)
HTML_ATTR = re.compile(
    r"""(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*)
        (?:\s*=\s*(?:"(?P<double>[^"]*)"|'(?P<single>[^']*)'))?""",
    re.VERBOSE,
)
MARKDOWN_MEDIA = re.compile(
    r"\[!\[(?P<alt>[^\]]+)\]\((?P<image>[^)\s]+)\)"
    r"\{(?P<image_attrs>[^}]*)\}\]"
    r"\((?P<link>[^)\s]+)\)\{(?P<link_attrs>[^}]*)\}"
)
MARKDOWN_ATTR = re.compile(
    r"""(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*|\.[A-Za-z0-9_-]+)
        (?:=(?:"(?P<double>[^"]*)"|'(?P<single>[^']*)'|(?P<bare>[^\s]+)))?""",
    re.VERBOSE,
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((https://[^)\s]+)\)")
EXTERNAL_IMAGE = re.compile(r"!\[[^\]]*\]\((?:https?:)?//", re.IGNORECASE)
RAW_EXTERNAL_IMAGE = re.compile(
    r"<img\b[^>]*\bsrc\s*=\s*[\"'](?:https?:)?//", re.IGNORECASE
)
REFERENCE_HEADING = re.compile(r"(?m)^##\s+Reference\s*$")
H2 = re.compile(r"(?m)^##\s+(.+?)\s*$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FORBIDDEN_PNG_CHUNKS = {"tEXt", "zTXt", "iTXt", "eXIf"}
FORBIDDEN_SVG_TAGS = {"script", "foreignObject", "image", "iframe", "object", "embed"}
SENSITIVE_PATTERNS = {
    "flag-like value": re.compile(r"(?i)\b(?:flag|ctf)\{[^}]{3,}\}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "macOS home path": re.compile(r"/Users/[^/\s]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
}


class DuplicateKeyError(ValueError):
    pass


def duplicate_safe_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def parse_html_attrs(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in HTML_ATTR.finditer(raw):
        value = match.group("double")
        if value is None:
            value = match.group("single")
        attrs[match.group("name")] = value or ""
    return attrs


def parse_markdown_attrs(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    classes: list[str] = []
    for match in MARKDOWN_ATTR.finditer(raw):
        name = match.group("name")
        if name.startswith("."):
            classes.append(name[1:])
            continue
        value = match.group("double")
        if value is None:
            value = match.group("single")
        if value is None:
            value = match.group("bare")
        attrs[name] = value or ""
    if classes:
        attrs["class"] = " ".join(classes)
    return attrs


def expect_keys(
    value: dict[str, Any],
    label: str,
    required: set[str],
    optional: set[str],
    errors: list[str],
) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing:
        errors.append(f"{label}: missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label}: unknown fields: {', '.join(unknown)}")


def valid_https(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def scan_sensitive(text: str, label: str, errors: list[str]) -> None:
    for name, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"{label}: detected {name}")


def inspect_png(path: Path, errors: list[str]) -> tuple[int, int]:
    data = path.read_bytes()
    label = path.relative_to(ROOT)
    if not data.startswith(PNG_SIGNATURE):
        errors.append(f"{label}: invalid PNG signature")
        return 0, 0
    cursor = len(PNG_SIGNATURE)
    width = height = 0
    chunks: list[str] = []
    while cursor + 12 <= len(data):
        length = struct.unpack(">I", data[cursor : cursor + 4])[0]
        kind = data[cursor + 4 : cursor + 8].decode("ascii", errors="replace")
        chunks.append(kind)
        payload = data[cursor + 8 : cursor + 8 + length]
        if kind == "IHDR" and len(payload) >= 8:
            width, height = struct.unpack(">II", payload[:8])
        cursor += 12 + length
        if kind == "IEND":
            break
    forbidden = sorted(set(chunks) & FORBIDDEN_PNG_CHUNKS)
    if forbidden:
        errors.append(f"{label}: forbidden metadata chunks: {', '.join(forbidden)}")
    if chunks[-1:] != ["IEND"]:
        errors.append(f"{label}: missing IEND")
    return width, height


def inspect_svg(path: Path, errors: list[str]) -> tuple[int, int, str]:
    label = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    scan_sensitive(text, str(label), errors)
    lowered = text.lower()
    if "javascript:" in lowered or re.search(r"url\(\s*['\"]?https?://", lowered):
        errors.append(f"{label}: external or executable SVG reference")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        errors.append(f"{label}: invalid SVG XML: {error}")
        return 0, 0, ""
    if local_name(root.tag) != "svg":
        errors.append(f"{label}: root element is not svg")
    for element in root.iter():
        tag = local_name(element.tag)
        if tag in FORBIDDEN_SVG_TAGS:
            errors.append(f"{label}: forbidden SVG element <{tag}>")
        for name, value in element.attrib.items():
            attribute = local_name(name).lower()
            if attribute.startswith("on") or attribute in {"href", "src"}:
                errors.append(f"{label}: forbidden SVG attribute {attribute}")
            scan_sensitive(value, f"{label}:{tag}@{attribute}", errors)
    titles = [
        (element.text or "").strip()
        for element in root.iter()
        if local_name(element.tag) == "title"
    ]
    descriptions = [
        (element.text or "").strip()
        for element in root.iter()
        if local_name(element.tag) == "desc"
    ]
    if not any(titles) or not any(descriptions):
        errors.append(f"{label}: SVG requires non-empty title and desc")
    width_match = re.fullmatch(r"(\d+)(?:px)?", root.attrib.get("width", ""))
    height_match = re.fullmatch(r"(\d+)(?:px)?", root.attrib.get("height", ""))
    width = int(width_match.group(1)) if width_match else 0
    height = int(height_match.group(1)) if height_match else 0
    if width <= 0 or height <= 0:
        errors.append(f"{label}: SVG requires positive integer width and height")
    return width, height, " ".join(root.itertext())


def resolve_local(page: Path, target: str) -> Optional[Path]:
    split = urlsplit(unescape(target))
    if split.scheme or split.netloc:
        return None
    return (page.parent / unquote(split.path)).resolve()


def generated_path(site_dir: Path, page: str) -> Path:
    relative = Path(page).relative_to("docs")
    if relative == Path("index.md"):
        return site_dir / "index.html"
    if relative.name == "index.md":
        return site_dir / relative.parent / "index.html"
    return site_dir / relative.with_suffix("") / "index.html"


class RenderedFigureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.figures: list[dict[str, Any]] = []
        self.current: Optional[dict[str, Any]] = None
        self.caption_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, Optional[str]]]
    ) -> None:
        values = {name: value or "" for name, value in attrs}
        if tag == "figure":
            self.current = {
                "attrs": values,
                "images": [],
                "links": [],
                "caption": [],
            }
            self.figures.append(self.current)
        elif self.current is not None and tag == "img":
            self.current["images"].append(values)
        elif self.current is not None and tag == "a":
            self.current["links"].append(values)
        elif self.current is not None and tag == "figcaption":
            self.caption_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "figcaption" and self.caption_depth:
            self.caption_depth -= 1
        elif tag == "figure":
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None and self.caption_depth:
            self.current["caption"].append(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        manifest = json.loads(
            MANIFEST.read_text(encoding="utf-8"),
            object_pairs_hook=duplicate_safe_object,
        )
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as error:
        print(f"{MANIFEST}: {error}", file=sys.stderr)
        return 1
    if not isinstance(manifest, dict):
        print(f"{MANIFEST}: root must be an object", file=sys.stderr)
        return 1
    expect_keys(
        manifest,
        "manifest",
        {"schema_version", "verified", "sources", "assets", "coverage"},
        set(),
        errors,
    )
    if manifest.get("schema_version") != 1:
        errors.append("manifest: schema_version must be 1")
    sources: dict[str, dict[str, Any]] = {}
    for index, source_value in enumerate(manifest.get("sources", [])):
        label = f"sources[{index}]"
        if not isinstance(source_value, dict):
            errors.append(f"{label}: must be an object")
            continue
        expect_keys(
            source_value,
            label,
            {
                "id",
                "kind",
                "title",
                "canonical_url",
                "artifact_url",
                "artifact_sha256",
                "revision",
                "retrieved",
                "creator",
                "license",
            },
            set(),
            errors,
        )
        source_id = source_value.get("id")
        if not isinstance(source_id, str) or not SLUG.fullmatch(source_id):
            errors.append(f"{label}.id: invalid slug")
            continue
        if source_id in sources:
            errors.append(f"{label}.id: duplicate {source_id}")
        sources[source_id] = source_value
        for field in ("canonical_url", "artifact_url"):
            if not valid_https(source_value.get(field)):
                errors.append(f"{label}.{field}: must be an HTTPS URL")
        if not SHA256.fullmatch(str(source_value.get("artifact_sha256", ""))):
            errors.append(f"{label}.artifact_sha256: invalid SHA-256")
        license_value = source_value.get("license")
        if not isinstance(license_value, dict):
            errors.append(f"{label}.license: must be an object")
        else:
            expect_keys(
                license_value,
                f"{label}.license",
                {"name", "url", "credit"},
                set(),
                errors,
            )
            if not valid_https(license_value.get("url")):
                errors.append(f"{label}.license.url: must be an HTTPS URL")
    assets: dict[str, dict[str, Any]] = {}
    registered_files: set[Path] = set()
    expected_placements: dict[tuple[str, str], str] = {}
    asset_hashes: dict[str, str] = {}
    for index, asset_value in enumerate(manifest.get("assets", [])):
        label = f"assets[{index}]"
        if not isinstance(asset_value, dict):
            errors.append(f"{label}: must be an object")
            continue
        common = {
            "id",
            "file",
            "origin",
            "format",
            "dimensions",
            "sha256",
            "title",
            "alt",
            "placements",
        }
        origin = asset_value.get("origin")
        required = common | ({"license"} if origin == "original" else {
            "source_id",
            "source_label",
            "transform",
            "visible_text",
        })
        expect_keys(asset_value, label, required, set(), errors)
        asset_id = asset_value.get("id")
        if not isinstance(asset_id, str) or not SLUG.fullmatch(asset_id):
            errors.append(f"{label}.id: invalid slug")
            continue
        if asset_id in assets:
            errors.append(f"{label}.id: duplicate {asset_id}")
        assets[asset_id] = asset_value
        if origin not in {"original", "external"}:
            errors.append(f"{label}.origin: must be original or external")
        if origin == "original" and asset_value.get("license") != "MIT":
            errors.append(f"{label}.license: original assets must declare MIT")
        if origin == "external":
            source_id = asset_value.get("source_id")
            if source_id not in sources:
                errors.append(f"{label}.source_id: unknown source {source_id!r}")
            scan_sensitive(str(asset_value.get("visible_text", "")), label, errors)
        relative = asset_value.get("file")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            errors.append(f"{label}.file: unsafe path")
            continue
        path = (FIGURES / relative).resolve()
        if FIGURES.resolve() not in path.parents or not path.is_file():
            errors.append(f"{label}.file: missing file {relative}")
            continue
        registered_files.add(path)
        actual_hash = digest(path)
        expected_hash = str(asset_value.get("sha256", ""))
        if not SHA256.fullmatch(expected_hash) or actual_hash != expected_hash:
            errors.append(f"{label}.sha256: expected {expected_hash}, got {actual_hash}")
        previous = asset_hashes.get(actual_hash)
        if previous:
            errors.append(f"{label}: duplicate binary content with {previous}")
        asset_hashes[actual_hash] = asset_id
        format_name = asset_value.get("format")
        if format_name == "PNG" and path.suffix == ".png":
            width, height = inspect_png(path, errors)
        elif format_name == "SVG" and path.suffix == ".svg":
            width, height, visible = inspect_svg(path, errors)
            scan_sensitive(visible, str(path.relative_to(ROOT)), errors)
        else:
            errors.append(f"{label}: format and suffix disagree")
            width = height = 0
        dimensions = asset_value.get("dimensions")
        if dimensions != [width, height]:
            errors.append(
                f"{label}.dimensions: expected {[width, height]}, got {dimensions!r}"
            )
        alt = asset_value.get("alt")
        if not isinstance(alt, str) or len(alt.strip()) < 12:
            errors.append(f"{label}.alt: must be descriptive")
        placements = asset_value.get("placements")
        if not isinstance(placements, list) or not placements:
            errors.append(f"{label}.placements: requires at least one placement")
            continue
        for placement_index, placement in enumerate(placements):
            placement_label = f"{label}.placements[{placement_index}]"
            if not isinstance(placement, dict):
                errors.append(f"{placement_label}: must be an object")
                continue
            expect_keys(
                placement,
                placement_label,
                {"page", "figure_id", "role"},
                set(),
                errors,
            )
            page = placement.get("page")
            figure_id = placement.get("figure_id")
            if not isinstance(page, str) or not (ROOT / page).is_file():
                errors.append(f"{placement_label}.page: missing Markdown page")
            if (
                not isinstance(figure_id, str)
                or not figure_id.startswith("fig-")
                or not SLUG.fullmatch(figure_id)
            ):
                errors.append(f"{placement_label}.figure_id: invalid stable id")
            key = (str(page), str(figure_id))
            if key in expected_placements:
                errors.append(f"{placement_label}: duplicate placement {key}")
            expected_placements[key] = asset_id
    disk_assets = {
        path.resolve()
        for path in FIGURES.glob("*/*")
        if path.suffix.lower() in {".png", ".svg", ".jpg", ".jpeg", ".webp"}
    }
    for orphan in sorted(disk_assets - registered_files):
        errors.append(f"{orphan.relative_to(ROOT)}: unregistered figure asset")
    for missing in sorted(registered_files - disk_assets):
        errors.append(f"{missing.relative_to(ROOT)}: registered asset not found")
    coverage_values = manifest.get("coverage", [])
    coverage: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(coverage_values):
        label = f"coverage[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        expect_keys(
            item,
            label,
            {"page", "status", "requires_reference", "reason"},
            set(),
            errors,
        )
        page = item.get("page")
        if not isinstance(page, str):
            errors.append(f"{label}.page: must be a string")
            continue
        if page in coverage:
            errors.append(f"{label}.page: duplicate {page}")
        coverage[page] = item
        if item.get("status") not in {"figure", "exception"}:
            errors.append(f"{label}.status: invalid value")
        if not isinstance(item.get("requires_reference"), bool):
            errors.append(f"{label}.requires_reference: must be boolean")
        if not isinstance(item.get("reason"), str) or len(item["reason"]) < 12:
            errors.append(f"{label}.reason: requires a meaningful reason")
    markdown_pages = {
        str(path.relative_to(ROOT)) for path in sorted(DOCS.rglob("*.md"))
    }
    if set(coverage) != markdown_pages:
        for page in sorted(markdown_pages - set(coverage)):
            errors.append(f"{page}: missing figure-coverage decision")
        for page in sorted(set(coverage) - markdown_pages):
            errors.append(f"{page}: coverage entry has no Markdown page")
    actual_placements: dict[tuple[str, str], str] = {}
    for page_string in sorted(markdown_pages):
        page = ROOT / page_string
        text = page.read_text(encoding="utf-8")
        if EXTERNAL_IMAGE.search(text) or RAW_EXTERNAL_IMAGE.search(text):
            errors.append(f"{page_string}: remote image hotlink is forbidden")
        blocks = list(FIGURE_BLOCK.finditer(text))
        item = coverage.get(page_string, {})
        if item.get("status") == "figure" and not blocks:
            errors.append(f"{page_string}: coverage requires a figure")
        if item.get("status") == "exception" and blocks:
            errors.append(f"{page_string}: coverage exception contains a figure")
        if item.get("requires_reference"):
            headings = H2.findall(text)
            if not headings or headings[-1].strip() != "Reference":
                errors.append(f"{page_string}: final H2 must be Reference")
            reference_match = REFERENCE_HEADING.search(text)
            reference_text = text[reference_match.end() :] if reference_match else ""
            if len(MARKDOWN_LINK.findall(reference_text)) < 2:
                errors.append(f"{page_string}: Reference needs at least two HTTPS links")
        for block in blocks:
            attrs = parse_html_attrs(block.group("attrs"))
            figure_id = attrs.get("id", "")
            asset_id = attrs.get("data-asset", "")
            key = (page_string, figure_id)
            if key in actual_placements:
                errors.append(f"{page_string}: duplicate figure id {figure_id}")
            actual_placements[key] = asset_id
            if "ctf-figure" not in attrs.get("class", "").split():
                errors.append(f"{page_string}#{figure_id}: missing ctf-figure class")
            if attrs.get("markdown") != "1":
                errors.append(f"{page_string}#{figure_id}: figure must use markdown=1")
            asset = assets.get(asset_id)
            if asset is None:
                errors.append(f"{page_string}#{figure_id}: unknown data-asset")
                continue
            expected_source = asset.get("source_id", "")
            if attrs.get("data-source", "") != expected_source:
                errors.append(f"{page_string}#{figure_id}: data-source mismatch")
            media = MARKDOWN_MEDIA.search(block.group("body"))
            if media is None:
                errors.append(f"{page_string}#{figure_id}: missing linked Markdown image")
                continue
            image_attrs = parse_markdown_attrs(media.group("image_attrs"))
            link_attrs = parse_markdown_attrs(media.group("link_attrs"))
            if "ctf-figure__media" not in link_attrs.get("class", "").split():
                errors.append(f"{page_string}#{figure_id}: media link needs class")
            if media.group("alt") != asset.get("alt"):
                errors.append(f"{page_string}#{figure_id}: alt differs from manifest")
            expected_width, expected_height = asset.get("dimensions", [0, 0])
            for field, expected in (
                ("width", expected_width),
                ("height", expected_height),
            ):
                if image_attrs.get(field) != str(expected):
                    errors.append(f"{page_string}#{figure_id}: {field} mismatch")
            if image_attrs.get("loading") not in {"lazy", "eager"}:
                errors.append(f"{page_string}#{figure_id}: missing loading policy")
            if image_attrs.get("decoding") != "async":
                errors.append(f"{page_string}#{figure_id}: decoding must be async")
            image_path = resolve_local(page, media.group("image"))
            expected_path = (FIGURES / asset["file"]).resolve()
            if image_path != expected_path:
                errors.append(f"{page_string}#{figure_id}: image path mismatch")
            caption_match = re.search(
                r"<figcaption>(?P<caption>.*?)</figcaption>",
                block.group("body"),
                re.DOTALL,
            )
            if caption_match is None or len(
                re.sub(r"<[^>]+>", "", caption_match.group("caption")).strip()
            ) < 20:
                errors.append(f"{page_string}#{figure_id}: caption is missing or thin")
            if asset.get("origin") == "original":
                if resolve_local(page, media.group("link")) != expected_path:
                    errors.append(f"{page_string}#{figure_id}: original must link to asset")
            else:
                source = sources.get(asset.get("source_id"), {})
                body = unescape(block.group("body"))
                if media.group("link") not in {
                    source.get("canonical_url"),
                    source.get("artifact_url"),
                    source.get("artifact_url") + "#page=25",
                }:
                    errors.append(f"{page_string}#{figure_id}: media link is not fixed source")
                if source.get("license", {}).get("url", "") not in body:
                    errors.append(f"{page_string}#{figure_id}: caption lacks license link")
                if not (
                    source.get("canonical_url", "") in body
                    or source.get("artifact_url", "") in body
                ):
                    errors.append(f"{page_string}#{figure_id}: caption lacks source link")
    if actual_placements != expected_placements:
        for key, asset_id in sorted(expected_placements.items()):
            if actual_placements.get(key) != asset_id:
                errors.append(f"{key[0]}#{key[1]}: manifest placement not matched")
        for key, asset_id in sorted(actual_placements.items()):
            if expected_placements.get(key) != asset_id:
                errors.append(f"{key[0]}#{key[1]}: unregistered placement")
    notice = NOTICE.read_text(encoding="utf-8") if NOTICE.is_file() else ""
    for asset in assets.values():
        if asset.get("origin") != "external":
            continue
        source = sources.get(asset.get("source_id"), {})
        for needle in (
            f"docs/assets/figures/{asset.get('file')}",
            source.get("canonical_url", ""),
            source.get("license", {}).get("url", ""),
        ):
            if needle and needle not in notice:
                errors.append(f"FIGURE_NOTICE.md: missing {asset.get('id')} provenance")
    scan_sensitive(notice, "FIGURE_NOTICE.md", errors)
    if args.site_dir is not None:
        site_dir = args.site_dir.resolve()
        for page_string, item in coverage.items():
            output = generated_path(site_dir, page_string)
            if not output.is_file():
                errors.append(f"{page_string}: generated HTML missing at {output}")
                continue
            html = output.read_text(encoding="utf-8")
            parser_html = RenderedFigureParser()
            parser_html.feed(html)
            by_id = {
                figure["attrs"].get("id", ""): figure
                for figure in parser_html.figures
                if "ctf-figure" in figure["attrs"].get("class", "").split()
            }
            expected_for_page = {
                figure_id: asset_id
                for (page, figure_id), asset_id in expected_placements.items()
                if page == page_string
            }
            if set(by_id) != set(expected_for_page):
                errors.append(f"{page_string}: rendered figure ids differ from manifest")
            for figure_id, asset_id in expected_for_page.items():
                figure = by_id.get(figure_id)
                if figure is None:
                    continue
                if figure["attrs"].get("data-asset") != asset_id:
                    errors.append(f"{page_string}#{figure_id}: rendered asset mismatch")
                images = figure["images"]
                if len(images) != 1:
                    errors.append(f"{page_string}#{figure_id}: rendered image count is not one")
                    continue
                image = images[0]
                asset = assets[asset_id]
                if image.get("alt") != asset.get("alt"):
                    errors.append(f"{page_string}#{figure_id}: rendered alt mismatch")
                width, height = asset.get("dimensions", [0, 0])
                if image.get("width") != str(width) or image.get("height") != str(height):
                    errors.append(f"{page_string}#{figure_id}: rendered dimensions mismatch")
                if image.get("loading") not in {"lazy", "eager"}:
                    errors.append(f"{page_string}#{figure_id}: rendered loading missing")
                if image.get("decoding") != "async":
                    errors.append(f"{page_string}#{figure_id}: rendered decoding mismatch")
                if image.get("src", "").startswith(("http://", "https://", "//")):
                    errors.append(f"{page_string}#{figure_id}: rendered image hotlink")
                if not any(link.get("href") for link in figure["links"]):
                    errors.append(f"{page_string}#{figure_id}: no focusable media link")
                if len(" ".join(figure["caption"]).strip()) < 20:
                    errors.append(f"{page_string}#{figure_id}: rendered caption missing")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    mode = "source + rendered HTML" if args.site_dir is not None else "source"
    print(
        f"图表检查通过（{mode}）：{len(assets)} 个资产，"
        f"{len(expected_placements)} 个位置，{len(markdown_pages)} 个页面覆盖决策"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
