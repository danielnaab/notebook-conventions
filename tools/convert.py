#!/usr/bin/env python3
"""Convert a v0.1 workspace to the v0.2 vault layout: notebook/ is the Obsidian vault and an OKF bundle.

Run from the workspace root on a clean branch, after upgrading the kit to v0.2. It changes files only under
notebook/, the root .obsidian/ and .gitignore, and links in Markdown files; it prints what is left to do by hand.
Re-running it is safe: each step is skipped when already done. --dry-run lists the steps without changing anything.

1. Moves notebook/daily and notebook/sessions under notebook/records/, rewriting links.
2. Flattens each session folder's README.md into YYYY-MM-DD-<slug>.md; other files stay in the folder beside it.
3. Replaces folder README.md files in the bundle with generated index.md listings; links follow.
4. Adds `type` to notes that lack one, by folder (Daily Note, Session, Task, Topic, Source).
5. Moves .obsidian/ into notebook/, points its daily-note and template settings at the new folders, and
   re-anchors the .gitignore patterns for it.
6. Writes notebook/.okfignore (templates/) first, and replaces unchanged v0.1 templates with the v0.2 ones.
7. Generates every index.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import move as mover
import vault

KIT = Path(__file__).resolve().parents[1]
NOTEBOOK = "notebook"
# sha256 prefixes of the v0.1.0–v0.1.4 templates and seeded folder READMEs: an exact match is unchanged
# seed content, safe to replace; anything else is reported.
V01_TEMPLATES = {
    "daily.md": "b966bd2d9c880f53",
    "session.md": "bd2559fd72bab343",
    "task-record.md": "8af9dbf12551738c",
    "wiki.md": "d5c6c77f447cb829",
}
V01_READMES = {
    "daily": "18ca2e88326bdaf8",
    "raw": "fe971b48d71635c5",
    "sessions": "60ba87d9f6a436f1",
    "tasks": "7a0824ae505f4eb1",
    "wiki": "a10f89f3173d33b8",
}
TYPES = (
    (re.compile(r"^records/daily/"), "Daily Note"),
    (re.compile(r"^records/sessions/\d{4}-\d{2}/[^/]+\.md$"), "Session"),
    (re.compile(r"^tasks/\d{4}-\d{2}/([^/]+\.md|[^/]+/README\.md)$"), "Task"),
    (re.compile(r"^wiki/"), "Topic"),
    (re.compile(r"^raw/"), "Source"),
)
SESSION_README = re.compile(r"^notebook/records/sessions/(\d{4}-\d{2})/([^/]+)/README\.md$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


class Converter:
    def __init__(self, root: Path, dry_run: bool):
        self.root = root
        self.dry_run = dry_run
        self.done: list[str] = []
        self.manual: list[str] = []

    def log(self, message: str) -> None:
        self.done.append(message)

    def move(self, old: str, new: str) -> None:
        if not (self.root / old).exists():
            return
        if (self.root / new).exists():
            self.manual.append(f"both {old} and {new} exist: merge them by hand")
            return
        changed, mentions = mover.move(self.root, old, new, dry_run=self.dry_run)
        self.log(f"moved {old} -> {new} ({len(changed)} files' links)")
        for rel in mentions:
            self.manual.append(f"{rel} mentions {old} as text: update it to {new}")

    def run(self) -> None:
        if not (self.root / NOTEBOOK).is_dir():
            sys.exit(f"convert: no {NOTEBOOK}/ here; run from the workspace root")
        # Before any move rewrites their links: which folder READMEs are unchanged seed content.
        self.seeded = {
            folder: digest(self.root / NOTEBOOK / folder / "README.md") == expected
            for folder, expected in V01_READMES.items()
            if (self.root / NOTEBOOK / folder / "README.md").is_file()
        }
        if not self.dry_run:
            self.write_okfignore()
        self.move(f"{NOTEBOOK}/daily", f"{NOTEBOOK}/records/daily")
        self.move(f"{NOTEBOOK}/sessions", f"{NOTEBOOK}/records/sessions")
        if self.dry_run:
            self.log("then: flatten sessions, replace READMEs, add types, move .obsidian/, write indexes")
            return
        self.flatten_sessions()
        self.readmes_to_indexes()
        self.add_types()
        self.obsidian()
        self.templates()
        for rel, content in vault.expected_indexes(self.root).items():
            path = self.root / rel
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8")
                self.log(f"wrote {rel}")

    def flatten_sessions(self) -> None:
        folder = self.root / NOTEBOOK / "records/sessions"
        for readme in sorted(folder.glob("*/*/README.md")):
            rel = readme.relative_to(self.root).as_posix()
            match = SESSION_README.match(rel)
            if not match:
                continue
            month, slug = match.groups()
            self.move(rel, f"{NOTEBOOK}/records/sessions/{month}/{slug}.md")
            leftover = readme.parent
            if leftover.is_dir() and not any(leftover.iterdir()):
                leftover.rmdir()

    def readmes_to_indexes(self) -> None:
        b = vault.bundle(self.root)
        for readme in sorted((self.root / NOTEBOOK).rglob("README.md")):
            rel = readme.relative_to(self.root).as_posix()
            folder = readme.parent.relative_to(self.root / NOTEBOOK).as_posix()
            if any(p.startswith(".") for p in Path(rel).parts) or b.is_ignored(rel):
                continue
            if folder.startswith("tasks/") or folder == "templates":
                continue  # a folder-shaped task's README is the task; templates/ is not in the bundle
            if folder.startswith("records/sessions/"):
                self.manual.append(f"{rel}: not a session index; rename it or leave it")
                continue
            if folder != "tasks" and not self.seeded.get(folder.replace("records/", ""), False):
                self.manual.append(
                    f"{rel} had local prose; it is replaced by a generated index (the prose is in git history)"
                )
            target = readme.with_name(vault.INDEX).relative_to(self.root).as_posix()
            if (self.root / target).exists():
                self.manual.append(f"{rel} and {target} both exist: keep one")
                continue
            self.move(rel, target)

    def add_types(self) -> None:
        b = vault.bundle(self.root)
        for path in sorted((self.root / NOTEBOOK).rglob("*.md")):
            rel = path.relative_to(self.root).as_posix()
            in_bundle = path.relative_to(self.root / NOTEBOOK).as_posix()
            hidden = any(p.startswith(".") for p in Path(in_bundle).parts)
            if path.name in vault.RESERVED or hidden or b.is_ignored(rel):
                continue
            text = path.read_text(encoding="utf-8")
            meta, _ = vault.frontmatter(text)
            if meta and isinstance(meta.get("type"), str) and meta["type"].strip():
                continue
            kind = next((t for pattern, t in TYPES if pattern.search(in_bundle)), None)
            if kind is None:
                self.manual.append(f"{rel}: add a `type` (no default for this folder)")
                continue
            if meta is None:
                text = f"---\ntype: {kind}\n---\n\n{text}"
            else:
                text = re.sub(r"\A---[ \t]*\n", f"---\ntype: {kind}\n", text, count=1)
            path.write_text(text, encoding="utf-8")
            self.log(f"type {kind}: {rel}")
            if kind == "Task" and not (meta or {}).get("description"):
                self.manual.append(f"{rel}: add a one-line `description` (the task index shows it)")

    def obsidian(self) -> None:
        old, new = self.root / ".obsidian", self.root / NOTEBOOK / ".obsidian"
        if old.is_dir() and not new.exists():
            shutil.move(str(old), str(new))
            self.log("moved .obsidian/ -> notebook/.obsidian/")
        for name, keys in (("daily-notes.json", ("folder", "template")), ("templates.json", ("folder",))):
            path = new / name
            if not path.is_file():
                continue
            data = json.loads(path.read_text())
            changed = False
            for key in keys:
                value = data.get(key)
                if isinstance(value, str) and value.startswith(f"{NOTEBOOK}/"):
                    value = value[len(NOTEBOOK) + 1:]
                    value = "records/daily" if value == "daily" else value
                    data[key], changed = value, True
            if changed:
                path.write_text(json.dumps(data, indent=2) + "\n")
                self.log(f"updated notebook/.obsidian/{name}")
        gitignore = self.root / ".gitignore"
        if gitignore.is_file():
            text = gitignore.read_text()
            updated = re.sub(r"(?m)^(!?)\.obsidian/", rf"\1{NOTEBOOK}/.obsidian/", text)
            if updated != text:
                gitignore.write_text(updated)
                self.log("re-anchored .obsidian/ patterns in .gitignore")
        self.manual.append("reopen the vault in Obsidian at notebook/ (Open folder as vault)")

    def write_okfignore(self) -> None:
        ignore = self.root / NOTEBOOK / ".okfignore"
        if not ignore.exists():
            ignore.write_text((KIT / "seed/common/notebook/.okfignore").read_text())
            self.log("wrote notebook/.okfignore")

    def templates(self) -> None:
        folder = self.root / NOTEBOOK / "templates"
        for name, old in V01_TEMPLATES.items():
            path = folder / name
            if not path.is_file():
                continue
            if digest(path) == old:
                shutil.copy2(KIT / "templates" / name, path)
                self.log(f"updated template {name}")
            elif (KIT / "templates" / name).read_text() != path.read_text():
                self.manual.append(f"templates/{name} has local changes: merge the v0.2 frontmatter by hand")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="List the folder moves; change nothing")
    args = parser.parse_args()
    converter = Converter(args.root.resolve(), args.dry_run)
    converter.run()
    for line in converter.done:
        print(f"done: {line}")
    for line in converter.manual:
        print(f"by hand: {line}")
    print(f"Converted: {len(converter.done)} steps done, {len(converter.manual)} to do by hand.")
    print("Then apply the remaining CHANGELOG Upgrading steps and run the checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
