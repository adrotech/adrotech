# AGENTS.md

Operational guide for coding agents working in this repository.

## Project Snapshot

- **Stack**: Astro 6.1.9, TypeScript 5.9.3
- **Routing**: Astro file-based routing in src/pages/
- **Testing**: Astro check (type validation)
- **Spec workflow**: OpenSpec change artifacts in `openspec/`

## Source Layout

- `src/pages/`: route files and page implementations
- `src/components/`: reusable UI components
- `src/layouts/`: Astro layouts
- `public/`: static assets

## Required Commands

Run from repository root.

### Install

```bash
npm install
```

### Development

```bash
npm run dev
```

### Validation

```bash
npm run lint
npm run check
```

## Architecture Rules

1. Use Astro component patterns
2. Keep layouts minimal and composable
3. Prefer static generation where possible
4. Use content collections for markdown content

## Testing Expectations

- Run type checking before finalizing
- Verify build succeeds

## OpenSpec Workflow

Use `opsx-explore`, `opsx-propose`, `opsx-apply`, `opsx-verify`, `opsx-archive` for spec-driven development.

## Agent Behavior Guidelines

- Make focused, minimal changes
- Do not revert unrelated local modifications
- Run relevant validation before finalizing
- When asked to commit/push, follow repository branch standards
- When task depends on repository-local tooling, inspect relevant SKILL.md files before acting