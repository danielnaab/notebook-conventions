# Changelog

## v1.2.0 - 2026-11-12

### Added

- `## Notes` before Activity in the daily template, reserved for human-input narrative. Activity remains
  agent-maintained; section ownership does not restrict the owner's ability to edit any part of a note.
- Daily-note ownership and contextual-review guidance in the workflow and start/wrap skills. Agents preserve
  human wording and edits, distinguish actors and proposals, and suggest canonical updates from relevant Notes
  without treating tentative thoughts as tasks or authorization. No background review or new automation.
- A seed-workspace regression test for the empty Notes section and daily heading order.

### Upgrading

1. `just upgrade notebook-kit@v1.2.0`. No tools, Obsidian settings, or plugin pins change.
2. Add `## Notes` before `## Activity` in `notebook/templates/daily.md`, preserving any local template content.
   For an uncustomized template, copy `.scions/notebook-kit/templates/daily.md` over the workspace copy.
3. Update the daily-note description in `notebook/templates/README.md` if the workspace keeps the seeded description.
   Point local ownership/review guidance at the kit's [daily-note rules](docs/workflow.md#daily-notes) instead of copying them.
4. Use Notes in new daily notes. The current day's note may gain the empty heading while preserving all entries;
   leave historical notes unchanged and do not infer or relabel their authorship.
5. Run `just check` and `just check-templates --strict`. The daily template should match the kit unless
   deliberately customized. Commit the pin, lock, generated scions, template, and applicable consumer changes together.

## v1.1.1 - 2026-11-12

### Changed

- The seed pins graft v2.11.0 and knowledge-base-kit v2.1.0, as the kit itself now does. graft v2.11.0 keeps a
  workspace's own `branches:` line in graft-check.yaml and rewrites its docs; knowledge-base-kit v2.1.0 revises
  its style, linking and lifecycle policies. No change to the kit's tools.

### Upgrading

1. `just upgrade`. A workspace seeded earlier keeps its own pins; `just upgrade` (or the weekly upgrade PR)
   moves graft and knowledge-base-kit within their major versions.

## v1.1.0 - 2026-11-11

### Added

- Optional `obsidian.identity.label`: a non-clickable badge before the desktop status-bar items, visible with
  collapsed sidebars. Labels are escaped, limited to one printable line, and truncated rather than covering controls.
- `obsidian.identity.accent` accepts `{ light = "#3366cc"; dark = "#99bbff"; }` as well as the existing single
  CSS color. The rendered snippet switches accent HSL/base/hover variables with Obsidian's theme, including system
  changes. Hover darkens in light mode and lightens in dark mode; contrasting control text is selected automatically.
  The stripe and badge use the light color consistently, which is also the static appearance fallback.
- Regression tests for compatibility, declaration validation/escaping, theme states and sample contrast,
  dry-run/idempotence, drift detection, and changing/removing the label or variants.

### Upgrading

1. `just upgrade notebook-kit@v1.1.0`. Existing single-color declarations and the seeded settings are unchanged;
   no plugin pins move. A single-color identity without a label renders exactly the same CSS as before.
2. Optionally add `label = "Workspace A";` and/or replace the accent string with
   `accent = { light = "#3366cc"; dark = "#99bbff"; };` in the flake's `obsidian.identity` declaration. Both variants
   must be six-digit hex colors; keep an explicit `stripe` if its colors should differ from the light accent.
3. Quit Obsidian, then `just upgrade-obsidian --dry-run` and `just upgrade-obsidian`. Do not hand-edit the generated
   snippet; removing a label or switching back to one accent regenerates it, and removing identity removes it.
4. `just check` and `just check-obsidian --strict`, then reopen the vault and inspect both light and dark modes,
   with sidebars collapsed, including links/hover/focus/controls and actual background contrast. The badge needs
   the desktop status bar visible; CSS text is not a semantic screen-reader label. Custom themes may override it.
5. Commit the flake, lock, scions and settings/snippet together. Nothing changes in workspaces that declare no identity.

## v1.0.0 - 2026-11-11

**Renamed:** notebook-conventions is now **notebook-kit**: something a workspace takes on and keeps upgrading
(tools, skills, structure, and the rules they enforce). It also takes the conventions and the checker from one
repo, [knowledge-base-kit](https://github.com/danielnaab/knowledge-base-kit) v2.0.0 (formerly meta-knowledge-base
and knowledge-base-integrity). The tools and layout are otherwise unchanged; the major version marks the input
rename every workspace has to make.

