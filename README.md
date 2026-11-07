# notebook-conventions

Conventions, tools, agent skills, and a starter seed for Markdown work-memory workspaces: a Git repository of
notes that people browse in Obsidian and agents maintain. The notes folder is the Obsidian vault and an
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) v0.2 bundle. It extracts what proved useful in practice and is
meant to be shared by several workspaces that evolve together.

A workspace pins this repository as a [graft](https://github.com/danielnaab/graft) scion, reads most of it in
place, and copies a small `seed/` once.

## What is here

| Path | Purpose |
| --- | --- |
| [docs/](docs/README.md) | The conventions: layout, workflow, tasks, conformance, Obsidian, adoption. |
| [templates/](templates/) | Canonical daily, session, wiki, and task-record note templates. |
| [skills/](skills/) | Generic agent skills `notebook-start` and `notebook-wrap`. |
| [tools/](tools/) | `check-tasks`, `check-kb`, `check-templates`, `index`, `move`, `convert`, and a pre-commit hook. |
| [nix/workspace.nix](nix/workspace.nix) | Flake wiring: dev shell, check apps, task check. |
| [seed/](seed/common/) | Files a workspace copies once and then owns. |
| [LICENSE](LICENSE) | CC0 1.0 Universal. |
| [tests/](tests/) | Tool tests and a test that builds a workspace from the seed and runs every check. |

## Use it

See the [adoption guide](docs/adoption.md): copy the seed, fill the placeholders, write the boundaries, graft the
kit, and check. Upgrade with `nix run .#graft upgrade`, read the changelog's **Upgrading** steps, and let
`nix run .#graft migrate` brief an agent.

## Principles

- **Generic and public.** No context from any one workspace. Boundaries (data, accounts, services) belong to each
  workspace and are never defined here.
- **Reference over copy.** What a workspace can read in place stays in the scion, so fixes arrive with an upgrade.
- **Small seed.** Seeded files are owned by the workspace; changes reach them through the changelog, not a merge tool.
- **Evidence-driven.** Structure is added for observed, repeated pain, following the
  [meta-KB](https://github.com/danielnaab/meta-knowledge-base/tree/v1.1.0).

## Develop

```sh
nix flake check          # tests, including a workspace built from seed/ and the hygiene scan
nix run .#check-kb       # links, status, and Sources in this repository
```

Requires Nix with flakes. See [AGENTS.md](AGENTS.md) for the rules for changing this repository.

## License

[CC0 1.0 Universal](LICENSE): public-domain dedication; use, copy, and adapt freely, with no attribution required.
The license file is exported with the scion, so every workspace that pins the kit carries it.

## Sources

- [Graft](https://github.com/danielnaab/graft)
- [meta-knowledge-base](https://github.com/danielnaab/meta-knowledge-base)
- [knowledge-base-integrity](https://github.com/danielnaab/knowledge-base-integrity)
