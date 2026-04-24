---
name: project-sync
description: Centralized GitHub Project mapping and status synchronization for OpenSpec and PR workflows.
license: MIT
compatibility: Requires gh CLI auth and project access.
metadata:
  author: adrotech
  version: "2.0"
---

Use this skill to run repository-backed GitHub Project sync.

## Inputs

- `changeName`
- `projectItemId` (optional)
- `status` (`Backlog|Ready|In progress|In review|Done`)
- `priority` (`P0|P1|P2`, optional)
- `size` (`XS|S|M|L|XL`, optional)

## Config placeholders

- `GITHUB_OWNER=adrotech`
- `PROJECT_NUMBER=2`
- `PROJECT_ID=PVT_kwHOCZrNic4BUhiB`
- `STATUS_FIELD_ID=PVTSSF_lAHOCZrNic4BUhiBzhBpEIQ`
- `PRIORITY_FIELD_ID=PVTSSF_lAHOCZrNic4BUhiBzhBpEQ0`
- `SIZE_FIELD_ID=PVTSSF_lAHOCZrNic4BUhiBzhBpEQ4`
- `PROJECT_TAG=adrotech`

## Behavior

- Execute `python3 .opencode/skills/project-sync/project_sync.py` with requested arguments.
- Keep managed draft title/body in Spanish.
- Always include project tag `adrotech` in generated title/body.
- Preserve technical identifiers, filenames, status values, and CLI flags.
- If mapping is missing, create draft item and persist `project_item_id` unless disabled.
- If remote step fails, return `sync_pending` and exact recovery command.

## States

- `ok`: sync completed.
- `blocked`: missing auth/access/context.
- `sync_pending`: remote sync failed partially or fully.
