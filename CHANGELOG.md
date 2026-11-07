# Changelog

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
2. Run `nix run .#convert`. It moves `notebook/daily` and `notebook/sessions` under `notebook/records/`, flattens
   session folders, turns folder READMEs in the vault into generated indexes, adds `type` by folder, moves
   `.obsidian/` into `notebook/` and updates its daily-note and template paths and the `.gitignore` patterns, writes
   `notebook/.okfignore`, and replaces unchanged templates. Links follow every move. It lists what is left as
   `by hand:` lines; re-running it is safe.
3. Do the `by hand:` lines: a `description` on each task; a `type` on notes in folders it does not know; prose from
   a replaced README that should live on (in `docs/` or a wiki page); local template changes merged with the new
   frontmatter.
4. In `knowledge-base.yaml` (ask first), take `paths`, `sources`, and `rules` from the seed's
   `seed/common/knowledge-base.yaml`: `rules.checks.okf`, the `records/` and `raw/` source classes, and
   `writeOnce`. Keep local additions.
5. In `README.md`, `AGENTS.md`, and `docs/`, point at `notebook/index.md` and `notebook/tasks/index.md`; the
   convert step rewrote links, so search for text: `grep -rn 'notebook/\(daily\|sessions\)\|tasks/README' --exclude-dir=.scions .`.
   Compare with the seed's `README.md` and `AGENTS.md`, and drop the dated-notes deviation from
   `docs/conventions.md`.
6. Fix links that leave the vault (`nix run .#check-kb` lists them as `escapes-bundle`): make them URLs or
   backticked paths.
7. Reopen the vault in Obsidian at `notebook/`.

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
