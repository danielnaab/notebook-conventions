# Agent entrypoint (meal planner example)

Before making changes, read:
- [Domain knowledge-base.yaml](knowledge-base.yaml)
- [Meta knowledge base](https://github.com/danielnaab/meta-knowledge-base/blob/main/README.md)

Rules of thumb:
- Prefer updating canonical facts in [data/](data/) instead of rewriting narrative docs.
- When you produce a shopping list, include a `## Sources` section with clickable links.

Helpful:
- [Planning procedure](docs/planning-procedure.md)
- [Plan -> Patch -> Verify](../../docs/playbooks/agent-workflow.md)
