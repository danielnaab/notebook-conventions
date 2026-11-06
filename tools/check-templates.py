#!/usr/bin/env python3
"""Report how a workspace's note templates differ from the kit's canonical copies.

Obsidian needs the templates in a visible folder, so a workspace copies them. This read-only
check lists which copies are identical, changed, or missing. Changed is not an error: a
workspace may adapt a template. Use --strict to exit 1 on missing or changed templates.
"""

import argparse
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[1]
CANONICAL = ("daily.md", "session.md", "wiki.md", "task-record.md")
DEFAULT_FOLDER = "notebook/templates"


def templates_folder(root: Path) -> str:
    config = root / "knowledge-base.yaml"
    if config.is_file():
        data = yaml.safe_load(config.read_text()) or {}
        value = (data.get("paths") or {}).get("templates")
        if isinstance(value, str) and value.strip("/"):
            return value.strip("/")
    return DEFAULT_FOLDER


def compare(root: Path, kit: Path = KIT) -> dict[str, str]:
    folder = root / templates_folder(root)
    result = {}
    for name in CANONICAL:
        local = folder / name
        if not local.is_file():
            result[name] = "missing"
        elif local.read_text() == (kit / "templates" / name).read_text():
            result[name] = "same"
        else:
            result[name] = "changed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = compare(args.root.resolve())
    for name, state in result.items():
        print(f"{state:8} {name}")
    if args.strict and any(state != "same" for state in result.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
