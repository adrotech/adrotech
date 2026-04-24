---
name: git-delivery
description: Unified git delivery workflow for commit, push, and PR creation on frontend projects.
license: MIT
compatibility: Requires git CLI, gh CLI, and npm scripts.
metadata:
  author: adrotech
  version: "2.0"
---

Use this skill for all delivery operations.

## Modes

- `commit`: create focused commit on safe branch.
- `push`: push current branch safely.
- `pr`: create PR with validation gates.

## Common rules

- Protected branches: `develop`, `main`, `master`.
- PR base branch: `main` (unless user explicitly requests another one).
- Never force push unless explicitly requested.
- Never claim validation without evidence.
- Always respond in Spanish.
- If user explicitly authorizes delivery, execute `git status/diff/log/add/commit/push` and `gh` without intermediate prompts.
- If explicit authorization is missing, return `blocked` with exact instruction.
- Always include project tag `adrotech` in delivery summaries and PR body.

## Evidence policy

- Every commit/PR must include explicit evidence of executed commands and key outputs.
- For frontend behavior changes, include local functional evidence (route, flow, expected vs actual).
- If runtime validation cannot run, report pending with exact command.

## PR evidence package

- `Resumen ejecutivo`
- `Alcance`
- `Cambios`
- `Validaciones tecnicas`
- `Evidencia funcional`
- `Diagrama`
- `Riesgos y mitigaciones`
- `Rollback/impacto`
- `Checklist`

## Templates

- PR template: `templates/pr-evidence-template.md`
- PR template (change completado): `templates/pr-change-completion-template.md`
- Commit report template: `templates/commit-evidence-template.md`
- Commit message template: `templates/commit-message-template.md`
- Issue comment template: `templates/issue-comment-template.md`

## PR validation gates

- `npm run lint`
- `npm run test`
- `npm run build`
- `npm run check`

## Output

- Branch used
- Actions executed
- Validation results
- Functional evidence collected
- ASCII diagram (unless exception applies)
- PR URL (if created)
- Blockers and recovery commands (if any)
