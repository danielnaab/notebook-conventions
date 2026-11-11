# notebook-kit — agent entrypoint

Public, generic conventions, tools, skills, and a copy-once seed for Markdown work-memory workspaces. Workspaces
pin it as a graft scion. Read [README.md](README.md), then [KB configuration](knowledge-base.yaml).

## Rules for changing this repo

- **Generic only.** This repository is public and consumed by unrelated workspaces. No employer, agency, client,
  project, machine, or person-specific context; use "the owner" and placeholders. `tests/test_hygiene.py` scans for
  known terms; passing it is necessary, not sufficient. Read your diff for context the scan cannot know.
- **Boundaries are the workspace's.** Never add data, account, service, or tool boundaries here. The seed ships a
  skeleton (`seed/profiles/generic/docs/boundaries.md`) that each workspace fills in.
- **Reference over copy.** Prefer content a workspace reads in place from the scion. Add to `seed/` only what a
  workspace must own and edit; every seeded file is a future migration.
- **Every release is a migration.** Update [CHANGELOG.md](CHANGELOG.md) with a `## vX.Y.Z` section and an
  **Upgrading** subsection written as steps an agent who knows only the workspace can apply: what moved, what to
  search for, what to replace, how to tell it is done. A change to seeded Obsidian settings is applied with
  `just upgrade-obsidian`, so test it against the previous seed. Tag releases; stay `0.x` until two workspaces
  run it stably.
- **The `just` menu is an interface.** Workspaces and their agents call `tools/kit.just` recipes by name; renaming
  or removing a recipe, or changing `kit_run`/`graft_run`, is a breaking change with Upgrading steps.
- **Docs follow knowledge-base-kit:** `status` frontmatter, `## Sources`, real relative links. Keep policy-style text short.
- **Verify:** `nix flake check` runs the tests (tool tests, a workspace built from `seed/`, and the hygiene scan);
  `nix run .#check-kb` checks links, status, and Sources here. Tests need no network.
- `.scions/` is graft output; never edit it. Upgrade inputs with `nix run .#graft upgrade`.
- Do not push, tag, or publish without the owner's authorization.
