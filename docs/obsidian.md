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
| New notes | `wiki/` (`app.json` → `newFileLocation: folder`, `newFileFolderPath: wiki`), including a note made by clicking a link to a note that does not exist yet |
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
- The releases come from the kit's Nix wiring (`packages.obsidian-plugins` from the kit's [`graft.nix`](../graft.nix)), which
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
workspace wants is declared in that workspace's `notebook-kit.yaml` ([declared deviations](#declared-deviations)); one left
undeclared is listed as changed, as a reminder.

### Declared deviations

A workspace states where its settings deliberately differ from the seed under `obsidian` in its
`notebook-kit.yaml` at the workspace's top ([workspace settings](adoption.md#workspace-settings)). The base stays in
the scion; the deviations are a few lines the workspace owns, so two workspaces on the same kit share everything
else.

```yaml
obsidian:
  settings:
    app.json:                  # settings file -> keys overlaid on the seed
      openBehavior: file
  identity:
    label: Workspace A
    accent: { light: "#3366cc", dark: "#99bbff" }
    stripe: ["#3366cc", "#ffffff", "#cc6633"]
```

- `settings` maps a settings file under `.obsidian/` to the keys it overrides. Objects overlay key by key; a list
  of plain values gains the declared items.
- `identity` tells vaults apart when several are open at once. `accent` is a single CSS color (the existing
  behavior), or `{ light: "#3366cc", dark: "#99bbff" }` with both colors in `#RRGGBB` form. Variants follow
  Obsidian's active theme, including system-driven changes; there is no separate toggle. The light color is the
  static `appearance.json` fallback. Generated CSS overrides the accent HSL/base/hover variables per theme;
  hover darkens in light mode and lightens in dark mode, with black/white control text chosen for contrast.
- `stripe` is a 3px band across the top of the window, in equal color segments. It stays constant across themes;
  without an explicit stripe it uses the single accent, or the light variant. It covers no controls and takes no clicks.
- Optional `label` is 1–64 printable characters on one line. It is a non-clickable badge before the desktop
  status-bar items, visible with collapsed sidebars while the status bar is shown. Its background is the single
  accent or light variant, constant across modes; hex colors get contrasting black/white text. Long labels truncate.
  The kit does not force a hidden status bar to show, add a mobile badge, or overlay note/window controls.
  CSS-generated text is a visual cue, not a reliable semantic label for screen readers or a security marking.
- All identity styling is rendered into `vault-identity.css` and enabled in `appearance.json`. Change `notebook-kit.yaml`,
  not the generated CSS. Check actual link, hover, focus, and control contrast against editor/sidebar backgrounds
  in both modes (4.5:1 for normal text); custom themes can override appearance. There is no blanket accessibility
  guarantee or full theme replacement.
- `upgrade-obsidian` applies the declarations last, so they win over both a kit change and a value set in the
  vault, and reports each as `declare`. Removing `identity` removes the snippet it rendered.
- `check-obsidian` compares the vault with the seed plus the declarations. A file that matches is `same` and
  names the declared keys; anything else is still `changed`, so `--strict` means undeclared drift.
- Both tools read `notebook-kit.yaml` when they run, so a change needs no rebuild: run `just upgrade-obsidian`
  with Obsidian closed.

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
- [Workspace settings reader](../tools/kit_settings.py): both tools read the declared deviations from `notebook-kit.yaml`
- [Pre-commit hook](../tools/hooks/pre-commit)
