---
status: working
---

# Obsidian and Markdown formatting

`notebook/` is the Obsidian vault (Open folder as vault), so the vault is the OKF bundle and nothing else: code,
workspace docs, and `.scions/` stay outside it. Obsidian is a view over the same Markdown agents maintain.
The [seed](../seed/common/notebook/.obsidian/) carries shared core settings, appearance, shortcuts, a layout preset, and
reviewed plugin settings; machine-specific UI state stays local.

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
| File picker | `Mod-P`: Quick Switcher++ file mode; the stock quick switcher stays on `Mod-O` |
| Command picker | `Mod-Shift-P`: Quick Switcher++ command mode; the stock command palette has no shortcut |
| Vault-wide Search | `Mod-Shift-F` |
| Right sidebar | Calendar above Search; Backlinks, Outgoing links, All properties, and Outline are tabs beside Search |
| Appearance | Base theme follows the system; default CSS theme and fonts; base font size 20; no translucency; ribbon shown |

- Paths in the settings are relative to the vault, `notebook/`. Templates must live in a visible folder, which is
  why a workspace copies them from the kit into `notebook/templates/`.
- Notes cannot link to workspace docs or the kit, which are outside the vault; use URLs or backticked paths.
- `[[` autocomplete finds notes by `title` and `aliases` and inserts a Markdown link; people notes carry an
  `@Full Name` alias, so `[[@` lists people. Links to notes not written yet show in the graph and create the
  note on click.
- Track plugin `data.json` files only for plugins you have reviewed: preferences can contain credentials or
  private text. Keep plugin executables, manifests, caches, and live workspace state ignored: a clone restores
  preferences, and `just upgrade-obsidian` installs the pinned plugins.
- Agents must not inspect or alter Obsidian's application profile to bypass its per-vault plugin approval.
- `hotkeys.json` uses `Mod`, which is Cmd on macOS and Ctrl elsewhere. The picker shortcuts call Quick
  Switcher++ commands, so they do nothing until that plugin is installed and enabled.

## Community plugins

The seed enables four community plugins and carries their reviewed settings. The kit pins each release in
[`obsidian-plugins.json`](obsidian-plugins.json): version, source commit, minimum Obsidian version, and the
SHA-256 of each release asset.

