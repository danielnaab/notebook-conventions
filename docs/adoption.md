---
status: working
---

# Adopt and upgrade the kit

A workspace uses this repository in three ways: reference content and tools it reads in place from the graft
scion, `seed/` files it copies once and then owns, and a local overlay of its own rules.

## Start a workspace

1. Create the repository. The seed includes an `.envrc` for direnv (`use flake`); the dev shell has
   [just](https://just.systems) and the kit's tools. Without direnv, run `nix develop`, or put `just` on `PATH`
   another way.
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
   nix run .#graft                    # writes and stages .scions/ (later: just sync)
   cp .scions/notebook-conventions/templates/*.md notebook/templates/
   git config core.hooksPath .githooks   # the seeded wrapper runs the kit's hook
   ```

6. Open `notebook/` as the Obsidian vault.
7. Check: `just check` (graft check, check-kb, check-tasks, `index --check`, check-obsidian),
   `just check-obsidian --strict`, and `nix flake check`. `just` alone lists every operation.

The first graft is `nix run .#graft` because the seeded `justfile` imports the kit's recipes from `.scions/`,
which does not exist until then.

## What the workspace references in place

| Need | How |
| --- | --- |
| Conventions | Links into `.scions/notebook-conventions/docs/`; the local `docs/conventions.md` states only local rules. |
| Agent skills | `.pi/settings.json` lists `../.scions/notebook-conventions/skills` under `skills`. |
| Tools and flake wiring | `flake.nix` imports `nix/workspace.nix` from the pinned kit input; apps run its `tools/`: `check-kb`, `check-tasks`, `check-templates`, `check-obsidian`, `upgrade-obsidian`, `index`, `move`, and `convert` (the v0.2 upgrade). |
| Operations menu | The seeded `justfile` imports `tools/kit.just` from the scion ([run operations with just](#run-operations-with-just)). |
| Hook | The seeded `.githooks/pre-commit` wrapper runs the kit's hook; `core.hooksPath` is `.githooks`. |

## Run operations with just

The seeded `justfile` imports [`tools/kit.just`](../tools/kit.just) from the scion, so the menu arrives with each
upgrade. `just` lists it by group:

| Group | Recipes |
| --- | --- |
| `check` | `check` (graft-check, check-kb, check-tasks, `index --check`, check-obsidian, then `check-local`), `graft-check`, `check-kb`, `check-tasks`, `check-templates`, `check-obsidian` |
| `notes` | `index`, `move OLD NEW` |
| `deps` | `outdated`, `changelog [NAMES]`, `upgrade [TARGETS]`, `migrate`, `sync` (graft with no arguments) |
| `migrations` | `upgrade-obsidian`, `convert` |

Arguments pass straight through, without Nix's `--`: `just index --check`, `just move OLD NEW --dry-run`.
Recipes run from the workspace root wherever `just` is called, so paths are repository-relative.

Underneath, a kit tool runs as `nix run .#TOOL -- ARGS` and graft as `nix run .#graft -- ARGS`; those forms
still work. Local recipes go in the `justfile` below the import. A comment line directly above a recipe is its
description in the list, and `[group('...')]` files it.

### Add local checks

`just check` ends with `check-local`, which the kit leaves empty. Define it in the workspace `justfile`; the seed
sets `allow-duplicate-recipes`, so the workspace's definition replaces the kit's wherever it appears:

```just
# Lint all Markdown
check-local:
    markdownlint-cli2
```

The same setting lets a workspace replace any kit recipe; keep its name and meaning when doing so.

### Override how tools run

Two variables decide how recipes run tools. `kit_run` is a command template in which `{}` becomes the tool's
name, followed by the recipe's arguments; `graft_run` is the command that graft's subcommand and arguments follow.
Set them in the workspace `justfile` (the seed sets `allow-duplicate-variables`, so the workspace's definition
wins wherever it appears), or for one shell with the `KIT_RUN` and `GRAFT_RUN` environment variables, which the
kit's defaults read. Examples, one per line:

```just
kit_run := "{}"                             # the kit's tools are on PATH (the dev shell, or packages.tools)
kit_run := ".local/tools/bin/{}"            # a prebuilt bin directory
kit_run := "nix run path:nix/tools#{} --"   # a separate flake that imports the kit's wiring
graft_run := "nix run github:danielnaab/graft/v2.6.0 --"   # graft's own flake, not the workspace's
```

The pre-commit hook runs `just check-kb` when the workspace has a `justfile` and `just` is on `PATH`, so it
follows the same override; otherwise it runs `nix run .#check-kb`.

### Run the tools without the root flake

Evaluating a workspace's flake copies the repository into the Nix store. A workspace whose content must not be
copied there can build the tools from a separate flake that does not contain the content. `nix/workspace.nix`
outputs `packages.<system>.tools`: one `bin/` with every kit tool, `just`, and `markdownlint-cli2`. Build it from
a small flake (for example in `nix/tools/`) with the same inputs as the seed's `flake.nix` and
`outputs = import "${inputs.notebook-conventions}/nix/workspace.nix" { inherit inputs; }`, put its `bin/` on
`PATH` or link it into an ignored folder, and set `kit_run` to match.

Graft's `outdated`, `upgrade`, and `migrate` also run from graft's own flake against the current directory;
`sync` runs only from the workspace flake. Check graft's documentation for which commands evaluate the
workspace flake (`migrate` runs `nix flake check` unless given `--no-check`).

## Local overlay

`docs/conventions.md` is the workspace's own file. It links to the pinned kit docs, records the **Meta-KB
conformance** table ([conformance](conformance.md)), and lists local deviations and additions. Local agent skills
add local rules and name the kit skill they extend; they do not copy it.

Templates are copied because Obsidian needs them visible. `just check-templates` lists which copies still
match the pinned versions. A changed template is a local choice, not an error. Shared Obsidian settings are
seeded for the same reason; `just check-obsidian` lists which still match the kit's
([Obsidian](obsidian.md#keeping-settings-in-sync)).

## Upgrade

1. `just outdated` shows the pinned and newest tags.
2. `just upgrade notebook-conventions@vX.Y.Z` moves the pin and rebuilds `.scions/`, then prints the next steps.
   Graft takes a new major only when you name it.
3. Read the kit's changelog between the tags (`just changelog notebook-conventions`, or `CHANGELOG.md` in the
   scion). **Upgrading** says what to change in the workspace's own files, including seeded files that changed.
4. On the upgrade branch, `just migrate` prints a brief for an agent or a person: what moved, the rules, the
   provider's changelog text, the scion diff, and the workspace lines that name moved paths.
5. If the release changed seeded Obsidian settings, quit Obsidian and run `just upgrade-obsidian`
   ([Obsidian](obsidian.md#keeping-settings-in-sync)); it merges them into the vault's copies and keeps local
   changes.
6. Apply the steps, run `just check` and `nix flake check`, then commit `flake.nix`, `flake.lock`, `.scions/`,
   and the workspace changes together.

Never edit `.scions/`; it is replaced on every graft.

## Contribute back

A convention that proves useful in one workspace and is free of local context belongs in the kit. Change the kit
first, tag it, then upgrade each workspace. Keep workspace-specific context, data, and boundaries out of the kit.
While the kit is `0.x`, any release may change seeded files, so every release carries an **Upgrading** section.

## Sources

- [Graft README: upgrades and migrations](https://github.com/danielnaab/graft/blob/v2.6.0/README.md#breaking-changes-and-migrations)
- [Meta-KB dependency playbook](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/playbooks/manage-kb-dependencies.md)
- [Seed files](../seed/common/)
- [just manual: imports, settings, and attributes](https://just.systems/man/en/)
