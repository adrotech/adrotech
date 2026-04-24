---
description: Generate standardized PR for completed OpenSpec change.
---

Use this command when an OpenSpec change is 100% complete (no pending tasks).

## Objective

Standardize closure with `delivery` and create one review-ready PR.

## Preflight

1. Confirm `openspec/changes/<change>/tasks.md` has no pending items.
2. Confirm no duplicate open PR exists for the same change.

## Recommended execution

1. Render PR body (optional):

   ```bash
   python3 .opencode/skills/git-delivery/render_pr_body.py \
     --change-name <changeName> \
     --summary "<resumen ejecutivo>" \
     --scope "<alcance del change>" \
     --validation "<evidencia de validacion>" \
     --risks "<riesgos>" \
     --rollback-impact "<rollback/impacto>" \
     --pending-tasks-count 0 \
     --output /tmp/change-pr-body.md
   ```

2. Create PR with `delivery` (`git-delivery`, `mode=pr`).
3. Sync project item to `In review`:

   ```bash
   python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status "In review"
   ```

## Tag policy

- Include `adrotech` in PR title/body/checklists.