### Changed

- Every reference to the kit's own name and scion path: `.scions/notebook-kit/`, the `notebook-kit` flake input,
  `import ".scions/notebook-kit/tools/kit.just"`, skill paths, hooks, docs, and the seed.
- `nix/workspace.nix` reads the checker from the `knowledge-base-kit` input (`${inputs.knowledge-base-kit}/src`);
  the `knowledge-base-integrity` input is gone. One input per repo: a second one for the same repo (a `git+https`
  one, say) shares Nix's fetch cache with the first, and one of them gets the wrong tree.
- The seed's `knowledge-base.yaml`: `apiVersion: kb/v1`, imports `.scions/knowledge-base-kit`,
  `precedence: domain-over-imports`. Links to the conventions point at knowledge-base-kit v2.0.0.
- `upgrade-obsidian` also finds the previous seed under `.scions/notebook-conventions/`, so the upgrade that renames
  the scion still merges Obsidian settings against the right base.

### Upgrading

From v0.6.0 or v0.7.0 (take v0.7.0's step too if coming from v0.6.0). In the workspace's flake (`flake.nix`, or the
one in a subdirectory such as `nix/workspace/` or `nix/agent-tools/`):

1. Inputs: replace `notebook-conventions` with
   `notebook-kit = { url = "github:danielnaab/notebook-kit/v1.0.0"; flake = false; };`, and replace both
   `meta-knowledge-base` and `knowledge-base-integrity` with
   `knowledge-base-kit = { url = "github:danielnaab/knowledge-base-kit/v2.0.0"; flake = false; };`.
2. In `outputs`: `import "${inputs.notebook-kit}/nix/workspace.nix"`, and delete `scions = [ ... ]` (every
   `flake = false` input is now a scion), or drop the two old names from it if it lists others to leave out.
3. Re-graft with Nix directly, since the justfile still imports the old path: `nix run .#graft`, or
   `nix run path:$PWD/nix/<dir>#graft` for a flake in a subdirectory. `.scions/notebook-conventions/` and
   `.scions/meta-knowledge-base/` become `.scions/notebook-kit/` and `.scions/knowledge-base-kit/`.
4. `justfile`: `import ".scions/notebook-kit/tools/kit.just"`.
5. Replace `notebook-conventions` with `notebook-kit`, and `.scions/meta-knowledge-base/` with
   `.scions/knowledge-base-kit/`, in the workspace's own files: AGENTS.md, README, docs, `.pi/settings.json` and
   `.githooks/pre-commit` (a missed hook path breaks every commit). This lists them, hidden files included:
   `rg -l --hidden 'notebook-conventions|meta-knowledge-base' --glob '!.scions' --glob '!.git' --glob '!notebook/**'`.
   Leave dated records and logs as written; only links break, and the check in step 7 finds any.
6. `knowledge-base.yaml`: `apiVersion: kb/v1`; the import paths from step 5; `precedence: domain-over-imports`.
7. `just upgrade-obsidian` (it re-renders `vault-identity.css`, whose header now names notebook-kit), then
   `just check`. Commit the flake, `flake.lock`, `.scions/` and the edits together.

## v0.7.0 - 2026-11-11

The daily note template carries no guidance comments, so they stop showing in every note and in the app. The rules
for each section live in the [workflow](docs/workflow.md#daily-notes), where agents read them.

### Changed

- `templates/daily.md`: the HTML comments under `## Activity`, `## Lookups` and `## Agent sessions` are removed;
  the sections themselves are unchanged.

### Upgrading

1. `just upgrade notebook-conventions@v0.7.0`.
2. In `notebook/templates/daily.md`, delete the three `<!-- ... -->` comment blocks, or copy the file from
   `.scions/notebook-conventions/templates/daily.md`. Existing daily notes are records; leave them alone.
   Done when `just check-templates` reports `daily.md` as the same as the kit's copy.

## v0.6.0 - 2026-11-10

A workspace declares its deliberate Obsidian deviations in its flake, so workspaces share the seeded settings
and differ only where they say so, including a visual identity that tells vaults apart.

### Added

- `obsidian` argument to `nix/workspace.nix`: `settings` (settings file -> keys overlaid on the seed) and
  `identity` (`accent`, and `stripe`, the colors of a band across the top of the window)
  ([declared deviations](docs/obsidian.md#declared-deviations)). It reaches `check-obsidian` and
  `upgrade-obsidian` as `$OBSIDIAN_WORKSPACE`.
- `upgrade-obsidian` applies the declarations after the merge (`declare` lines), and renders the
  `vault-identity` CSS snippet from `identity`, or removes it when `identity` is gone.

### Changed

- `check-obsidian` compares the vault with the seed plus the declarations, and checks the identity snippet. A file
  that matches is `same (declared: ...)`; `--strict` now fails only on undeclared drift.

### Upgrading

1. `just upgrade notebook-conventions@v0.6.0`. Nothing changes until the workspace declares something.
2. Run `just check-obsidian`. For each `changed` file, decide: a deliberate choice goes into `obsidian.settings`
   in the flake's `nix/workspace.nix` call (copy the vault's value); anything else is drift to undo by copying
   the seed's value from `.scions/notebook-conventions/seed/common/notebook/.obsidian/`.
3. Optionally add `obsidian.identity = { accent = "<color>"; };` to tell this vault apart from others.
4. Rebuild the tools (`kit_run`), quit Obsidian, run `just upgrade-obsidian`, and commit the flake and
   `notebook/.obsidian/`, including `snippets/vault-identity.css` if an identity is declared. Done when
   `just check-obsidian --strict` exits 0.

## v0.5.0 - 2026-11-09

The seed carries Obsidian's appearance settings, so every workspace gets the same look through `just upgrade`.

### Added

- `seed/common/notebook/.obsidian/appearance.json`: base theme follows the system, default CSS theme and fonts,
  base font size 20, no translucency, ribbon shown ([shared settings](docs/obsidian.md#shared-settings)).

### Upgrading

1. `just upgrade notebook-conventions@v0.5.0`, with Obsidian closed. Its `upgrade-obsidian` step creates
   `notebook/.obsidian/appearance.json`, or, where Obsidian already wrote one, adds the kit's keys and keeps the
   vault's own values, listing each as `kept   appearance.json: local value for <key>`.
   With Obsidian open, quit it and run `just upgrade-obsidian`.
2. A kept value is a local choice. To take the kit's instead, copy it from
   `.scions/notebook-conventions/seed/common/notebook/.obsidian/appearance.json`.
3. Commit `notebook/.obsidian/appearance.json` with the upgrade. Done when `just check-obsidian` lists
   `appearance.json` as same, or changed only in keys the workspace chose to keep.

## v0.4.0 - 2026-11-09

The kit installs its pinned Obsidian community plugins, so a release that adds a plugin or moves a pin reaches
every workspace through `just upgrade`, with the settings, instead of by hand in each vault.

### Added

- `packages.<system>.obsidian-plugins` in `nix/workspace.nix`: each pinned release asset from
  `docs/obsidian-plugins.json`, downloaded and checked against its SHA-256, as `<id>/<asset>`.
- `upgrade-obsidian` installs the pinned plugins the vault's `community-plugins.json` lists, after merging the
  settings: a plugin missing or not matching its pin gets `main.js`, `manifest.json`, and `styles.css`; its
  `data.json` is left alone. It checks each asset against the pin before copying. `--no-plugins` merges settings
  only. Run without the kit's Nix wiring, it lists the plugins to install and installs none.

### Changed

- `just upgrade` runs `just upgrade-obsidian` after graft, in a fresh `just` so a workspace whose `kit_run` names
  a built tools path gets the new pin's tools. If Obsidian is open it does not run, and `just upgrade` says so.
- A workspace opts out of a kit plugin by removing it from `community-plugins.json`; later upgrades keep the
  removal and install nothing for it.
- [Obsidian](docs/obsidian.md#community-plugins) and [adoption](docs/adoption.md): installing the plugins is
  `just upgrade-obsidian`, on each clone and each upgrade; the hand-download steps are gone. Obsidian's
  one-time trust prompt per vault and device is unchanged.

### Upgrading

1. `just upgrade notebook-conventions@v0.4.0`, with Obsidian closed. It runs `upgrade-obsidian`, which installs
   the plugins: look for `install   plugin <id> <version>` lines. With Obsidian open, quit it and run
   `just upgrade-obsidian`.
2. A workspace whose `kit_run` runs the tools some other way than the kit's Nix wiring (the default `nix run`,
   or the `tools` package from `nix/workspace.nix`) sees `by hand: plugin ...` lines instead; point `kit_run` at
   the kit's tools.
3. A workspace whose boundaries rule out a kit plugin: remove its id from
   `notebook/.obsidian/community-plugins.json` before step 1.
4. Done when `just check-obsidian` shows each enabled plugin as `matches the pinned release`. Open the vault and
   accept Obsidian's prompt to trust its plugins. Plugin code stays ignored by git; there is nothing new to
   commit for it. On each other clone, run `just upgrade-obsidian` once after pulling.

## v0.3.1 - 2026-11-09

Fixes found while upgrading a workspace to v0.3.0.

### Fixed

- `upgrade-obsidian` works out its plan first and refuses to run while Obsidian is open only if it would write
  something (a merge, a created file, a `.gitignore` line). With nothing to write it reports and exits 0.
  `--dry-run` and `--allow-running` are unchanged.
- The store probe in [adoption](docs/adoption.md#a-workspace-whose-content-must-not-enter-the-nix-store) runs
  `xargs -0 -r`: without `-r`, when no store path was new, `grep -r` searched the current directory and reported
  the workspace's own note.
- The probe's control is `nix flake prefetch --json "git+file://$PWD?dir=nix/workspace"`. The old control,
  `nix flake metadata`, does not copy the source on Nix with lazy trees, so it proved nothing.

### Changed

- The probe is run in a throwaway workspace with synthetic content, never a copy of real notes, since the control
  copies the repository into the store; `nix store delete` removes the copy. `nix flake prefetch --json
  path:nix/workspace` is documented as a direct check: its store path holds only `flake.nix` and `flake.lock`.
- Adoption: a `git+file:` or plain-path reference *can* copy the whole repository (on lazy-tree Nix, only when
  the source is needed); the advice to name the flake as `path:nix/workspace` is unchanged.
- Seed `flake.nix` pins notebook-conventions v0.3.1.

### Upgrading

From v0.3.0. Nothing in the workspace's own files changes: `just upgrade notebook-conventions@v0.3.1`, then
`just check`, and commit the flake's `flake.nix` and `flake.lock` with `.scions/`. To tell it is done,
`grep -rn 'notebook-conventions/v0.3.1' flake.nix nix/workspace/flake.nix 2>/dev/null` names the new pin. If the
workspace keeps a note or script with the old probe (`xargs -0 grep`, or `nix flake metadata` as the control),
change it as the adoption guide now says, and run the control only in a throwaway workspace.

## v0.3.0 - 2026-11-07

A `just` operations menu, read in place from the scion: `just` lists every operation a workspace has, grouped,
and recipes pass flags through without Nix's `--`.

### Added

- `tools/kit.just`, imported by the workspace's `justfile`. Groups: `check` (`check`, `check-kb`, `check-tasks`,
  `check-templates`, `check-obsidian`), `notes` (`index`, `move`), `deps` (`outdated`, `changelog`, `upgrade`,
  `migrate`, `sync`), and `migrations` (`upgrade-obsidian`, `convert`). `just check` runs check-kb, check-tasks,
  `index --check`, and check-obsidian, then the workspace's `check-local`. `just upgrade` prints the next steps.
  `just changelog` needs a graft that has the `changelog` command.
- Two variables decide how recipes run tools: `kit_run` (default `nix run .#{} --`, `{}` is the tool) and
  `graft_run` (default `nix run .#graft --`). A workspace sets them in its `justfile`, or per shell with `KIT_RUN`
  and `GRAFT_RUN` ([override how tools run](docs/adoption.md#override-how-tools-run)).
- `packages.<system>.tools` in `nix/workspace.nix`: every kit tool, `just`, and `markdownlint-cli2` in one
  `bin/`, for workspaces that run the tools without evaluating their own flake
  ([run the tools without the root flake](docs/adoption.md#run-the-tools-without-the-root-flake)).
- Seed: `justfile`, which imports the menu, lists it as the default recipe, and shows where overrides and local
  recipes go.
- `just graft-check`: graft's `check` (`.scions/` as git would commit it, and graft's workflows, against the pins).
  `just check` runs it first. Needs graft v2.7.0 or later, as `just changelog` does.
- A workspace whose content must not enter the Nix store: its one flake in a subdirectory (`nix/workspace`), run
  as a `path:` flake, with graft v2.7.0's `flakeDir`
  ([adoption](docs/adoption.md#a-workspace-whose-content-must-not-enter-the-nix-store)). `nix/workspace.nix`
  takes the same `flakeDir`; when it is not `.`, there is no task check, whose source would hold no notes, and
  `just check` is the check.

### Changed

- The dev shell has `just` and the kit's tools on `PATH` (the `tools` package).
- The pre-commit hook runs `just check-kb` when the workspace has a `justfile` and `just` is on `PATH`, so it
  follows the workspace's `kit_run`; otherwise `nix run .#check-kb` as before. It falls back to Nix
  (`nix develop`, `nix run .#check-kb`) only when `flake.nix` is at the top, and otherwise says to put the tools on
  `PATH`.
- "Run the tools without the root flake" no longer suggests a second tools flake: one flake in a subdirectory
  serves graft and the tools.
- `nix/workspace.nix`'s `extraPackages` go into the `tools` package as well as the dev shell, so a workspace's
  own tools come from the same flake.
- Docs, skills, the seed, and tool messages name `just` recipes (`just index`, `just move OLD NEW`,
  `just check`) instead of `nix run .#…` forms, which still work underneath.
- Seed `knowledge-base.yaml`: `justfile` is ask-first.

### Upgrading

From v0.2.2. Work on a branch with a clean tree.

1. Upgrade graft to v2.7.0 or later first (`nix run .#graft upgrade graft@v2.7.0`, then its Upgrading steps):
   `just check` runs `graft check` and `just changelog` runs `graft changelog`, which earlier graft lacks. Then
   `nix run .#graft upgrade notebook-conventions@v0.3.0` (the last time in this form).
2. Copy the seed's justfile: `cp -n .scions/notebook-conventions/seed/common/justfile justfile` and
   `git add justfile`. If the workspace already has a `justfile`, add the seed's two `set` lines, its `import`,
   and its `default` recipe at the top instead, and rename any local recipe whose name collides with a kit
   recipe unless it is meant to replace it.
3. Get `just`: with direnv, reload the dev shell (`direnv reload`), which now has it; otherwise install it, or use
   `nix shell nixpkgs#just`.
4. If the workspace does not run the tools through its root flake, set `kit_run` (and `graft_run` if graft runs
   another way) in the `justfile`, below the import. A hand-kept bin directory of kit tools can be replaced by
   the `tools` package from a flake that imports the kit's wiring.
5. If the workspace has its own checks (scripts, a lint step), define `check-local` in the `justfile` to run them
   from `just check`.
6. Replace `nix run .#` forms in the workspace's own files (not `.scions/`):
   `grep -rn 'nix run \.#' --exclude-dir=.scions --exclude-dir=.git .`. `nix run .#TOOL -- ARGS` becomes
   `just TOOL ARGS`; `nix run .#graft outdated|upgrade|migrate` becomes `just outdated|upgrade|migrate`;
   `nix run .#graft` becomes `just sync`. In `AGENTS.md`, compare with the seed's, which says to run `just` to list
   operations and to verify with `just check`. Keep the first `nix run .#graft` in bootstrap instructions: the
   menu lives in `.scions/`.
7. In `knowledge-base.yaml` (ask first), add `justfile` to `rules.writes.askFirst`.
8. Optional: to keep the workspace's content out of the Nix store, move to the subdirectory layout
   ([adoption](docs/adoption.md#a-workspace-whose-content-must-not-enter-the-nix-store)): `git mv flake.nix
   flake.lock nix/workspace/`; add `flakeDir = "nix/workspace";` to the `mkFlake` call and to the
   `nix/workspace.nix` import's arguments; set `kit_run` and `graft_run` in the `justfile` to
   `nix run path:nix/workspace#…`; change `.envrc` to `use flake path:nix/workspace`; `nix flake lock
   "path:$PWD/nix/workspace"`, `just sync`, and commit. A workspace that built its tools from a second flake
   (for example `nix/tools/`) deletes it and points whatever ran those tools at the one flake. Replace
   `nix run .#`, `nix develop`, and `nix flake check` in the workspace's own files with `just` recipes or
   `path:nix/workspace` forms.

Done when `just` lists the `check`, `deps`, `migrations`, and `notes` groups, `just check` passes (it now
includes `graft-check`), and a commit that stages Markdown runs the hook.

## v0.2.2 - 2026-11-07

### Added

- `nix run .#upgrade-obsidian` applies a release's seeded Obsidian settings to the vault. For each seeded file it
  merges the old seed (in the scion at `--base`, default `HEAD`), the new seed, and the vault's copy: kit changes
  apply where the vault kept the old value, and local changes are kept and reported. It creates missing files and
  adds the seed's `.gitignore` exceptions for plugin settings. It does not install plugins; `--dry-run` writes
  nothing. It refuses to write while Obsidian is running.
- `check-obsidian` and `upgrade-obsidian` report a `.obsidian/` at the repository root. Obsidian creates one,
  with default settings, when it still opens the vault from before the v0.2 move. That is why a vault there has no
  community plugins and none of the shortcuts ([Obsidian](docs/obsidian.md#moving-the-vault)).

### Changed

- `convert` says to remove the old root vault from Obsidian's list, not only to open `notebook/`.

### Upgrading

From v0.2.1, nothing changes in the workspace's files.

1. `nix run .#graft upgrade notebook-conventions@v0.2.2`.
2. If the workspace has not applied v0.2.1's Obsidian settings yet, quit Obsidian and run
   `nix run .#upgrade-obsidian` instead of v0.2.1's steps 2 and 3. Read its `kept` and `by hand:` lines.
3. If either tool reports a `.obsidian/` at the repository root, open `notebook/` as the vault, remove the old
   vault from Obsidian's list, and delete that folder.

Done when `nix run .#check-obsidian` reports no stale folder and every `changed` file is a deliberate local choice.

## v0.2.1 - 2026-11-07

The seed carries the full set of shared Obsidian preferences, and a check reports where a vault has drifted
from them.

### Added

- **Shortcuts** (`notebook/.obsidian/hotkeys.json`): `Mod-P` opens Quick Switcher++ file mode and `Mod-Shift-P` its
  command mode, with no shortcut left on the stock command palette. `Mod-Shift-F` opens vault-wide Search, and the
  stock quick switcher keeps `Mod-O`.
- **Plugins:** Advanced Tables (`table-editor-obsidian`) and Quick Switcher++ (`darlal-switcher-plus`) join
  Calendar and Linter in `community-plugins.json`. Advanced Tables' `data.json` is seeded, and `.gitignore`
  tracks both plugins' `data.json`.
- **Plugin pins:** [`docs/obsidian-plugins.json`](docs/obsidian-plugins.json) records the reviewed release of
  each of the four plugins: version, source commit, minimum Obsidian version, and release-asset SHA-256 hashes.
  The workspace reads it in place.
- **Layout preset** (`notebook/.obsidian/layout-preset.json`): Calendar above Search in the right sidebar, with no
  open files. Apply it by hand with the vault closed ([Obsidian](docs/obsidian.md#layout-preset)).
- `nix run .#check-obsidian` compares the vault's shared settings with the seed's (as JSON, so Obsidian's
  reformatting is not drift) and shows each pinned plugin's installed state. `--strict` exits 1 on changed or
  missing settings.

### Upgrading

From v0.2.0; the steps change seeded files only.

1. `nix run .#graft upgrade notebook-conventions@v0.2.1`.
2. `nix run .#check-obsidian` lists the seeded settings as same, changed, or missing. For each `missing` file,
   copy it from `.scions/notebook-conventions/seed/common/notebook/.obsidian/`. For `changed` files, merge the
   kit's entries if the workspace wants them: `community-plugins.json` gains the two plugins, and
   `hotkeys.json` is new. Close Obsidian first, because it overwrites these files while running.
3. In `.gitignore`, add the exceptions for `table-editor-obsidian` and `darlal-switcher-plus` beside the existing
   Calendar and Linter lines, as in `seed/common/.gitignore`. `git status` should then show
   `notebook/.obsidian/plugins/table-editor-obsidian/data.json` and none of the plugin code.
4. If local docs list the shortcuts, plugins, or layout, link to the kit's
   [Obsidian](docs/obsidian.md) page instead. Keep the workspace's own plugin approvals and boundaries.
5. Install the plugins the workspace's boundaries allow, in the Obsidian UI or from the pinned releases.

Done when `nix run .#check-obsidian` lists no `missing` files and every `changed` file is a deliberate local
choice, and `nix run .#check-kb` and `nix flake check` pass.

## v0.2.0 - 2026-11-06

`notebook/` becomes the Obsidian vault and an [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle, organized by lifecycle. Breaking: notes move, and the checks require a `type` on every note.

### Changed

- **Layout** ([layout](docs/layout.md)): `raw/` (sources as captured), `records/` (dated notes written once:
  `records/daily/`, `records/sessions/`), `tasks/`, `wiki/`, and `templates/`. Sessions are single files,
  `records/sessions/YYYY-MM/YYYY-MM-DD-<slug>.md`, with a sibling folder only for artifacts.
- **Vault:** Obsidian opens `notebook/`; `.obsidian/` moves into it. Code, docs, and `.scions/` stay outside.
- **Notes** carry OKF frontmatter: a required `type`; `title`, `description`, and `aliases` recommended;
  `sources`, `generated`, `verified`, and `stale_after` where they apply. Templates carry their note's `type`.
- **Indexes:** folder `README.md` files inside the vault become generated OKF `index.md` listings; the vault root's
  declares `okf_version: "0.2"`. Kit guidance that lived in them is in the kit docs.
- **Tasks:** `tasks/index.md` is generated, sectioned by status; records need `type: Task` and a `description`.
  `check-tasks` fails when the index is stale instead of checking a hand-kept one.
- **Links** stay inside the vault; links out of it are URLs or backticked paths. Missing notes are reported as
  unwritten and do not fail; a link to a note that exists under the same name elsewhere fails.
- **Write rules:** `rules.writes.writeOnce` marks `records/**` and `raw/**`.
- **Seed flake:** `flake.nix` imports `nix/workspace.nix` from the pinned kit input instead of `.scions/`, so the
  dev shell and checks exist before the first graft; `.envrc` is a plain `use flake`.
- **Pins:** meta-knowledge-base v1.1.0 (raw and historical layers, structured provenance) and
  knowledge-base-integrity v0.4.0 (OKF checks). The deviation for dated notes without `status` is retired.

### Added

- `nix run .#index` generates the `index.md` listings (`--check` reports stale ones).
- `nix run .#move -- OLD NEW` moves a note or folder and rewrites relative links to and from it.
- `nix run .#convert` converts a v0.1 workspace (see Upgrading).
- `notebook/.okfignore` (`.gitignore` syntax) keeps `templates/` out of the bundle, per option B of
  [OKF issue #58](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58).

### Removed

- `docs/proposal-okf-vault.md`: adopted by this release.

### Upgrading

Work on a branch with a clean tree.

1. In `flake.nix`, set `notebook-conventions` to `v0.2.0`, `meta-knowledge-base` to `v1.1.0`, and
   `knowledge-base-integrity` to `v0.4.0`; run `nix run .#graft`.
2. In `flake.nix`, replace the `outputs` with the seed's (`seed/common/flake.nix`): the wiring import reads
   `"${inputs.notebook-conventions}/nix/workspace.nix"`. If `.envrc` is the seeded watcher, make it `use flake`.
3. Run `nix run .#convert`. It moves `notebook/daily` and `notebook/sessions` under `notebook/records/`, flattens
   session folders, turns the seeded folder READMEs into generated indexes, renames existing `index.md` notes to
   `map.md` (OKF reserves the name), adds `type` by folder, moves `.obsidian/` into `notebook/` and updates its
   daily-note and template paths and the `.gitignore` patterns, writes `notebook/.okfignore`, and replaces
   unchanged templates. Links follow every move. It lists what is left as `by hand:` lines. Running it again
   changes nothing; if it is interrupted, restore with `git checkout -- . && git clean -fd` and run it again.
4. Do the `by hand:` lines: a `description` on each task; a `type` on notes in folders it does not know; prose from
   a replaced README that should live on (in `docs/` or a wiki page); local template changes merged with the new
   frontmatter.
5. In `knowledge-base.yaml` (ask first; the OKF checks need it), take `paths`, `sources`, and `rules` from the seed's
   `seed/common/knowledge-base.yaml`: `rules.checks.okf`, the `records/` and `raw/` source classes, and
   `writeOnce`. Keep local additions.
6. In `README.md`, `AGENTS.md`, and `docs/`, point at `notebook/index.md` and `notebook/tasks/index.md`; the
   convert step rewrote links, so search for text: `grep -rn 'notebook/\(daily\|sessions\)\|tasks/README' --exclude-dir=.scions .`.
   Compare with the seed's `README.md` and `AGENTS.md`, and drop the dated-notes deviation from
   `docs/conventions.md`.
7. Fix links that leave the vault (`nix run .#check-kb` lists them as `escapes-bundle`): make them URLs or
   backticked paths.
8. Reopen the vault in Obsidian at `notebook/`.

Done when `nix run .#check-kb`, `nix run .#check-tasks`, `nix run .#index -- --check`, and `nix flake check` pass.

## v0.1.4 - 2026-11-06

### Fixed

- The pre-commit hook linted staged files under `.scions/`. It passes staged paths to `markdownlint-cli2` by name,
  which bypasses the `.scions/**` ignore, so any commit that staged the scion failed on the kit's seed files,
  whose links resolve only inside a workspace. That includes a workspace's first commit and every graft upgrade.
  The hook now leaves `.scions/` out.
- The seed pins this release.

### Upgrading

Nothing to change by hand: the hook runs from the scion, so `nix run .#graft upgrade` applies the fix. Done when a
commit that stages `.scions/` passes the hook. If a commit was made with `--no-verify` to get past this, nothing
needs redoing.

## v0.1.3 - 2026-11-06

### Changed

- graft v2.6.0: the seed's `flake.nix` uses `mkFlake`, and the docs name its subcommands
  (`nix run .#graft upgrade`). `nix run .#graft` now stages `.scions/`, so the adoption guide drops `git add .scions`.
- The seed pins this kit at the release it ships in. It had stayed at `v0.1.0`.

### Fixed

- The seed's `.envrc` failed in a new workspace: the dev shell comes from the kit, which isn't there before the
  first `nix run .#graft`. It now says what to run instead. It also watches the kit's wiring, so a graft or an
  upgrade reloads the shell; `use flake` watches only `flake.nix` and `flake.lock`.

### Upgrading

Needs graft v2.6.0. In `flake.nix`, move graft to `v2.6.0`, then replace the `outputs` that call `mkGraft` with the
ones in `seed/common/flake.nix`, keeping any local changes. `graft upgrade` can't make this change. Copy
`seed/common/.envrc` over the workspace's `.envrc` if it is the seeded `use flake`. Then `nix run .#graft`, and
`nix flake check`.

## v0.1.2 - 2026-11-06

### Added

- A [CC0 1.0 Universal](LICENSE) license. It is exported with the scion.

### Upgrading

Nothing to change. A workspace that redistributes this kit's content should keep the `LICENSE` file with it.

## v0.1.1 - 2026-11-06

### Fixed

- The pre-commit hook could not run from the scion: graft does not keep the executable bit on files in `.scions/`,
  so git ignored `core.hooksPath` set to the kit's `tools/hooks`. The seed now has an executable wrapper,
  `.githooks/pre-commit`, that runs the kit's hook with `sh`.

### Upgrading

If you enabled the hook with `core.hooksPath .scions/notebook-conventions/tools/hooks` (v0.1.0), it never ran:

1. Copy the wrapper, keeping its executable bit:
   `cp -n .scions/notebook-conventions/seed/common/.githooks/pre-commit .githooks/pre-commit` after
   `mkdir -p .githooks`, then `chmod +x .githooks/pre-commit` and track it with `git add`.
2. `git config core.hooksPath .githooks`.
3. Update any local text that tells people to set the old path.
4. Done when `git commit` on a staged Markdown file runs `markdownlint-cli2` and `nix run .#check-kb`.

## v0.1.0 - 2026-11-06

First release, extracted from a working workspace.

### Added

- Conventions in `docs/`: layout, work-memory workflow (logging levels, checkpoints, lookup signals), task workflow,
  meta-KB conformance, Obsidian and Markdown formatting, adoption and upgrade.
- Canonical note templates, and the generic agent skills `notebook-start` and `notebook-wrap`.
- Tools: `check-tasks` (task folder configurable with `rules.checks.tasks.path`), `check-kb` (runs
  knowledge-base-integrity), `check-templates` (template drift), and a pre-commit hook.
- `nix/workspace.nix`: dev shell, check apps, and the task check for a workspace flake.
- `seed/`: starter files for a new workspace, with a generic boundaries skeleton.
- Tests, including a workspace built from `seed/` with every check run on it, and a hygiene scan that keeps the
  public kit generic.

### Upgrading

Nothing to upgrade from. To start a workspace, follow [the adoption guide](docs/adoption.md). A workspace that
already follows these conventions by hand should replace its copies of the shared docs, templates, skills, and
check scripts with references to the scion, keep its own boundaries and conformance table in a local
`docs/conventions.md`, and point its flake at `nix/workspace.nix`.
