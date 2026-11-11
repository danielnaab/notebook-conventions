"""Shared helpers for the vault tools: the bundle, note frontmatter, links, and index generation.

The bundle and `.okfignore` come from knowledge-base-kit's checker (KBI_SRC), so the kit and the checker agree
on what is in the bundle. Everything here is read-only except `write_indexes` and `rewrite_links`.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote

import yaml

OKF_VERSION = "0.2"
DEFAULT_BUNDLE = "notebook"
DEFAULT_TASKS_PATH = "notebook/tasks"
INDEX = "index.md"
RESERVED = ("index.md", "log.md")

# Descriptions for the kit's own folders, used in generated indexes (a folder has no frontmatter).
FOLDER_DESCRIPTIONS = {
    "raw": "Sources as captured, never edited",
    "records": "Dated notes, written once",
    "records/daily": "Daily notes",
    "records/sessions": "Agent session records",
    "tasks": "Task records, by creation month",
    "wiki": "Maintained knowledge",
}
TASK_SECTIONS = (
    ("In progress", "in-progress"),
    ("Ready", "ready"),
    ("Waiting", "waiting"),
    ("Later", "later"),
    ("Recently completed", "completed"),
)
RECENTLY_COMPLETED = 10

DATED = re.compile(r"^\d{4}-\d{2}")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+).+?\1")
# [text](destination "optional title"): link text may span lines and hold one level of brackets
# ([a [b]](x), [![img](i.png)](x)); the destination is bare, with balanced parentheses, or in <angle brackets>.
_LABEL = r"\[(?:[^\[\]\\]|\\.|\[(?:[^\[\]\\]|\\.)*\])*\]"
_BARE = r"(?:[^()\s\\]|\\.|\((?:[^()\s\\]|\\.)*\))*"
LINK = re.compile(
    rf"(!?{_LABEL})\((<[^>\n]*>|{_BARE})((?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?)\s*\)"
)
# A reference definition: [label]: destination "optional title"
REFERENCE = re.compile(r"(?m)^ {0,3}\[(?:[^\]\\\n]|\\.)+\]:[ \t]*(<[^>\n]*>|\S+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$\n?", re.S | re.M)


def load_kbi():
    """Import knowledge-base-kit's okf module from KBI_SRC (set by the nix apps)."""
    src = os.environ.get("KBI_SRC")
    if not src:
        sys.exit("set KBI_SRC to knowledge-base-kit's src/ (use the nix run apps)")
    if src not in sys.path:
        sys.path.insert(0, src)
    from tool_cli import config, okf  # noqa: PLC0415

    return config, okf


def config(root: Path) -> dict:
    path = root / "knowledge-base.yaml"
    return (yaml.safe_load(path.read_text()) or {}) if path.is_file() else {}


def bundle(root: Path):
    """The OKF bundle declared in knowledge-base.yaml (rules.checks.okf), else notebook/."""
    kbi_config, okf = load_kbi()
    declared = okf.load_bundle(root, kbi_config.load_config(root))
    if declared is not None:
        return declared
    return okf.Bundle(root=DEFAULT_BUNDLE, ignore=okf.parse_ignore(_read(root / DEFAULT_BUNDLE / ".okfignore")))


def tasks_path(root: Path) -> str:
    value = ((config(root).get("rules") or {}).get("checks") or {}).get("tasks") or {}
    path = value.get("path") if isinstance(value, dict) else None
    return path.strip("/") if isinstance(path, str) and path.strip("/") else DEFAULT_TASKS_PATH


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def frontmatter(text: str) -> tuple[dict | None, str]:
    """(metadata, body); metadata is None without a block and {} when it is not a mapping."""
    match = FRONTMATTER.match(text)
    if not match:
        return None, text
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), text[match.end():]


# --- links ---------------------------------------------------------------------------------------------


@dataclass
class Link:
    start: int  # offsets of the destination (inside the parentheses) in the file text
    end: int
    destination: str  # as written, angle brackets included


