# PR Evidence Template (ES)

Usar este template para `mode=pr`.

## Resumen
- [adrotech] <1-3 puntos del cambio principal>

## Cambios
- <que se cambio>
- <por que se cambio>

## Validaciones Tecnicas
- `npm run lint`: <PASS/FAIL + evidencia corta>
- `npm run test`: <PASS/FAIL + evidencia corta>
- `npm run build`: <PASS/FAIL + evidencia corta>
- `npm run check`: <PASS/FAIL + evidencia corta>

## Evidencia Funcional
- Contexto: <ruta/flujo afectado>
- Flujo 1: <pasos de validacion>
- Resultado 1: <estado visual o salida>
- Flujo 2 (si aplica): <pasos>
- Resultado 2 (si aplica): <estado visual o salida>
- Interpretacion: <esperado vs real>

## Diagrama (ASCII)
```text
Usuario
  |
  v
Pagina/Ruta
  |
  v
Componente/Layout
  |
  v
Resultado visual/estado
```

## Riesgos y Mitigaciones
- Riesgo: <riesgo principal>
  - Mitigacion: <accion concreta>

## Estado de Evidencias Pendientes
- <si no hay pendientes, escribir "Sin pendientes">
