#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Renderiza y valida el body de PR estandarizado para change completado."
        )
    )
    parser.add_argument("--change-name", required=True, help="Nombre técnico del change.")
    parser.add_argument("--summary", required=True, help="Resumen ejecutivo.")
    parser.add_argument("--scope", required=True, help="Alcance del change.")
    parser.add_argument(
        "--validation", required=True, help="Evidencia consolidada de validaciones."
    )
    parser.add_argument("--risks", required=True, help="Riesgos y mitigaciones.")
    parser.add_argument(
        "--rollback-impact", required=True, help="Plan de rollback e impacto operativo."
    )
    parser.add_argument(
        "--functional-evidence",
        default="No aplica",
        help="Evidencia funcional (flujo UI/ruta) o 'No aplica'.",
    )
    parser.add_argument(
        "--diagram",
        default=(
            "Cliente\n"
            "  |\n"
            "  | Navega a <ruta>\n"
            "  v\n"
            "Pagina/Layout\n"
            "  |\n"
            "  v\n"
            "Componente\n"
            "  |\n"
            "  v\n"
            "Estado/UI"
        ),
        help="Diagrama ASCII del flujo (usar 'No aplica' si corresponde).",
    )
    parser.add_argument(
        "--pending-tasks-count",
        type=int,
        default=0,
        help="Cantidad de tasks pendientes del change (debe ser 0 para cierre).",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Solo valida campos obligatorios y gates.",
    )
    parser.add_argument(
        "--output",
        help="Ruta de salida para guardar markdown. Si se omite, imprime por stdout.",
    )
    return parser.parse_args(argv)


def is_blank(value: str) -> bool:
    return not value or not value.strip()


def validate(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []

    required = {
        "change-name": args.change_name,
        "summary": args.summary,
        "scope": args.scope,
        "validation": args.validation,
        "risks": args.risks,
        "rollback-impact": args.rollback_impact,
    }

    for key, value in required.items():
        if is_blank(value):
            errors.append(f"{key} es obligatorio")

    if args.pending_tasks_count < 0:
        errors.append("pending-tasks-count no puede ser negativo")
    if args.pending_tasks_count != 0:
        errors.append(
            "pending-tasks-count debe ser 0 para PR de change completado"
        )

    return errors


def render_markdown(args: argparse.Namespace) -> str:
    checklist_tasks = "x" if args.pending_tasks_count == 0 else " "
    return (
        "## Resumen ejecutivo\n"
        f"- [adrotech] {args.summary.strip()}\n\n"
        "## Alcance\n"
        f"- {args.scope.strip()}\n"
        f"- Change: `{args.change_name.strip()}`\n\n"
        "## Evidencia de validación\n"
        f"- {args.validation.strip()}\n"
        f"- Evidencia funcional: {args.functional_evidence.strip()}\n\n"
        "## Riesgos\n"
        f"- {args.risks.strip()}\n\n"
        "## Rollback / Impacto\n"
        f"- {args.rollback_impact.strip()}\n\n"
        "## Checklist\n"
        f"- [{checklist_tasks}] Change con tasks al 100% (sin pendientes).\n"
        "- [x] PR generado por `delivery` para change completado.\n"
        "- [x] Tag `adrotech` aplicado en artefactos de entrega.\n"
        "- [x] Se aplicará gate de continuidad para no iniciar otro change sin autorización/cierre.\n"
        "\n"
        "## Diagrama (ASCII)\n"
        "```text\n"
        f"{args.diagram.strip()}\n"
        "```\n"
    )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors = validate(args)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("OK: body PR validado")
        return 0

    markdown = render_markdown(args)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"OK: body PR renderizado en {output_path}")
        return 0

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
