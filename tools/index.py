#!/usr/bin/env python3
"""Generate the vault's OKF index.md listings from note frontmatter (OKF v0.2 §8).

Every folder in the bundle that holds notes gets an index: headed sections of `* [Title](path) - description`,
from each note's `title` and `description`. The bundle root's index declares `okf_version`; the tasks folder's
index lists active tasks by status and the ten most recently completed. Hidden folders and `.okfignore` matches
are skipped. With --check, nothing is written and the exit code is 1 if any index is missing or stale.
"""

import argparse
import sys
from pathlib import Path

import vault


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root (default: cwd)")
    parser.add_argument("--check", action="store_true", help="Report missing or stale indexes; write nothing")
    args = parser.parse_args()
    root = args.root.resolve()
    stale = []
    for rel, content in vault.expected_indexes(root).items():
        path = root / rel
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            continue
        stale.append(rel)
        if not args.check:
            path.write_text(content, encoding="utf-8")
    verb = "stale or missing" if args.check else "written"
    for rel in stale:
        print(f"{verb}: {rel}")
    print(f"Indexes: {len(stale)} {verb}.")
    if args.check and stale:
        print("Run `nix run .#index` to regenerate them.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
