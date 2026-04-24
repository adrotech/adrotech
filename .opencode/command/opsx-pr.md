---
description: Create a frontend PR with npm validation gates and project sync.
---

Use unified delivery skill for PR generation and creation.

## Command behavior

- Invoke `git-delivery` in `pr` mode.
- With explicit delivery authorization, `delivery` can run Git/GH commands directly.
- If authorization is missing, return `blocked` with required command/instruction.
- Enforce source branch policy (`develop`, `main`, `master` blocked as PR source).
- Use base branch `main` by default.
- Require Spanish output in PR body/comment.
- Require project tag `adrotech` in PR title/body.
- Require validation gates:
  - `npm run lint`
  - `npm run test`
  - `npm run build`
  - `npm run check`
- Require frontend functional evidence (route/flow proof) for behavior changes.
- Include ASCII diagram unless docs-only or no behavior flow exists.
- Build PR evidence from `/.opencode/skills/git-delivery/templates/pr-evidence-template.md`.
- If project board tracking is enabled, run:

  ```bash
  python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status "In review"
  ```

## Recommended execution

1. `git-delivery` (`mode=pr`)
2. `python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status "In review"`
