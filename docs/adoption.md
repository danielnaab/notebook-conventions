---
status: working
---

# Adopt and upgrade the kit

A workspace uses this repository in three ways: reference content and tools it reads in place from the graft
scion, `seed/` files it copies once and then owns, and a local overlay of its own rules.

## Start a workspace

This needs [graft](https://github.com/danielnaab/graft) v2.13.0 or later, Nix 2.27 or later, and git.

1. Create the repository. The seed includes an `.envrc` for direnv (`use flake`); the dev shell has
   [just](https://just.systems) and the kit's tools. Without direnv, run `nix develop`, or put `just` on `PATH`
   another way. If the notes must never be copied into the Nix store, use the
   [subdirectory layout](#a-workspace-whose-content-must-not-enter-the-nix-store) from the start.
2. Copy the seed. The profile is copied first so its files win; `-n` never overwrites.

   ```sh
   # from a checkout of this repository, into the new workspace root:
   cp -rn seed/profiles/generic/. /path/to/workspace/
   cp -rn seed/common/. /path/to/workspace/
   ```

3. Fill the placeholders: `grep -rn '<<' .` lists them. Names and the owner go in `README.md`, `AGENTS.md`,
   and `knowledge-base.yaml`. Settings for the kit's tools go in `notebook-kit.yaml`
   ([workspace settings](#workspace-settings)).
4. Write the boundaries. `docs/boundaries.md` is a skeleton: which data, accounts, tools, and services this
   workspace may use. The kit supplies no boundaries, because they depend on the workspace's context.
5. Graft the kit and the checker it runs. Each becomes a git submodule in `.scions/` at a release tag:

   ```sh
   git init -b main && git add -A
   nix run github:danielnaab/graft/v2.13.0 -- add --scions .scions https://github.com/danielnaab/knowledge-base-kit@v2.2.0
   nix run github:danielnaab/graft/v2.13.0 -- add https://github.com/danielnaab/notebook-kit@v2.0.0
   git commit -m "Seed the workspace"   # Nix reads the scions at the commits the repository records
   nix flake lock
   cp .scions/notebook-kit/templates/*.md notebook/templates/
   git config core.hooksPath .githooks   # the seeded wrapper runs the kit's hook
   ```

6. Run `just upgrade-obsidian` to install the pinned community plugins (on each clone, since plugin code is not
   tracked), then open `notebook/` as the Obsidian vault and trust its plugins when asked.
7. Check: `just check` (graft check, check-kb, check-tasks, `index --check`, check-obsidian),
   `just check-obsidian --strict`, and `nix flake check`. `just` alone lists every operation.

A fresh clone's `.scions/` folders are empty until `git submodule update --init` (or `just sync`): Nix fetches the
scions itself, but `just` reads the kit's menu, and the hook the kit's script, from the folders. The seeded
`justfile` imports the menu with `import?`, so it still lists the workspace's own recipes before then, as long as
no workspace recipe lists a kit recipe as a dependency (`just` then rejects the whole file): call kit recipes from
a recipe's body, `@{{just_executable()}} --justfile {{quote(justfile())}} RECIPE`.

## What the workspace references in place

| Need | How |
| --- | --- |
| Conventions | Links into `.scions/notebook-kit/docs/`; the local `docs/conventions.md` states only local rules. |
| Agent skills | `.pi/settings.json` lists `../.scions/notebook-kit/skills` under `skills`. |
| Tools and flake wiring | The kit's [`graft.nix`](../graft.nix): graft's `mkFlake` puts the tools in `packages.<system>.tools` (and the dev shell) and an app per tool: `check-kb`, `check-tasks`, `check-templates`, `check-obsidian`, `upgrade-obsidian`, `nb-index`, `nb-move`, and `nb-convert` (the v0.2 upgrade), plus `just` and `markdownlint-cli2`; `packages.<system>.obsidian-plugins`; and the task check `checks.<system>.notebook-kit-tasks` when the flake's source has a `notebook-kit.yaml`. `flake.nix` names no kit. |
| Settings | `notebook-kit.yaml` at the top, read when a tool runs ([workspace settings](#workspace-settings)). |
| Operations menu | The seeded `justfile` imports `tools/kit.just` from the scion ([run operations with just](#run-operations-with-just)). |
| Hook | The seeded `.githooks/pre-commit` wrapper runs the kit's hook; `core.hooksPath` is `.githooks`. |

## Workspace settings

`notebook-kit.yaml` at the workspace's top holds its settings for the kit's tools, read each time a tool runs
(not Nix arguments: changing one needs no rebuild). Every key is optional; without the file, the defaults hold.

```yaml
tasks: false          # the workspace keeps no task records: check-tasks and the task check skip (default: true)
obsidian:             # deliberate deviations from the kit's seeded Obsidian settings
  settings:
    app.json:
      openBehavior: file
  identity:
    label: Workspace A
    accent: { light: "#3366cc", dark: "#99bbff" }
    stripe: ["#3366cc", "#cc6633"]
```

`obsidian` is described in [Obsidian: declared deviations](obsidian.md#declared-deviations). The tools read the
file in the directory they run from (`--root`), which `just` makes the workspace's top. An unknown key or a wrong
type is an error that names the file.

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

Underneath, a kit tool runs as `nix run .#TOOL -- ARGS` (`just index` runs the tool `nb-index`) and graft as
`nix run .#graft -- ARGS`; those forms still work. Local recipes go in the `justfile` below the import. A comment
line directly above a recipe is its description in the list, and `[group('...')]` files it.

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
kit_run := "nix run path:nix/workspace#{} --"   # a flake in a subdirectory (content kept out of the store)
graft_run := "nix run path:nix/workspace#graft --"         # graft from that flake
```

The pre-commit hook runs `just check-kb` when the workspace has a `justfile` and `just` is on `PATH`, so it
follows the same override; otherwise it runs `nix run .#check-kb`.

### Run the tools without the root flake

A workspace whose content must not be copied into the Nix store has no flake at its top; its one flake is in a
subdirectory and the `justfile` names it
([content kept out of the Nix store](#a-workspace-whose-content-must-not-enter-the-nix-store)). The flake also
outputs `packages.<system>.tools`, one `bin/` with every kit tool, `just`, and `markdownlint-cli2`, for putting
them on `PATH` (then `kit_run := "{}"`). Tools the workspace's own agents need join them through mkFlake's
`perSystem`, which also reaches the dev shell, so one flake builds every tool:

```nix
  outputs = inputs: inputs.graft.lib.mkFlake {
    inherit inputs;
    dir = ".scions";
    perSystem = { pkgs, ... }: { tools = { inherit (pkgs) jq; }; };
  };
```

```sh
nix build --out-link .local/tools path:nix/workspace#tools   # .local/tools/bin/, ignored by the seed
```

## A workspace whose content must not enter the Nix store

Evaluating a flake at a Git repository's top copies every tracked file into the Nix store, which every user of
the machine can read: every `nix run .#…`, `nix develop`, `nix flake check`, and direnv's `use flake`. When the
notes must not land there, move the workspace's one flake into a subdirectory and run it as a `path:` flake,
which copies only that directory. The scions live under it
([graft: a flake in a subdirectory](https://github.com/danielnaab/graft/blob/v2.13.0/docs/guides/flake-in-a-subdirectory.md)).

```text
nix/workspace/flake.nix    the seed's flake.nix, moved, without `inputs.self.submodules`
nix/workspace/flake.lock
nix/workspace/.scions/     the scions (git submodules), under the flake
notebook-kit.yaml          still at the top: the tools read it where they run
justfile                   names the path: flake and the scions under it
.envrc                     use flake path:nix/workspace
```

In `nix/workspace/flake.nix`:

```nix
  inputs.graft.url = "github:danielnaab/graft/v2.13.0";
  outputs = inputs: inputs.graft.lib.mkFlake { inherit inputs; dir = ".scions"; };
```

Graft the scions there: `nix run github:danielnaab/graft/v2.13.0 -- add --scions nix/workspace/.scions URL@TAG`.
In the `justfile`:

```just
import? "nix/workspace/.scions/notebook-kit/tools/kit.just"
kit_run := "nix run path:nix/workspace#{} --"
graft_run := "nix run path:nix/workspace#graft --"
```

and point `.githooks/pre-commit`, `.pi/settings.json`, `knowledge-base.yaml`'s imports, and links at
`nix/workspace/.scions/`.

What changes:

- Lock once from the top with an absolute path, `nix flake lock "path:$PWD/nix/workspace"`: Nix does not write
  the lock of a relative `path:` flake. `just upgrade` re-locks by itself.
- A `path:` flake reads the working tree, so a fresh clone needs `git submodule update --init` (or `just sync`)
  before any build: an empty scion leaves its tools out, with a warning.
- `just check` is the check. The flake's source holds no notes and no `notebook-kit.yaml`, so it has no task
  check; `just check` runs `graft check` and the kit's tools on the working tree.
  `nix flake check path:nix/workspace` still evaluates the flake.
- Name the flake as `path:nix/workspace` in every Nix command, or let `just` do it. Inside a Git checkout a plain
  path (`.`, `nix/workspace`) or `git+file:` reference can copy the whole repository, even with `?dir=`;
  without lazy trees, every command does.
- The pre-commit hook needs `markdownlint-cli2` and `just` on `PATH` (direnv, or the `tools` package): without
  a `flake.nix` at the top it has no Nix fallback.
- An upgrade commits the moved scions and `nix/workspace/flake.lock` together.

To check the layout, use a throwaway workspace with synthetic content (for example one built from `seed/`) and the
same `nix/workspace/` and `justfile`, never a copy of real notes: the control below copies the whole repository
into the store. Commit a random string in a note, `touch STAMP`, run the operations you use (`just`,
`just check`, direnv), and search the store paths created since:

```sh
find /nix/store -mindepth 1 -maxdepth 1 -cnewer STAMP ! -name .links -print0 | xargs -0 -r grep -rlsF STRING
```

- `-cnewer`: Nix sets every store path's modification time to 1970, so `-newer` finds nothing.
- `xargs -r`: when no store path is new, plain `xargs` still runs `grep -r` with no files, which then searches
  the current directory and reports the workspace's own note.
- The control is `nix flake prefetch --json "git+file://$PWD?dir=nix/workspace"`: it copies the repository and
  prints the copy's `storePath`, and the search then finds the string. `nix flake metadata` and `nix develop` are
  no control: on Nix with lazy trees (Determinate Nix, for one) they need not copy the source. Remove the copy
  with `nix store delete STOREPATH`.
- `nix flake prefetch --json path:nix/workspace` checks directly: its `storePath` holds only the flake's directory.

## Local overlay

`docs/conventions.md` is the workspace's own file. It links to the pinned kit docs, records the **knowledge-base-kit
conformance** table ([conformance](conformance.md)), and lists local deviations and additions. Local agent skills
add local rules and name the kit skill they extend; they do not copy it.

Templates are copied because Obsidian needs them visible. `just check-templates` lists which copies still
match the pinned versions. A changed template is a local choice, not an error. Shared Obsidian settings are
seeded for the same reason; `just check-obsidian` lists which still match the kit's
([Obsidian](obsidian.md#keeping-settings-in-sync)).

## Upgrade

1. `just outdated` shows the pinned and newest tags.
2. `just upgrade notebook-kit@vX.Y.Z` moves the scion to the new release tag (and stages it), then prints the
   next steps. Graft takes a new major only when you name it.
3. Read the kit's changelog between the tags (`just changelog notebook-kit`, or `CHANGELOG.md` in the
   scion). **Upgrading** says what to change in the workspace's own files, including seeded files that changed.
4. On the upgrade branch, `just migrate` prints a brief for an agent or a person: what moved, the rules, the
   provider's changelog text, its changes, and the workspace lines that name moved paths.
5. Step 2 also ran `just upgrade-obsidian` ([Obsidian](obsidian.md#keeping-settings-in-sync)): it merges the
   kit's seeded settings into the vault's copies, keeping local changes, and installs the pinned plugins. If
   Obsidian was open, it did not run: quit Obsidian and run it before committing (it reads the old seed from the
   release `HEAD` records, so run it before the commit, or pass `--base`).
6. Apply the steps, run `just check` and `nix flake check` (`nix flake check path:nix/workspace` for a
   [flake in a subdirectory](#a-workspace-whose-content-must-not-enter-the-nix-store)), then commit the moved
   scions, `flake.lock`, and the workspace changes together.

Don't commit edits inside `.scions/`: `just check` fails while a scion has uncommitted edits or sits off a
release tag. A fix to the kit goes to the kit's repository, then a release, then step 2.

## Contribute back

A convention that proves useful in one workspace and is free of local context belongs in the kit. Change the kit
first, tag it, then upgrade each workspace. Keep workspace-specific context, data, and boundaries out of the kit.
While the kit is `0.x`, any release may change seeded files, so every release carries an **Upgrading** section.

## Sources

- [graft: a flake in a subdirectory](https://github.com/danielnaab/graft/blob/v2.13.0/docs/guides/flake-in-a-subdirectory.md)
- [graft README](https://github.com/danielnaab/graft/blob/v2.13.0/README.md)
- [knowledge-base-kit dependency playbook](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/playbooks/manage-kb-dependencies.md)
- [Seed files](../seed/common/)
- [just manual: imports, settings, and attributes](https://just.systems/man/en/)
