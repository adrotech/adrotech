# adrotech

Sitio personal de Adrian Rojas para compartir cursos gratuitos, tutoriales aplicados y posts de reflexion sobre tecnologia, producto e IA.

## Stack

- Astro + MDX
- npm
- Despliegue en Vercel

## Estructura

```text
src/
  content/
    cursos/
    tutoriales/
    posts/
  pages/
    index.astro
    cursos/
    tutoriales/
    posts/
    sobre-mi.astro
```

## Scripts

- `npm run dev` - entorno local
- `npm run lint` - chequeos Astro
- `npm run test` - chequeos Astro (placeholder)
- `npm run build` - build de produccion
- `npm run check` - chequeos Astro

## Deploy en Vercel

### Setup inicial

1. Crear repo en GitHub con nombre `adrotech`.
2. Importar el repo en Vercel (`Add New -> Project -> Import Git Repository`).
3. Framework preset: `Astro`.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Variable de entorno recomendada:
   - `SITE_URL=https://<tu-dominio-o-subdominio>`

### Checklist de publicacion

- [ ] `npm run lint`
- [ ] `npm run test`
- [ ] `npm run build`
- [ ] `npm run check`
- [ ] Revisar rutas clave (`/`, `/cursos`, `/tutoriales`, `/posts`, `/sobre-mi`)
- [ ] Validar metadata y sitemap (`/sitemap-index.xml`, `/rss.xml`)
- [ ] Confirmar dominio final en `SITE_URL`

## Operacion OpenSpec/OpenCode

- Board objetivo: `https://github.com/users/adrotech/projects/2`
- Tag operativo obligatorio: `adrotech`
- Config en `.opencode` ya adaptada a frontend.
