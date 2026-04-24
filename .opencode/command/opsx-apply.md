---
description: Implement tasks from an OpenSpec change.
---

Run unified OpenSpec workflow in `apply` mode.

## Command behavior

- Select target change from argument or active change list.
- Invoke `openspec-workflow` with mode `apply`.
- Continue implementation until all tasks are done or blocked.
- Keep task checkboxes synchronized.
- Keep human-facing text in Spanish and include project tag `adrotech` in task titles/summaries.
- If board tracking is enabled, run:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status "In progress"
  ```

## Recommended execution

1. `openspec-workflow` (`mode=apply`)
2. `python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status "In progress"`
