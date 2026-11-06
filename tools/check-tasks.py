"""Read-only validation of task records and their current-work index. No scheduling/actions.

The tasks folder is `notebook/tasks` unless knowledge-base.yaml sets `rules.checks.tasks.path`.
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
from urllib.parse import unquote

import yaml

STATUSES = {"ready", "in-progress", "waiting", "later", "completed", "canceled"}
ACTIVE = STATUSES - {"completed", "canceled"}
SECTIONS = {
    "Ready": "ready", "In progress": "in-progress", "Waiting": "waiting",
    "Later": "later", "Recently completed": "completed",
}
REQUIRED = {"status", "created", "updated", "owner", "project"}
DEFAULT_TASKS_PATH = "notebook/tasks"
RECORD = re.compile(r"^(\d{4}-\d{2})/([a-z0-9]+(?:-[a-z0-9]+)*)(?:\.md|/README\.md)$")
LINK = re.compile(r"\[[^\]\n]*\]\(([^\s)]+)\)")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    pairs = loader.construct_pairs(node, deep=deep)
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate metadata key")
        result[key] = value
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def frontmatter(text):
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError("missing frontmatter")
    meta = yaml.load(match.group(1), Loader=UniqueLoader)
    if not isinstance(meta, dict):
        raise ValueError("metadata must be a mapping")
    return meta, text[match.end():]


def as_date(value):
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    raise ValueError("expected ISO date")


def prose(text):
    lines, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            kind = marker.group(1)[0]
            fence = None if fence == kind else kind if fence is None else fence
        elif not fence:
            lines.append(line)
    return re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)


def tasks_path(root: Path) -> str:
    """Repository-relative tasks folder from knowledge-base.yaml, else the default."""
    config = root / "knowledge-base.yaml"
    if config.is_file():
        data = yaml.safe_load(config.read_text()) or {}
        value = (((data.get("rules") or {}).get("checks") or {}).get("tasks") or {}).get("path")
        if isinstance(value, str) and value.strip("/"):
            return value.strip("/")
    return DEFAULT_TASKS_PATH


def validate(root: Path) -> list[str]:
    root = root.resolve()
    tasks_rel = tasks_path(root)
    folder = root / tasks_rel
    errors, records, bodies, dependencies = [], {}, {}, {}

    def error(path, message):
        errors.append(f"{path}: {message}")

    def safe(path):
        return not any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root))

    if not folder.is_dir() or not safe(folder):
        return [f"{tasks_rel}: missing directory or symlink"]
    candidates = list(folder.rglob("*.md"))
    record_paths = {p for p in candidates if RECORD.fullmatch(p.relative_to(folder).as_posix())}
    artifact_folders = {p.parent for p in record_paths if p.name == "README.md"}
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        if path == folder / "README.md":
            continue
        if path not in record_paths:
            if not any(path.is_relative_to(p) for p in artifact_folders):
                error(rel, "unsupported task path (use creation-month/task-name.md)")
            continue
        if not safe(path) or not path.resolve().is_relative_to(folder.resolve()):
            error(rel, "task symlinks are not allowed")
            continue
        try:
            meta, body = frontmatter(path.read_text())
        except (ValueError, TypeError, yaml.YAMLError, UnicodeError):
            error(rel, "missing/invalid frontmatter or duplicate metadata keys")
            continue
        records[rel], bodies[rel] = meta, body
        for key in sorted(REQUIRED):
            if key not in meta:
                error(rel, f"missing required field {key}")
        status = meta.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            error(rel, "invalid status")
            status = None
        for key in ["owner", "project"]:
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                error(rel, f"{key} must be a nonempty string")
        dates = {}
        for key in ["created", "updated", "due", "review_on", "completed"]:
            if key not in meta:
                continue
            try:
                dates[key] = as_date(meta[key])
            except (ValueError, TypeError):
                error(rel, f"{key} must be a YYYY-MM-DD date")
        if "created" in dates:
            month = RECORD.fullmatch(path.relative_to(folder).as_posix()).group(1)
            if dates["created"].strftime("%Y-%m") != month:
                error(rel, "creation month does not match path")
        if "created" in dates and "updated" in dates and dates["updated"] < dates["created"]:
            error(rel, "updated precedes created")
        if status == "completed" and "completed" not in dates:
            error(rel, "completed tasks require a completion date")
        if "completed" in dates:
            if status != "completed":
                error(rel, "completion date is only valid for completed status")
            if "created" in dates and dates["completed"] < dates["created"]:
                error(rel, "completion precedes created")
            if "updated" in dates and dates["completed"] > dates["updated"]:
                error(rel, "updated precedes completion")
        if "priority" in meta and meta["priority"] not in ("high", "normal", "low"):
            error(rel, "invalid priority")
        for key in ["contexts", "blocked_by"]:
            value = meta.get(key, [])
            if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
                error(rel, f"{key} must be a list of nonempty strings")
                value = []
            if key == "blocked_by":
                dependencies[rel] = value
        text = prose(body)
        if "{{" in path.read_text():
            error(rel, "unresolved template placeholder")
        if not re.search(r"^# \S", text, re.M):
            error(rel, "missing task title")
        headings = list(re.finditer(r"^## ([^\n]+)\s*$", text, re.M))
        sections = {}
        for n, heading in enumerate(headings):
            name = heading.group(1).strip()
            end = headings[n + 1].start() if n + 1 < len(headings) else len(text)
            if name in sections:
                error(rel, "duplicate body section")
            sections[name] = text[heading.end():end].strip()
        required = {"Goal", "Sources"}
        if status in ACTIVE:
            required |= {"Next action", "Resurface when", "Done when"}
        if status == "waiting":
            required.add("Waiting on")
        if status in {"completed", "canceled"}:
            required.add("Outcome")
        for name in sorted(required):
            if not sections.get(name):
                error(rel, f"missing/empty section {name}")
        if not LINK.search(sections.get("Sources", "")):
            error(rel, "Sources requires a Markdown evidence/context link")
        for target in LINK.findall(text):
            name = unquote(target.split("#", 1)[0])
            if name and not re.match(r"[a-zA-Z][\w+.-]*:", name) and not (path.parent / name).exists():
                error(rel, "missing local navigation target")

    for rel, deps in dependencies.items():
        for dep in deps:
            if dep == rel or dep not in records:
                error(rel, "blocked_by must reference another existing task identifier")
    visiting, visited = set(), set()

    def visit(rel):
        if rel in visiting:
            error(rel, "dependency cycle")
            return
        if rel in visited:
            return
        visiting.add(rel)
        for dep in dependencies.get(rel, []):
            if dep in records:
                visit(dep)
        visiting.remove(rel)
        visited.add(rel)

    for rel in records:
        visit(rel)
    index = folder / "README.md"
    index_rel = index.relative_to(root).as_posix()
    if not index.is_file() or not safe(index):
        return errors + [f"{index_rel}: missing index or symlink"]
    try:
        meta, body = frontmatter(index.read_text())
    except (ValueError, TypeError, yaml.YAMLError, UnicodeError):
        return errors + [f"{index_rel}: invalid frontmatter"]
    if meta.get("status") != "living":
        error(index_rel, "index must have status living")
    indexed, section, closed = set(), None, 0
    for line in prose(body).splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        for target in LINK.findall(line):
            name = unquote(target.split("#", 1)[0])
            if re.match(r"[a-zA-Z][\w+.-]*:", name) or not name:
                continue
            path = (folder / name).resolve()
            if not path.exists():
                error(index_rel, "missing local navigation target")
            if not path.is_relative_to(folder):
                continue
            rel = path.relative_to(root).as_posix()
            if rel not in records:
                error(index_rel, "index link must identify a task record")
                continue
            if rel in indexed:
                error(index_rel, "duplicate task link")
            indexed.add(rel)
            if records[rel].get("status") != SECTIONS.get(section):
                error(index_rel, "task status does not match index section")
            if section == "Recently completed":
                closed += 1
    if closed > 10:
        error(index_rel, "Recently completed exceeds ten links")
    for rel, meta in records.items():
        status = meta.get("status")
        if isinstance(status, str) and status in ACTIVE and rel not in indexed:
            error(rel, "active task is missing from index")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root (default: cwd)")
    args = parser.parse_args()
    errors = validate(args.root)
    for message in errors:
        print(message)
    print(f"Task validation: {len(errors)} errors.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
