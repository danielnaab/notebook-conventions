# <<WORKSPACE_NAME>>

<<ONE_LINE_DESCRIPTION>> Agents are the primary writing interface; Obsidian is a local navigation and editing view
over the same Markdown. Open `notebook/` as the vault: it is also an
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle.

## Currently working on

_Nothing yet._

## Navigate

| Area | Purpose |
| --- | --- |
| [Notebook](notebook/index.md) | The vault: `raw/` sources, `records/` (daily notes, sessions), `tasks/`, `wiki/`. |
| [Tasks](notebook/tasks/index.md) | Current work queue with stable records, next actions, and blockers. |
| [Templates](notebook/templates/README.md) | Shared note structures for Obsidian and agents. |
| [Agent instructions](AGENTS.md) | Boundaries, workflow routing, and write rules. |
| [Boundaries](docs/boundaries.md) | What data, accounts, tools, and services this workspace may use. |
| [Local conventions](docs/conventions.md) | Local rules and knowledge-base-kit conformance, extending the pinned kit. |
| [KB configuration](knowledge-base.yaml) | Layer and authority declarations and check scopes. |

The shared conventions live in [notebook-kit](.scions/notebook-kit/docs/README.md), a pinned graft
dependency. Daily → session → wiki is the browsing path, but a session is not mandatory for every interaction.
Folder `index.md` files are generated: `just index`. Run `just` to list every operation.
