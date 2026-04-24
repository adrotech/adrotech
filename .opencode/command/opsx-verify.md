---
description: Verify OpenSpec implementation before archive.
---

Run unified OpenSpec workflow in `verify` mode.

## Command behavior

- Select target change.
- Invoke `openspec-workflow` with mode `verify`.
- Produce completeness, correctness, and coherence findings.
- Write findings in Spanish and include tag `adrotech`.
- If board tracking is enabled, run:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName>
  ```

## Recommended execution

1. `openspec-workflow` (`mode=verify`)
2. `python3 .opencode/skills/project-sync/project_sync.py --change <changeName>`
