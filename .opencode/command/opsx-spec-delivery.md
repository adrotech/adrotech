---
description: Standardize OpenSpec task closure (commit/push/project/comment).
---

Reusable operational guide for complete closure of one spec task.

## Objective

Apply one traceable flow across:

1. commit,
2. push,
3. PR when needed,
4. OpenSpec update,
5. GitHub Project update,
6. required issue comment.

## Templates and helper

- Commit message: `/.opencode/skills/git-delivery/templates/commit-message-template.md`
- Issue comment: `/.opencode/skills/git-delivery/templates/issue-comment-template.md`
- Render helper: `python3 .opencode/skills/git-delivery/render_issue_comment.py`

## Tag policy

- Include `adrotech` in closure summaries/comments.

## Execution from `delivery`

- With explicit user authorization, `delivery` runs Git/GH commands without intermediate prompts.
- If authorization is missing, return `blocked` with exact instruction.
- Use `git-delivery` for `mode=commit`, `mode=push`, and `mode=pr` when needed.
- Use `project-sync` for board updates.