| Plugin | Id | Pinned | Settings |
| --- | --- | --- | --- |
| [Calendar](https://github.com/liamcain/obsidian-calendar-plugin) | `calendar` | 1.5.10 | Confirm before creating a note; locale week start; weekly notes off |
| [Linter](https://github.com/platers/obsidian-linter) | `obsidian-linter` | 1.35.0 | One rule, heading blank lines; lints on save and on file change |
| [Advanced Tables](https://github.com/tgrosinger/advanced-tables-obsidian) | `table-editor-obsidian` | 0.23.2 | Defaults: Enter and Tab navigate tables; normal format |
| [Quick Switcher++](https://github.com/darlal/obsidian-switcher-plus) | `darlal-switcher-plus` | 6.2.0 | Defaults (no `data.json`); its commands carry the picker shortcuts |

- `just upgrade-obsidian` installs them, and `just upgrade` runs it, so a kit release that moves a pin or adds a
  plugin reaches every workspace with its settings. It installs only the pinned plugins the vault's
  `community-plugins.json` lists: a workspace whose boundaries rule a plugin out removes it there, and the kit's
  later upgrades keep that removal. `--no-plugins` merges settings only.
- The releases come from the kit's Nix wiring (`packages.obsidian-plugins` in `nix/workspace.nix`), which
  downloads each pinned asset and checks its SHA-256; the tool checks them again before copying. It writes
  `main.js`, `manifest.json`, and `styles.css` (where the release has one) and leaves `data.json` alone. A plugin
  that already matches its pin, including the in-app installer's copy (see below), is left as it is.
- Obsidian asks once per vault, on each device, to turn off Restricted mode and trust the vault's plugins. That
  prompt stays the owner's: the tool does not answer it.
- A pin records the release the seeded settings were written against and lets a download be checked. It is not
  a security review. Obsidian's update check may offer newer versions; moving a pin is a kit change: check the
  release and its settings, update the pin, then release the kit.
- The in-app installer appends `/* nosourcemap */` to `main.js`, so its file matches the pin only without that
  last line. Installing or updating a plugin in the UI works too; `check-obsidian` then reports whether it still
  matches the pin.
- Calendar uses the core Daily notes folder, format, and template, including the month folder.

## Layout preset

The live layout, `.obsidian/workspace.json`, changes constantly and stays ignored. `layout-preset.json` is
a copy of the shared arrangement with no open files or history: Files and Bookmarks on the left, Calendar above
Search on the right, and the other right-sidebar views as tabs beside Search.

To apply it, close the vault, back up `notebook/.obsidian/workspace.json`, and copy the preset over it. This
replaces the current layout, so it is a deliberate step, never part of routine note-taking. Startup opens
the daily note either way, through `openBehavior`.

## Keeping settings in sync

The settings are seeded, so a workspace owns its copy. `just check-obsidian` compares each seeded file with
the vault's copy. It compares JSON, not text, because Obsidian rewrites formatting. It lists each file as same,
changed (and which keys or list items differ), or missing. It also shows each pinned plugin's installed version
and whether its `main.js` matches the pinned release. A changed file is a local choice, not an error; `--strict`
exits 1 on changed or missing files.

`just upgrade-obsidian` applies a kit release's setting and plugin changes, and `just upgrade` runs it after
moving the pins. Run it on the upgrade branch, with Obsidian closed, because Obsidian rewrites its settings while it runs. For each
seeded file it merges three versions: the seed in the scion at `--base` (default `HEAD`, which still holds the
old scion until the upgrade is committed), the current seed, and the vault's copy.

- A kit change applies where the vault still has the old value. Where the workspace changed the same setting, its
  value is kept and listed as `kept`.
- Objects merge key by key. Lists of plain values, such as `community-plugins.json`, merge as sets and keep the
  vault's order. A missing file is created.
- It adds the seed's `.gitignore` exceptions for plugin settings, then installs the pinned plugins the merged
  `community-plugins.json` lists ([community plugins](#community-plugins)).
- `--dry-run` writes nothing. Running it again changes nothing. While Obsidian runs it refuses to write
  (`--allow-running` overrides); with nothing to write it reports and exits 0.
- If the upgrade is already committed, pass the commit before it as `--base`. The tool says so when the base's
  seed matches the current one and a file still differs.

A preference meant for every workspace goes into the kit's seed first and is then released. A setting only one
workspace wants stays in that workspace. The check then lists it as changed, as a reminder.

### Moving the vault

Obsidian keeps its own list of vaults. After a vault moves (v0.2 moved it from the repository root into
`notebook/`), the old entry still opens the old folder. Obsidian then writes default settings into a new
`.obsidian/` there: no community plugins, so no Restricted mode prompt and none of the shortcuts. Use **Open
folder as vault** on `notebook/`, remove the old entry from the vault list, then delete the stray `.obsidian/`.
Both checks report a `.obsidian/` at the repository root.

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
`just check-kb` over the repository, and blocks the commit on violations. Git cannot run it from
`.scions/`, because graft does not keep the executable bit there. The seed therefore has an executable wrapper,
`.githooks/pre-commit`, that runs it with `sh`. Enable the wrapper once per clone:

```sh
git config core.hooksPath .githooks
```

It falls back to `nix develop` when `markdownlint-cli2` is not on `PATH`, and to `nix run .#check-kb` when the
workspace has no `justfile` or `just` is not on `PATH`, but only when `flake.nix` is at the top; a workspace whose
flake is in a subdirectory puts the tools on `PATH`
([adoption](adoption.md#a-workspace-whose-content-must-not-enter-the-nix-store)).

## Sources

- [Obsidian Linter](https://github.com/platers/obsidian-linter)
- [Pinned plugin releases](obsidian-plugins.json), checked against the GitHub release assets
- [Seed Obsidian settings](../seed/common/notebook/.obsidian/app.json)
- [Settings drift check](../tools/check-obsidian.py) and [settings upgrade](../tools/upgrade-obsidian.py)
- [Pre-commit hook](../tools/hooks/pre-commit)
