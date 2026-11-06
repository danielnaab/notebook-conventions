# Changelog

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
