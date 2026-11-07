#!/usr/bin/env python3
"""Move a note or folder and rewrite the relative Markdown links to and from it.

Every Markdown file in the repository outside hidden folders is scanned: links that pointed into the moved
path are re-pointed, and links inside moved files are re-relativized from their new folder. Links starting
with `/` resolve from the bundle root and keep that form. Fragments, queries, and angle brackets are kept.
Plain-text mentions of the old path (backticked paths, `blocked_by` entries) are listed for review, not changed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import vault

SKIP = {".git", "node_modules", "__pycache__"}


def markdown_files(root: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP and not d.startswith("."))
        found += [Path(dirpath, f) for f in sorted(filenames) if f.endswith(".md")]
    return found


def move(root: Path, old: str, new: str, dry_run: bool = False) -> tuple[list[str], list[str]]:
    """Move root/old to root/new. Returns (files whose links changed, files that mention old as text)."""
    root = root.resolve()
    old = os.path.normpath(old).replace(os.sep, "/")
    new = os.path.normpath(new).replace(os.sep, "/")
    source, target = root / old, root / new
    if not source.exists():
        raise SystemExit(f"move: {old} does not exist")
    if target.exists():
        raise SystemExit(f"move: {new} already exists")
    if new == old or new.startswith(old + "/"):
        raise SystemExit("move: cannot move a path into itself")
    b = vault.bundle(root)

    def mapped(rel: str) -> str:
        if rel == old:
            return new
        if rel.startswith(old + "/"):
            return new + rel[len(old):]
        return rel

    # Plain-text mentions use the repository path or the path inside the bundle.
    # A bare one-word name ("daily") would match prose, so only path-like names count.
    inner = old[len(b.root) + 1:] if b.root and old.startswith(b.root + "/") else old
    mention_names = {n for n in (old, inner) if "/" in n or "." in n}
    changed, mentions, updates = [], [], {}
    for path in markdown_files(root):
        rel = path.relative_to(root).as_posix()
        new_rel = mapped(rel)
        here, there = os.path.dirname(rel), os.path.dirname(new_rel)
        text = path.read_text(encoding="utf-8")

        def rewrite(destination: str, here=here, there=there) -> str | None:
            target_path, suffix, angle = vault.split_destination(destination)
            rooted = target_path.startswith("/")
            base = b.root if rooted else here
            resolved = os.path.normpath(os.path.join(base, target_path.lstrip("/"))).replace(os.sep, "/")
            if resolved.startswith(".."):
                return None
            moved = mapped(resolved)
            if moved == resolved and here == there:
                return None
            trailing = "/" if target_path.endswith("/") and not moved.endswith("/") else ""
            if rooted:
                relative = "/" + os.path.relpath(moved, b.root or ".").replace(os.sep, "/")
            else:
                relative = os.path.relpath(moved, there or ".").replace(os.sep, "/")
            if relative == ".":
                relative = "./"
                trailing = ""
            return vault.format_destination(relative + trailing, suffix, angle)

        updated = vault.rewrite_links(text, rewrite)
        if updated != text:
            updates[path] = updated
            changed.append(new_rel)
        plain = vault.links_masked_text(updated)
        if any(name in plain for name in mention_names):
            mentions.append(new_rel)

    if not dry_run:
        for path, text in updates.items():
            path.write_text(text, encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    return changed, mentions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", help="Repository-relative path to move")
    parser.add_argument("new", help="Repository-relative destination; must not exist")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change; write nothing")
    args = parser.parse_args()
    changed, mentions = move(args.root, args.old, args.new, args.dry_run)
    verb = "would rewrite" if args.dry_run else "rewrote"
    for rel in changed:
        print(f"{verb} links: {rel}")
    for rel in mentions:
        print(f"mentions {args.old} as text, review by hand: {rel}")
    print(f"{'Would move' if args.dry_run else 'Moved'} {args.old} -> {args.new}; {len(changed)} files' links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
