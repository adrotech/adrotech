# Issue Comment Template (ES)

Usar este template para el comentario obligatorio de cierre/avance de tarea de spec.

```md
## Avance de tarea de spec

TRACE-COMMIT: <sha-corto-o-completo>
TRACE-TASK: <change>#<task-id>

### Resumen
- Proyecto: adrotech
- <resumen-item-1>
- <resumen-item-2>

### Commit
- Commit ID: `<sha-corto>`
- Link: https://github.com/<owner>/<repo>/commit/<sha>

### Continuidad
- Siguiente paso: <qué sigue>
```

## Campos obligatorios

- `TRACE-COMMIT` (cuando el comentario esté asociado a commit)
- `TRACE-TASK` (cuando el comentario esté asociado a task)
- `Resumen`
- `Commit ID`
- `Link` al commit
- `Continuidad`

Si falta uno de estos campos, la tarea no cumple la politica de cierre.
