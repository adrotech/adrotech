# Git Delivery Toolkit

Directorio para estandarizar entrega en repos frontend:

- mensaje de commit,
- comentario obligatorio en issue,
- pasos operativos manuales o coordinados por `delivery`.

## Regla de autorizacion Git/GH

- Si el usuario da instruccion explicita de entrega, `delivery` ejecuta `git status/diff/log/add/commit/push` y `gh` sin prompts intermedios.
- Si no existe esa instruccion, devolver estado `blocked` indicando exactamente que falta.

## Gates tecnicos

- `npm run lint`
- `npm run test`
- `npm run build`
- `npm run check`

## Politica de tag

- Todo artefacto de entrega debe incluir tag `adrotech`.

## Artefactos

- `SKILL.md`: contrato operativo del skill `git-delivery`.
- `templates/commit-message-template.md`: estructura base para commit message.
- `templates/commit-evidence-template.md`: reporte de evidencia de commit.
- `templates/pr-evidence-template.md`: reporte de evidencia de PR.
- `templates/pr-change-completion-template.md`: template para PR de change 100% completado.
- `templates/issue-comment-template.md`: comentario estandar de issue (spec).
- `render_issue_comment.py`: helper para validar/renderizar comentario.
- `render_pr_body.py`: helper para validar/renderizar body de PR.
- `traceability_gate.py`: gate de trazabilidad por commit y task.
