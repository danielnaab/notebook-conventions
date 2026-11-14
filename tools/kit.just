# notebook-kit operations menu. A workspace's justfile imports it in place (see seed/common/justfile,
# whose first recipe, `default`, lists this menu: just runs the root justfile's first recipe, never an imported one):
#
#   set allow-duplicate-variables   # lets the workspace override kit_run and graft_run below
#   set allow-duplicate-recipes     # lets the workspace define check-local (and override any recipe)
#   import? ".scions/notebook-kit/tools/kit.just"
#
# `import?` (optional): a fresh clone whose scions are not filled yet (git submodule update --init) still lists the
# workspace's own recipes. A flake in a subdirectory imports from its scions directory, e.g.
# "nix/agent-tools/.scions/notebook-kit/tools/kit.just".
# `just` lists every recipe by group. Recipes run from the workspace root, so paths are repository-relative,
# and flags pass straight through: `just index --check`, `just move OLD NEW --dry-run`.
# Docs: .scions/notebook-kit/docs/adoption.md#run-operations-with-just

# How a kit tool runs: `{}` becomes the tool's name (check-kb, nb-index, ...), and the recipe's arguments follow.
# Override with the KIT_RUN environment variable or `kit_run := "..."` in the workspace justfile, e.g.
# "{}" (tools on PATH), ".local/tools/bin/{}", or "nix run path:nix/tools#{} --".
kit_run := env("KIT_RUN", "nix run .#{} --")

# How graft runs; its subcommand and arguments follow. Override with GRAFT_RUN or `graft_run := "..."`.
graft_run := env("GRAFT_RUN", "nix run .#graft --")

# Run every kit check, then the workspace's check-local
[group('check')]
check: graft-check check-kb check-tasks (index "--check") check-obsidian check-local
    @echo "check: all checks passed"

# A workspace defines check-local (with `set allow-duplicate-recipes`) to add its own checks to `check`
[private]
check-local:

# Check that every scion is clean and at a release tag, and graft's workflows are current
[group('check')]
[positional-arguments]
graft-check *args:
    {{graft_run}} check "$@"

# Check links, lifecycle status, and Sources with knowledge-base-kit's checker
[group('check')]
[positional-arguments]
check-kb *args:
    {{replace(kit_run, "{}", "check-kb")}} "$@"

# Validate current task records and their index
[group('check')]
[positional-arguments]
check-tasks *args:
    {{replace(kit_run, "{}", "check-tasks")}} "$@"

# Report how note templates differ from the kit's canonical copies (--strict: fail on drift)
[group('check')]
[positional-arguments]
check-templates *args:
    {{replace(kit_run, "{}", "check-templates")}} "$@"

# Report how the vault's shared Obsidian settings differ from the kit's (--strict: fail on drift)
[group('check')]
[positional-arguments]
check-obsidian *args:
    {{replace(kit_run, "{}", "check-obsidian")}} "$@"

# Regenerate the vault's index.md listings from note frontmatter (--check: report stale ones)
[group('notes')]
[positional-arguments]
index *args:
    {{replace(kit_run, "{}", "nb-index")}} "$@"

# Move a note or folder and rewrite the links to and from it (paths from the repository root; --dry-run)
[group('notes')]
[positional-arguments]
move old new *flags:
    {{replace(kit_run, "{}", "nb-move")}} "$@"

# Show the pinned and newest tag of each scion
[group('deps')]
[positional-arguments]
outdated *args:
    {{graft_run}} outdated "$@"

# Show scion changelogs between the pinned and newest tags (all scions, or the ones named)
[group('deps')]
[positional-arguments]
changelog *names:
    {{graft_run}} changelog "$@"

# Move scions to newer release tags (e.g. notebook-kit@vX.Y.Z), apply the kit's Obsidian settings and plugins
# (upgrade-obsidian), then list the next steps
[group('deps')]
[positional-arguments]
upgrade *targets:
    {{graft_run}} upgrade "$@"
    @echo
    @# A fresh just, so tools that resolve kit_run once (a built tools path) use the new pin.
    @{{just_executable()}} --justfile {{quote(justfile())}} upgrade-obsidian \
        || echo "upgrade-obsidian did not run: quit Obsidian, then run just upgrade-obsidian before committing"
    @echo
    @echo "Next steps:"
    @echo "  1. Read each upgraded scion's CHANGELOG.md, its Upgrading sections in particular: just changelog"
    @echo "  2. Brief an agent or yourself on what moved:                                       just migrate"
    @echo "  3. Apply the Upgrading steps, then verify:                                          just check"
    @echo "  4. Commit the moved scions, flake.nix and flake.lock (graft's pin), and the workspace changes together."

# Print a migration brief for an upgrade: what moved, the changelog text, the provider's changes
[group('deps')]
[positional-arguments]
migrate *args:
    {{graft_run}} migrate "$@"

# Fill empty scions (git submodule update --init), and write graft's scions README and workflows
[group('deps')]
[positional-arguments]
sync *args:
    {{graft_run}} "$@"

# Merge the kit's Obsidian settings into the vault, keeping local changes, and install its pinned plugins
# (quit Obsidian first; --dry-run, --no-plugins)
[group('migrations')]
[positional-arguments]
upgrade-obsidian *args:
    {{replace(kit_run, "{}", "upgrade-obsidian")}} "$@"

# Convert a v0.1 workspace to the v0.2 vault layout (--dry-run)
[group('migrations')]
[positional-arguments]
convert *args:
    {{replace(kit_run, "{}", "nb-convert")}} "$@"
