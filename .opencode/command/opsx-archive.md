---
description: Archive an OpenSpec change after verification.
---

Run unified OpenSpec workflow in `archive` mode.

## Command behavior

- Select target change.
- Warn on incomplete artifacts/tasks and request confirmation.
- Archive change directory using dated folder convention.
- Preserve Spanish text and include tag `adrotech` in archive notes/sync text.
- If board tracking is enabled, run:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status Done
  ```

## Recommended execution

1. `openspec-workflow` (`mode=archive`)
2. `python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status Done`
