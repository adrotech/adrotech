---
description: Create a new OpenSpec change and generate proposal artifacts.
---

Run unified OpenSpec workflow in `propose` mode.

## Command behavior

- Resolve change name from command argument or user request.
- Invoke `openspec-workflow` with mode `propose`.
- Ensure proposal/design/tasks/spec updates are implementation-ready.
- Write human-facing text in Spanish.
- Include project tag `adrotech` in generated task/change titles and summaries.
- If board tracking is enabled, run:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status Ready
  ```

## Recommended execution

1. `openspec-workflow` (`mode=propose`)
2. `python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status Ready`
