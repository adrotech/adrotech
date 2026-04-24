#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Renderiza y valida el comentario obligatorio de issue para cierre de tarea de spec."
        )
    )
    parser.add_argument("--summary", required=True, help="Resumen breve del avance/entrega.")
    parser.add_argument("--commit-sha", required=True, help="SHA corto o completo del commit.")
    parser.add_argument("--repo", required=True, help="Repositorio en formato owner/repo.")
    parser.add_argument("--continuity", required=True, help="Siguiente paso de continuidad.")
    parser.add_argument(
        "--trace-commit",
        help="Marcador parseable TRACE-COMMIT para deduplicación (opcional).",
    )
    parser.add_argument(
        "--trace-task",
        help="Marcador parseable TRACE-TASK para deduplicación (opcional).",
    )
    parser.add_argument(
        "--output",
        help="Ruta de salida para guardar el markdown. Si se omite, imprime por stdout.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Solo valida campos (no imprime ni escribe markdown).",
    )
    return parser.parse_args(argv)


def is_blank(value: str) -> bool:
    return not value or not value.strip()


def normalize_list_items(value: str) -> list[str]:
    items: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if line:
            items.append(line)

    if items:
        return items

    compact = " ".join(value.split())
    return [compact] if compact else []


def validate(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []

    if is_blank(args.summary):
        errors.append("summary es obligatorio")
    if is_blank(args.continuity):
        errors.append("continuity es obligatorio")

    repo = args.repo.strip()
    if "/" not in repo or repo.startswith("/") or repo.endswith("/"):
        errors.append("repo debe tener formato owner/repo")

    commit_sha = args.commit_sha.strip()
    if not SHA_PATTERN.match(commit_sha):
        errors.append("commit-sha debe ser hexadecimal de 7 a 40 caracteres")

    if args.trace_commit and not SHA_PATTERN.match(args.trace_commit.strip()):
        errors.append("trace-commit debe ser hexadecimal de 7 a 40 caracteres")
    if args.trace_task and is_blank(args.trace_task):
        errors.append("trace-task no puede estar vacío")

    return errors


def render_markdown(
    summary: str,
    commit_sha: str,
    repo: str,
    continuity: str,
    trace_commit: str | None,
    trace_task: str | None,
) -> str:
    commit_link = f"https://github.com/{repo}/commit/{commit_sha}"
    summary_items = normalize_list_items(summary)
    summary_block = "\n".join(f"- {item}" for item in summary_items)
    continuity_clean = " ".join(continuity.strip().split())

    trace_block = ""
    if trace_commit:
        trace_block += f"TRACE-COMMIT: {trace_commit.strip()}\n"
    if trace_task:
        trace_block += f"TRACE-TASK: {trace_task.strip()}\n"
    if trace_block:
        trace_block = f"{trace_block}\n"

    return (
        "## Avance de tarea de spec\n\n"
        f"{trace_block}"
        "### Resumen\n"
        f"{summary_block}\n\n"
        "### Commit\n"
        f"- Commit ID: `{commit_sha.strip()}`\n"
        f"- Link: {commit_link}\n\n"
        "### Continuidad\n"
        f"- Siguiente paso: {continuity_clean}\n"
    )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors = validate(args)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("OK: campos obligatorios validados")
        return 0

    markdown = render_markdown(
        args.summary,
        args.commit_sha,
        args.repo,
        args.continuity,
        args.trace_commit,
        args.trace_task,
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"OK: comentario renderizado en {output_path}")
        return 0

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
