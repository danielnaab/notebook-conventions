---
status: working
---

# Adopt and upgrade the kit

A workspace uses this repository in three ways: reference content and tools it reads in place from the graft
scion, `seed/` files it copies once and then owns, and a local overlay of its own rules.

## Start a workspace

1. Create the repository. The seed includes an `.envrc` for direnv (`use flake`).
2. Copy the seed. The profile is copied first so its files win; `-n` never overwrites.

   ```sh
   # from a checkout of this repository, into the new workspace root:
   cp -rn seed/profiles/generic/. /path/to/workspace/
   cp -rn seed/common/. /path/to/workspace/
   ```

3. Fill the placeholders: `grep -rn '<<' .` lists them. Names and the owner go in `README.md`, `AGENTS.md`,
   and `knowledge-base.yaml`.
4. Write the boundaries. `docs/boundaries.md` is a skeleton: which data, accounts, tools, and services this
   workspace may use. The kit supplies no boundaries, because they depend on the workspace's context.
5. Materialize the pinned guidance and the kit. Flakes see only Git-tracked files, so track the seed first;
   graft stages the scions itself:

   ```sh
   git init -b main && git add -A     # flake.nix must be tracked for nix to read it
   nix run .#graft                    # writes and stages .scions/ (meta-KB and this kit)
   cp .scions/notebook-conventions/templates/*.md notebook/templates/
   git config core.hooksPath .githooks   # the seeded wrapper runs the kit's hook
   ```

6. Open `notebook/` as the Obsidian vault.
7. Check: `nix run .#check-kb`, `nix run .#check-tasks`, `nix run .#index -- --check`,
   `nix run .#check-obsidian -- --strict`, `nix flake check`.

## What the workspace references in place

| Need | How |
| --- | --- |
| Conventions | Links into `.scions/notebook-conventions/docs/`; the local `docs/conventions.md` states only local rules. |
| Agent skills | `.pi/settings.json` lists `../.scions/notebook-conventions/skills` under `skills`. |
| Tools and flake wiring | `flake.nix` imports `nix/workspace.nix` from the pinned kit input; apps run its `tools/`: `check-kb`, `check-tasks`, `check-templates`, `check-obsidian`, `upgrade-obsidian`, `index`, `move`, and `convert` (the v0.2 upgrade). |
| Hook | The seeded `.githooks/pre-commit` wrapper runs the kit's hook; `core.hooksPath` is `.githooks`. |

## Local overlay

`docs/conventions.md` is the workspace's own file. It links to the pinned kit docs, records the **Meta-KB
conformance** table ([conformance](conformance.md)), and lists local deviations and additions. Local agent skills
add local rules and name the kit skill they extend; they do not copy it.

Templates are copied because Obsidian needs them visible. `nix run .#check-templates` lists which copies still
match the pinned versions. A changed template is a local choice, not an error. Shared Obsidian settings are
seeded for the same reason; `nix run .#check-obsidian` lists which still match the kit's
([Obsidian](obsidian.md#keeping-settings-in-sync)).

## Upgrade

1. `nix run .#graft outdated` shows the pinned and newest tags.
2. `nix run .#graft upgrade notebook-conventions@vX.Y.Z` moves the pin and rebuilds `.scions/`.
   Graft takes a new major only when you name it.
3. Read the kit's `CHANGELOG.md` sections between the tags. **Upgrading** says what to change in the workspace's
   own files, including seeded files that changed.
4. On the upgrade branch, `nix run .#graft migrate` prints a brief for an agent or a person: what moved, the
   rules, the provider's changelog text, the scion diff, and the workspace lines that name moved paths.
5. If the release changed seeded Obsidian settings, quit Obsidian and run `nix run .#upgrade-obsidian`
   ([Obsidian](obsidian.md#keeping-settings-in-sync)); it merges them into the vault's copies and keeps local
   changes.
6. Apply the steps, run `nix flake check` and the repository checks, then commit `flake.nix`, `flake.lock`,
   `.scions/`, and the workspace changes together.

Never edit `.scions/`; it is replaced on every graft.

## Contribute back

A convention that proves useful in one workspace and is free of local context belongs in the kit. Change the kit
first, tag it, then upgrade each workspace. Keep workspace-specific context, data, and boundaries out of the kit.
While the kit is `0.x`, any release may change seeded files, so every release carries an **Upgrading** section.

## Sources

- [Graft README: upgrades and migrations](https://github.com/danielnaab/graft/blob/v2.6.0/README.md#breaking-changes-and-migrations)
- [Meta-KB dependency playbook](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/playbooks/manage-kb-dependencies.md)
- [Seed files](../seed/common/)
