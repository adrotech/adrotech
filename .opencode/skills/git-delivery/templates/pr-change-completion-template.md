# PR Template - Change Completado (ES)

Usar este template cuando un change OpenSpec este 100% aplicado.

## Resumen ejecutivo
- [adrotech] <resultado principal del change>
- <contexto tecnico/negocio en 1-2 lineas>

## Alcance
- Incluye:
  - <ambito incluido 1>
  - <ambito incluido 2>
- No incluye (si aplica):
  - <ambito fuera de alcance>

## Evidencia de validacion

### Validaciones tecnicas
- `npm run lint`: <PASS/FAIL + evidencia>
- `npm run test`: <PASS/FAIL + evidencia>
- `npm run build`: <PASS/FAIL + evidencia>
- `npm run check`: <PASS/FAIL + evidencia>

### Evidencia funcional
- Contexto: <ruta/flujo afectado>
- Pasos: `<secuencia de validacion>`
- Resultado: `<estado visual/salida resumida>`
- Interpretacion: <esperado vs real>

## Riesgos
- Riesgo: <riesgo operativo/tecnico>
  - Mitigacion: <accion concreta>

## Rollback / Impacto
- Rollback: <como revertir>
- Impacto operativo esperado: <alto/medio/bajo + detalle>

## Checklist
- [ ] Change con tasks al 100% (sin pendientes).
- [ ] Validaciones tecnicas ejecutadas con evidencia.
- [ ] Evidencia funcional documentada o justificada como "No aplica".
- [ ] Riesgos y rollback documentados.
- [ ] Tag `adrotech` incluido en artefactos de entrega.

## Diagrama (ASCII)
```text
Usuario -> Ruta -> Componente -> Estado/UI
```
