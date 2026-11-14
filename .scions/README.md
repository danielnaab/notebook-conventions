<!-- managed by graft: https://github.com/danielnaab/graft -->
# Scions

Each folder here is a git submodule: another repository, grafted at a release tag. Empty folders?
Run `git submodule update --init --recursive` (or `nix run .#graft sync`).

- Read them freely. Ask before you edit one: a fix belongs in the provider. See graft's "Fix a provider from
  a consumer" guide: edit on a branch, test, build with it (`nix run .#graft -- try NAME`, then `nix run .#graft -- try --stop`),
  push to the provider, release, then `nix run .#graft upgrade NAME`.
- `nix run .#graft check` fails until every scion is clean and at a release tag, and while try is on.
- Versions: `nix run .#graft outdated`.
