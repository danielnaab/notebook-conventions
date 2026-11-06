---
status: working
---

# Obsidian and Markdown formatting

The repository root is the Obsidian vault. Obsidian is a view over the same Markdown agents maintain.
The [seed](../seed/common/.obsidian/) carries shared core settings; machine-specific UI state stays local.

## Shared settings

| Setting | Value |
| --- | --- |
| Daily notes folder | `notebook/daily` |
| Daily notes date format | `YYYY-MM/YYYY-MM-DD` (the plugin creates the month folder) |
| Daily notes template | `notebook/templates/daily` |
| Templates folder | `notebook/templates` |
| Open on startup | Current daily note (`app.json` → `openBehavior: daily`) |
| Markdown links | Enabled, relative paths; link updates on rename enabled |
| Attachments | `./attachments`, beside the note's folder |

- Obsidian omits hidden folders (`.scions/`, `.pi/`), so notes cannot link into pinned guidance inside its UI.
  Those folders stay available on disk and in Git hosts. Templates must live in a visible folder, which is
  why a workspace copies them from the kit.
- Track plugin `data.json` files only for plugins you have reviewed: preferences can contain credentials or
  private text. Keep plugin executables, manifests, caches, and live workspace state ignored. A clone restores
  preferences, not plugin installations.
- Agents must not inspect or alter Obsidian's application profile to bypass its per-vault plugin approval.

## Markdown formatting

The Obsidian [Linter](https://github.com/platers/obsidian-linter) plugin rewrites notes on save, so Markdown
that does not already follow its rules later shows up as unrelated whitespace diffs. The seed enables one rule:

- **Heading blank lines:** every `#`-style heading has exactly one blank line before and after it. A heading at
  the start or end of a file needs none on that side. Headings in fenced code, front matter, and math are ignored.

`markdownlint-cli2` mirrors it with `MD022` only, through `.markdownlint-cli2.jsonc`. If the Linter settings
change, change that file to match.

```sh
markdownlint-cli2                # check all Markdown
markdownlint-cli2 --fix FILE...  # fix in place; output matches the Obsidian Linter
```

## Pre-commit hook

[`tools/hooks/pre-commit`](../tools/hooks/pre-commit) runs the lint check on staged `.md` files and
`nix run .#check-kb` over the repository, and blocks the commit on violations. Enable it once per clone:

```sh
git config core.hooksPath .scions/notebook-conventions/tools/hooks
```

It falls back to `nix develop` when `markdownlint-cli2` is not on `PATH`.

## Sources

- [Obsidian Linter](https://github.com/platers/obsidian-linter)
- [Seed Obsidian settings](../seed/common/.obsidian/app.json)
- [Pre-commit hook](../tools/hooks/pre-commit)
