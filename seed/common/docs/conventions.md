---
status: working
---

# Local conventions

This workspace follows the pinned [notebook-conventions](../.scions/notebook-conventions/docs/README.md) kit and
the [meta-KB](../.scions/meta-knowledge-base/README.md). This file states only local rules and differences.
Local rules take precedence. [Boundaries](boundaries.md) are separate and override everything.

## Local rules

_None yet. Add a rule here only when the kit's default does not fit, with the reason._

## Meta-KB conformance

The seven core policies bind. Application is the kit's default
([conformance](../.scions/notebook-conventions/docs/conformance.md#default-application)) except as listed.

- **Deliberate deviations:** the kit's three (task status vocabulary, no status on dated notes, `YYYY-MM` folders).
  Add local deviations here with a reason.
- **Added locally:** [boundaries](boundaries.md) and anything under Local rules.
- **Verification:** `nix run .#check-kb`, `nix run .#check-tasks`; the pre-commit hook runs the first.
  Write boundaries and `askFirst` approvals are checked by hand.
- **Ask-first changes** need <<OWNER>>'s approval for the specific change, recorded in the task, session, daily
  note, or commit message.

## Sources

- [Kit conformance guide](../.scions/notebook-conventions/docs/conformance.md)
- [KB configuration](../knowledge-base.yaml)
