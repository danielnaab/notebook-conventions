---
status: working
---

# Obsidian and Markdown formatting

`notebook/` is the Obsidian vault (Open folder as vault), so the vault is the OKF bundle and nothing else: code,
workspace docs, and `.scions/` stay outside it. Obsidian is a view over the same Markdown agents maintain.
The [seed](../seed/common/notebook/.obsidian/) carries shared core settings; machine-specific UI state stays local.

## Shared settings

| Setting | Value |
| --- | --- |
| Daily notes folder | `records/daily` |
| Daily notes date format | `YYYY-MM/YYYY-MM-DD` (the plugin creates the month folder) |
| Daily notes template | `templates/daily` |
| Templates folder | `templates` |
| Open on startup | Current daily note (`app.json` → `openBehavior: daily`) |
| Markdown links | Enabled, relative paths; link updates on rename enabled; wikilinks off |
| Attachments | `./attachments`, beside the note's folder |

- Paths in the settings are relative to the vault, `notebook/`. Templates must live in a visible folder, which is
  why a workspace copies them from the kit into `notebook/templates/`.
- Notes cannot link to workspace docs or the kit, which are outside the vault; use URLs or backticked paths.
- `[[` autocomplete finds notes by `title` and `aliases` and inserts a Markdown link; people notes carry an
  `@Full Name` alias, so `[[@` lists people. Links to notes not written yet show in the graph and create the
  note on click.
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
`nix run .#check-kb` over the repository, and blocks the commit on violations. Git cannot run it from
`.scions/`, because graft does not keep the executable bit there. The seed therefore has an executable wrapper,
`.githooks/pre-commit`, that runs it with `sh`. Enable the wrapper once per clone:

```sh
git config core.hooksPath .githooks
```

It falls back to `nix develop` when `markdownlint-cli2` is not on `PATH`.

## Sources

- [Obsidian Linter](https://github.com/platers/obsidian-linter)
- [Seed Obsidian settings](../seed/common/notebook/.obsidian/app.json)
- [Pre-commit hook](../tools/hooks/pre-commit)
