---
name: openspec-workflow
description: Unified OpenSpec lifecycle workflow for explore, propose, apply, verify, and archive.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: adrotech
  version: "2.0"
---

Use this skill for all OpenSpec stages.

## Modes

- `explore`: analyze problem space and options, no implementation.
- `propose`: create change and artifacts until apply-ready.
- `apply`: implement pending tasks and update checkboxes.
- `verify`: check implementation completeness/correctness/coherence.
- `archive`: archive completed change with warnings when needed.

## Stage rules

- Determine active change from input or `openspec list --json`.
- Read context files reported by `openspec instructions`.
- Keep progress explicit (`N/M tasks complete`).
- Default all human-facing OpenSpec artifact content to Spanish.
- Preserve technical identifiers, filenames, change slugs, code symbols, and CLI flags.
- For `apply`, implement until done or blocked.
- For `apply`, follow frontend baseline: semantic HTML, accessibility, responsive behavior, SEO, and low JS overhead.
- For `apply`, close tasks with delivery traceability: commit + push + OpenSpec update + project sync + issue comment.
- For `propose`/`apply`/`verify`/`archive`, include project tag `adrotech` in generated titles and summaries.

## Integration rules

- Use `project-sync` when lifecycle step requires board status update or artifact snapshot refresh.
- Entry point:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName> [--status ...]
  ```

- If project mapping is missing, create/link the item through `project_sync.py` or return `sync_pending` with exact recovery command.
- If explicit delivery authorization or required capability is missing, return `blocked` with exact recovery instruction.