def masked(text: str) -> str:
    """The text with fenced code, inline code, and HTML comments blanked; offsets and newlines kept."""
    out: list[str] = []
    fence = ""
    in_comment = False
    for line in text.splitlines(keepends=True):
        marker = FENCE.match(line)
        if fence:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence) \
                    and line.strip() == marker.group(1):
                fence = ""
            out.append(_blank(line))
        elif marker and not in_comment:
            fence = marker.group(1)
            out.append(_blank(line))
        else:
            line_masked, in_comment = _mask(line, in_comment)
            out.append(line_masked)
    return "".join(out)


def _blank(line: str) -> str:
    return re.sub(r"[^\n]", " ", line)


def links(text: str) -> list[Link]:
    """Inline links (and links inside their text) and reference definitions, outside code and comments."""
    hidden = masked(text)
    found: list[Link] = []

    def scan(start: int, end: int) -> None:
        for match in LINK.finditer(hidden, start, end):
            found.append(Link(match.start(2), match.end(2), text[match.start(2):match.end(2)]))
            scan(match.start(1) + 1, match.end(1) - 1)  # [![image](i.png)](page.md)

    scan(0, len(hidden))
    for match in REFERENCE.finditer(hidden):
        found.append(Link(match.start(1), match.end(1), text[match.start(1):match.end(1)]))
    return sorted(found, key=lambda link: link.start)


def _mask(line: str, in_comment: bool) -> tuple[str, bool]:
    """Blank out inline code and HTML comments, keeping offsets."""
    out = INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)
    chars = list(out)
    i = 0
    while i < len(out):
        if in_comment:
            end = out.find("-->", i)
            stop = len(out) if end == -1 else end + 3
            chars[i:stop] = " " * (stop - i)
            in_comment = end == -1
            i = stop
        else:
            start = out.find("<!--", i)
            if start == -1:
                break
            in_comment = True
            i = start
    return "".join(chars), in_comment


def split_destination(destination: str) -> tuple[str, str, bool]:
    """(decoded path, suffix: ?query and #fragment as written, angle-bracketed)."""
    angle = destination.startswith("<") and destination.endswith(">")
    raw = destination[1:-1] if angle else destination
    cut = min((i for i in (raw.find("?"), raw.find("#")) if i != -1), default=len(raw))
    return unquote(raw[:cut]), raw[cut:], angle


def format_destination(path: str, suffix: str, angle: bool) -> str:
    if angle:
        return f"<{path}{suffix}>"
    return quote(path, safe="/._-~!$&'*+,;=:@") + suffix


def is_local(destination: str) -> bool:
    path, _, angle = split_destination(destination)
    return bool(path) and not SCHEME.match(destination[1:] if angle else destination)


def rewrite_links(text: str, rewrite) -> str:
    """Replace each local link destination with rewrite(destination) (None keeps it)."""
    out, last = [], 0
    for link in links(text):
        if not is_local(link.destination):
            continue
        new = rewrite(link.destination)
        if new is None or new == link.destination:
            continue
        out += [text[last:link.start], new]
        last = link.end
    return "".join(out) + text[last:]


def links_masked_text(text: str) -> str:
    """The text with every link destination blanked, to find plain-text mentions of a path."""
    out, last = [], 0
    for link in links(text):
        out.append(text[last:link.start])
        last = link.end
    return "".join(out) + text[last:]


# --- indexes -------------------------------------------------------------------------------------------


H1 = re.compile(r"^# (.+?)\s*#*\s*$", re.M)


def _title(meta: dict | None, path: Path, body: str = "") -> str:
    """The note's `title`, else its first # heading, else its filename."""
    title = (meta or {}).get("title")
    if title:
        return str(title).strip()
    heading = H1.search(body)
    return heading.group(1).strip() if heading and "{{" not in heading.group(1) else path.stem


def _entry(title: str, href: str, description: str | None) -> str:
    # OKF index entries are matched as [text](url): brackets in a title become parentheses, a trailing
    # backslash is dropped, and the URL is fully encoded, parentheses included.
    title = " ".join(title.split()).replace("[", "(").replace("]", ")").rstrip("\\") or href
    line = f"* [{title}]({quote(href, safe='/._-~')})"
    description = " ".join(str(description).split()) if description else ""
    return f"{line} - {description}" if description else line


