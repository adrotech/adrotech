# Template de Tutorial

Usá esta base para escribir tutoriales paso a paso y después pasalos a `src/content/tutoriales/<slug>.md`.

## Frontmatter

```yaml
---
title: "Tutorial: título claro y concreto"
description: "Qué va a lograr la persona al terminar este tutorial."
date: 2026-04-23
tags: ["tag 1", "tag 2", "tag 3"]
category: "tutorial"
level: "intermedio"
featured: false
# heroImage: "./cover.png"
---
```

## Estructura sugerida

```md
Introducción breve.
Explicá qué problema resuelve el tutorial y para quién está pensado.

## Qué vas a construir

- Resultado 1
- Resultado 2
- Resultado 3

## Qué necesitás antes de empezar

- Requisito 1
- Requisito 2
- Requisito 3

## Paso 1. Preparar la base

Explicación breve.

```bash
# comando o snippet
```

## Paso 2. Implementar

Explicación breve.

```ts
// ejemplo de código
```

## Paso 3. Verificar

Mostrá cómo comprobar que todo funciona.

## Errores comunes

- Error frecuente 1
- Error frecuente 2

## Cierre

Resumen corto de lo logrado y siguiente paso natural.
```

## Guía de estilo

- El tutorial tiene que ser accionable, no teórico.
- Cada paso debe tener un objetivo claro.
- Evitá bloques enormes de texto entre pasos.
- Si agregás código, explicá por qué importa.
- Cerrá con una validación o resultado observable.

## Checklist antes de publicar

- ¿Se entiende qué se construye?
- ¿Los prerequisitos están claros?
- ¿Los pasos tienen orden lógico?
- ¿Hay comandos o snippets útiles?
- ¿Incluiste cómo validar el resultado?
- ¿La ortografía está cuidada?

## Convención de slugs

- Usar minúsculas.
- Separar palabras con guiones.
- Evitar tildes y caracteres especiales.

Ejemplo:

`pipeline-content-frontend.md`
