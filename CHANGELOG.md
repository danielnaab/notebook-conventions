# Changelog

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