def _sort(entries: list[tuple[str, str]]) -> list[str]:
    """Dated names newest first, then the rest by title."""
    dated = sorted((e for e in entries if DATED.match(e[0])), key=lambda e: e[0], reverse=True)
    rest = sorted((e for e in entries if not DATED.match(e[0])), key=lambda e: e[1].casefold())
    return [line for _, line in dated + rest]


def expected_indexes(root: Path) -> dict[str, str]:
    """Repository-relative index path -> generated content, for every indexed folder in the bundle.

    A folder is indexed when it holds a note, an indexed subfolder, or an index already. Hidden folders and
    `.okfignore` matches are not part of the bundle.
    """
    b = bundle(root)
    base = root / b.root if b.root else root
    tasks_rel = tasks_path(root)
    result: dict[str, str] = {}

    def visit(directory: Path) -> bool:
        rel = directory.relative_to(root).as_posix()
        in_bundle = directory.relative_to(base).as_posix()
        subdirs, notes = [], []
        for child in sorted(directory.iterdir()):
            child_rel = child.relative_to(root).as_posix()
            if child.name.startswith(".") or b.is_ignored(child_rel + ("/x" if child.is_dir() else "")):
                continue
            if child.is_dir():
                if visit(child):
                    subdirs.append(child)
            elif child.suffix == ".md" and child.name not in RESERVED:
                notes.append(child)
        has_index = (directory / INDEX).is_file()
        if not (subdirs or notes or has_index):
            return False
        if rel == tasks_rel:
            content = task_index(directory)
        else:
            content = _folder_index(directory, in_bundle, subdirs, notes)
        if in_bundle == ".":
            content = f'---\nokf_version: "{OKF_VERSION}"\n---\n\n' + content
        result[(directory / INDEX).relative_to(root).as_posix()] = content
        return True

    if base.is_dir():
        visit(base)
    tasks = root / tasks_rel
    if tasks.is_dir() and not b.contains(tasks_rel):
        result[f"{tasks_rel}/{INDEX}"] = task_index(tasks)  # a tasks folder outside the bundle
    return result


def _heading(in_bundle: str) -> str:
    if in_bundle == ".":
        return "Notebook"
    name = in_bundle.rsplit("/", 1)[-1]
    return name if DATED.match(name) else name.replace("-", " ").capitalize()


def _folder_index(directory: Path, in_bundle: str, subdirs: list[Path], notes: list[Path]) -> str:
    lines = [f"# {_heading(in_bundle)}", ""]
    if subdirs:
        prefix = "" if in_bundle == "." else in_bundle + "/"
        entries = [
            (d.name, _entry(d.name, d.name + "/", FOLDER_DESCRIPTIONS.get(prefix + d.name))) for d in subdirs
        ]
        lines += ["## Folders", "", *_sort(entries), ""]
    if notes:
        entries = []
        for note in notes:
            meta, body = frontmatter(note.read_text(encoding="utf-8"))
            entries.append((note.name, _entry(_title(meta, note, body), note.name, (meta or {}).get("description"))))
        lines += ["## Notes", "", *_sort(entries), ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def task_index(directory: Path) -> str:
    """Active tasks by status, then the ten most recently completed."""
    by_status: dict[str, list[tuple[str, str, str]]] = {status: [] for _, status in TASK_SECTIONS}
    for note in sorted(directory.glob("*/*.md")) + sorted(directory.glob("*/*/README.md")):
        if note.name in RESERVED:
            continue
        meta, body = frontmatter(note.read_text(encoding="utf-8"))
        status = (meta or {}).get("status")
        if not isinstance(status, str) or status not in by_status:
            continue
        href = note.relative_to(directory).as_posix()
        key = str((meta or {}).get("completed") or (meta or {}).get("updated") or "")
        by_status[status].append((key, href, _entry(_title(meta, note, body), href, (meta or {}).get("description"))))
    lines = ["# Tasks", ""]
    for heading, status in TASK_SECTIONS:
        entries = by_status[status]
        if status == "completed":
            entries = sorted(entries, key=lambda e: (e[0], e[1]), reverse=True)[:RECENTLY_COMPLETED]
        else:
            entries = sorted(entries, key=lambda e: e[1])
        if entries:
            lines += [f"## {heading}", "", *(e[2] for e in entries), ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def as_date(value) -> date | None:
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    return None
