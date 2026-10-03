#!/usr/bin/env python3
"""Insert (or refresh) a Table of Contents in a guide, listing its H2
headings (each question) as links using GitHub's anchor-slug rules.

Usage: python3 scripts/add_toc.py <file.md> [<file.md> ...]

Idempotent: if a TOC block (marked by <!-- toc --> ... <!-- /toc -->) already
exists, it's replaced in place rather than duplicated, so this is safe to
re-run after editing a guide's headings.
"""
import re
import sys

HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)
FENCE_RE = re.compile(r"^```")
TOC_BLOCK_RE = re.compile(r"<!-- toc -->.*?<!-- /toc -->\n?", re.DOTALL)


def slugify(heading: str) -> str:
    """GitHub's markdown heading-to-anchor algorithm (github-slugger), run on
    the heading's rendered text: drop code-span backticks and emphasis
    markers, lowercase, drop non-word/space/hyphen chars, then convert each
    remaining space to a hyphen INDIVIDUALLY (no collapsing) — a punctuation
    character stripped from between two spaces (e.g. "A & B" -> "A  B")
    must become a double hyphen ("a--b"), not a single one.

    Underscores are word characters to github-slugger, so they survive in
    the anchor ("`REQUIRES_NEW`" -> "requires_new"). Only an underscore used
    as an emphasis delimiter outside a code span is removed."""
    parts = re.split(r"(`[^`]*`)", heading)
    rendered = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            rendered.append(part[1:-1])  # code span: content is literal
        else:
            part = part.replace("*", "")
            part = re.sub(r"(?<![0-9A-Za-z])_+|_+(?![0-9A-Za-z])", "", part)
            rendered.append(part)
    text = "".join(rendered).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)  # drop punctuation
    text = text.replace(" ", "-")
    return text


def strip_code_fences(content: str) -> str:
    lines = content.split("\n")
    out, in_fence = [], False
    for line in lines:
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def build_toc(content: str) -> str:
    scan_content = strip_code_fences(content)
    seen = {}
    lines = ["<!-- toc -->", "## Table of Contents", ""]
    for match in HEADING_RE.finditer(scan_content):
        level, text = len(match.group(1)), match.group(2).strip()
        base = slugify(text)
        n = seen.get(base, 0)
        slug = base if n == 0 else f"{base}-{n}"
        seen[base] = n + 1
        indent = "  " * (level - 2)
        lines.append(f"{indent}- [{text}](#{slug})")
    lines.append("")
    lines.append("<!-- /toc -->")
    return "\n".join(lines) + "\n"


def insert_or_replace_toc(content: str) -> str:
    # Scan with any existing TOC block removed first, so a refresh doesn't
    # pick up the old block's own "## Table of Contents" heading as an entry.
    content_for_scan = TOC_BLOCK_RE.sub("", content, count=1)
    toc = build_toc(content_for_scan)
    if TOC_BLOCK_RE.search(content):
        return TOC_BLOCK_RE.sub(toc, content, count=1)
    # Insert after the intro paragraph, i.e. before the first "---" line,
    # or before the first H2 if there's no "---" separator.
    lines = content_for_scan.split("\n")
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            insert_at = i
            break
        if line.startswith("## "):
            insert_at = i
            break
    if insert_at is None:
        insert_at = len(lines)
    new_lines = lines[:insert_at] + [toc.rstrip("\n"), ""] + lines[insert_at:]
    return "\n".join(new_lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: add_toc.py <file.md> [<file.md> ...]", file=sys.stderr)
        return 2
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        updated = insert_or_replace_toc(content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
