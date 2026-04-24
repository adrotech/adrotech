# Project Sync

`project_sync.py` is the executable implementation behind the `project-sync` skill.

## What it does

- Reads change metadata from `openspec/changes/<change>/.openspec.yaml`.
- Discovers OpenSpec artifacts for each change.
- Generates a managed draft-item body in Spanish.
- Syncs GitHub Project draft items and single-select fields (status, priority, size).
- Injects project tag `adrotech` in generated draft title/body.

## Usage

```bash
python3 .opencode/skills/project-sync/project_sync.py --change <changeName> --status Ready
python3 .opencode/skills/project-sync/project_sync.py --backfill --dry-run
```

## Notes

- Requires authenticated `gh` CLI with access to `users/adrotech/projects/2`.
- Defaults can be overridden with environment variables.
- If change has no `project_item_id`, script creates a draft item and persists mapping.
- Remote failures are reported as `sync_pending` with a recovery command.
