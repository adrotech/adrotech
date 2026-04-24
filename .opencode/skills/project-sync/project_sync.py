#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANAGED_BEGIN = "<!-- OPENSPEC_PROJECT_SYNC:BEGIN -->"
MANAGED_END = "<!-- OPENSPEC_PROJECT_SYNC:END -->"
MANUAL_BEGIN = "<!-- OPENSPEC_PROJECT_SYNC:MANUAL_NOTES:BEGIN -->"
MANUAL_END = "<!-- OPENSPEC_PROJECT_SYNC:MANUAL_NOTES:END -->"
ORDERING_BEGIN = "<!-- OPENSPEC_PROJECT_SYNC:ORDERING_METADATA:BEGIN -->"
ORDERING_END = "<!-- OPENSPEC_PROJECT_SYNC:ORDERING_METADATA:END -->"
SNAPSHOT_LIMIT = 45_000
HARD_BODY_LIMIT = 60_000
TRUNCATION_NOTE = "_Resumen truncado; consulta el artefacto de OpenSpec referenciado para ver el contenido completo._"
ORDERING_OVERRIDES_PATH = Path(__file__).with_name("ordering_overrides.json")

PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
CATEGORY_RANK = {
    "foundation": 0,
    "data": 1,
    "security": 2,
    "identity": 3,
    "governance": 4,
    "topology": 5,
    "feature": 6,
    "planning": 7,
    "workflow": 8,
    "general": 9,
}

SURFACE_KEYWORDS = {
    "workflow": ("workflow", "openspec", "project", "sync"),
    "frontend": (
        "frontend",
        "web",
        "astro",
        "mdx",
        "ui",
        "layout",
        "component",
        "seo",
        "a11y",
        "content",
    ),
    "full-stack": ("full-stack", "end-to-end", "app and api"),
}

CATEGORY_KEYWORDS = {
    "workflow": ("workflow", "project sync", "openspec"),
    "planning": ("roadmap", "plan", "milestone", "sequence"),
    "security": ("security", "audit", "traceability", "alert"),
    "identity": ("authentication", "password", "session", "credential"),
    "governance": ("governance", "role", "permission", "authorization"),
    "topology": ("resident", "membership", "neighborhood", "lot", "scope"),
    "data": ("postgresql", "data model", "schema", "migration"),
    "foundation": ("foundation", "architecture", "runtime", "compose", "platform"),
    "feature": ("news", "voting", "alert lifecycle", "publishing"),
}

REFERENCE_PATTERN = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`")
ORDERING_BLOCK_PATTERN = re.compile(
    re.escape(ORDERING_BEGIN) + r"\n?(.*?)\n?" + re.escape(ORDERING_END),
    re.DOTALL,
)

DEFAULT_CONFIG = {
    "github_owner": os.environ.get("GITHUB_OWNER", "adrotech"),
    "project_number": os.environ.get("PROJECT_NUMBER", "2"),
    "project_id": os.environ.get("PROJECT_ID", "PVT_kwHOCZrNic4BUhiB"),
    "status_field_id": os.environ.get("STATUS_FIELD_ID", "PVTSSF_lAHOCZrNic4BUhiBzhBpEIQ"),
    "priority_field_id": os.environ.get("PRIORITY_FIELD_ID", "PVTSSF_lAHOCZrNic4BUhiBzhBpEQ0"),
    "size_field_id": os.environ.get("SIZE_FIELD_ID", "PVTSSF_lAHOCZrNic4BUhiBzhBpEQ4"),
    "project_tag": os.environ.get("PROJECT_TAG", "adrotech"),
}

OPTION_IDS = {
    "status": {
        "Backlog": os.environ.get("STATUS_OPTION_BACKLOG", "f75ad846"),
        "Ready": os.environ.get("STATUS_OPTION_READY", "61e4505c"),
        "In progress": os.environ.get("STATUS_OPTION_IN_PROGRESS", "47fc9ee4"),
        "In review": os.environ.get("STATUS_OPTION_IN_REVIEW", "df73e18b"),
        "Done": os.environ.get("STATUS_OPTION_DONE", "98236657"),
    },
    "priority": {
        "P0": os.environ.get("PRIORITY_OPTION_P0", "79628723"),
        "P1": os.environ.get("PRIORITY_OPTION_P1", "0a877460"),
        "P2": os.environ.get("PRIORITY_OPTION_P2", "da944a9c"),
    },
    "size": {
        "XS": os.environ.get("SIZE_OPTION_XS", "6c6483d2"),
        "S": os.environ.get("SIZE_OPTION_S", "f784b110"),
        "M": os.environ.get("SIZE_OPTION_M", "7515a9f1"),
        "L": os.environ.get("SIZE_OPTION_L", "817d0097"),
        "XL": os.environ.get("SIZE_OPTION_XL", "db339eb2"),
    },
}

QUERY_PROJECT_ITEM = """
query($itemId: ID!) {
  node(id: $itemId) {
    __typename
    ... on ProjectV2Item {
      id
      type
      content {
        __typename
        ... on DraftIssue {
          id
          title
          body
        }
        ... on Issue {
          id
          title
          body
        }
        ... on PullRequest {
          id
          title
          body
        }
      }
    }
  }
}
""".strip()

MUTATION_CREATE_DRAFT = """
mutation($projectId: ID!, $title: String!, $body: String!) {
  addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
    projectItem {
      id
      type
      content {
        __typename
        ... on DraftIssue {
          id
          title
          body
        }
      }
    }
  }
}
""".strip()

MUTATION_UPDATE_DRAFT = """
mutation($draftIssueId: ID!, $title: String!, $body: String!) {
  updateProjectV2DraftIssue(input: {draftIssueId: $draftIssueId, title: $title, body: $body}) {
    draftIssue {
      id
      title
      body
    }
  }
}
""".strip()

MUTATION_UPDATE_SINGLE_SELECT = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: {singleSelectOptionId: $optionId}
    }
  ) {
    projectV2Item {
      id
    }
  }
}
""".strip()


class SyncError(RuntimeError):
    pass


class SyncPending(SyncError):
    pass


@dataclass(frozen=True)
class ArtifactInventory:
    root: str
    core: dict[str, str | None]
    specs: list[str]
    supplemental: list[str]


@dataclass(frozen=True)
class OrderingMetadata:
    priority: str | None
    surface: str
    category: str
    suggested_sequence: int
    dependencies: list[str]
    sources: list[str]


@dataclass(frozen=True)
class ChangeRecord:
    change_name: str
    directory: Path
    metadata_path: Path
    metadata: dict[str, Any]
    archived: bool

    @property
    def project_item_id(self) -> str | None:
        value = self.metadata.get("project_item_id")
        return str(value) if value else None


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sincroniza artefactos de cambios OpenSpec con items de GitHub Project.")
    parser.add_argument("--change", action="append", help="Change name to sync. Repeat for multiple changes.")
    parser.add_argument("--project-item-id", help="Override project item id for single-change sync.")
    parser.add_argument("--status", choices=sorted(OPTION_IDS["status"].keys()))
    parser.add_argument("--priority", choices=sorted(OPTION_IDS["priority"].keys()))
    parser.add_argument("--size", choices=sorted(OPTION_IDS["size"].keys()))
    parser.add_argument("--backfill", action="store_true", help="Sync all mapped active changes by default.")
    parser.add_argument("--active-only", action="store_true", help="When backfilling, limit sync to active changes only.")
    parser.add_argument("--include-archived", action="store_true", help="When backfilling, include archived mapped changes after active changes.")
    parser.add_argument("--dry-run", action="store_true", help="Compute and compare without remote writes.")
    parser.add_argument("--persist-mapping", action=argparse.BooleanOptionalAction, default=True, help="Persist a newly created project item id into .openspec.yaml.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--print-body", action="store_true", help="Include generated body in JSON output.")
    args = parser.parse_args(argv)
    if not args.backfill and not args.change:
        parser.error("provide --change or --backfill")
    if args.project_item_id and (not args.change or len(args.change) != 1):
        parser.error("--project-item-id requires exactly one --change")
    if args.backfill and args.project_item_id:
        parser.error("--project-item-id cannot be combined with --backfill")
    if args.include_archived and not args.backfill:
        parser.error("--include-archived requires --backfill")
    return args


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            return data
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # pragma: no cover
        raise SyncError(f"failed to parse YAML {path}: {exc}") from exc

    data: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        if value[0:1] == value[-1:] and value.startswith(("'", '"')):
            value = value[1:-1]
        elif value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
            continue
        data[key] = value
    return data


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise SyncError(f"failed to parse JSON {path}: {exc}") from exc


def load_ordering_overrides() -> dict[str, dict[str, Any]]:
    data = load_json(ORDERING_OVERRIDES_PATH)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SyncError(f"ordering overrides must be an object: {ORDERING_OVERRIDES_PATH}")
    normalized: dict[str, dict[str, Any]] = {}
    for change_name, value in data.items():
        if isinstance(change_name, str) and isinstance(value, dict):
            normalized[change_name] = copy.deepcopy(value)
    return normalized


def iter_change_records(repo_root: Path, include_archived: bool) -> list[ChangeRecord]:
    base = repo_root / "openspec" / "changes"
    records: list[ChangeRecord] = []

    for entry in sorted(base.iterdir()):
        if not entry.is_dir() or entry.name.startswith(".") or entry.name == "archive":
            continue
        metadata_path = entry / ".openspec.yaml"
        if metadata_path.exists():
            records.append(ChangeRecord(entry.name, entry, metadata_path, load_yaml(metadata_path), False))

    if include_archived:
        archive_root = base / "archive"
        if archive_root.exists():
            for entry in sorted(archive_root.iterdir()):
                if not entry.is_dir() or entry.name.startswith("."):
                    continue
                metadata_path = entry / ".openspec.yaml"
                if not metadata_path.exists():
                    continue
                change_name = archived_change_name(entry.name)
                records.append(ChangeRecord(change_name, entry, metadata_path, load_yaml(metadata_path), True))

    return records


def archived_change_name(directory_name: str) -> str:
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", directory_name)
    return match.group(1) if match else directory_name


def find_change_record(repo_root: Path, change_name: str) -> ChangeRecord:
    for record in iter_change_records(repo_root, include_archived=True):
        if record.change_name == change_name:
            return record
    raise SyncError(f"change not found: {change_name}")


def read_markdown(path: Path) -> str:
    return normalize_markdown(path.read_text(encoding="utf-8"))


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    normalized = "\n".join(lines).strip()
    return normalized


def discover_artifacts(change_dir: Path, repo_root: Path) -> ArtifactInventory:
    core = {
        "proposal": relative_artifact_path(change_dir / "proposal.md", repo_root),
        "design": relative_artifact_path(change_dir / "design.md", repo_root),
        "tasks": relative_artifact_path(change_dir / "tasks.md", repo_root),
    }
    specs = sorted(
        str(path.relative_to(repo_root)).replace(os.sep, "/")
        for path in change_dir.glob("specs/**/spec.md")
        if path.is_file()
    )
    supplemental = sorted(
        str(path.relative_to(repo_root)).replace(os.sep, "/")
        for path in change_dir.glob("*.md")
        if path.is_file() and path.name not in {"proposal.md", "design.md", "tasks.md"}
    )
    return ArtifactInventory(
        root=str(change_dir.relative_to(repo_root)).replace(os.sep, "/") + "/",
        core=core,
        specs=specs,
        supplemental=supplemental,
    )


def relative_artifact_path(path: Path, repo_root: Path) -> str | None:
    if not path.exists():
        return None
    return str(path.relative_to(repo_root)).replace(os.sep, "/")


def read_change_context(record: ChangeRecord) -> str:
    parts: list[str] = []
    for filename in ("proposal.md", "design.md", "tasks.md"):
        path = record.directory / filename
        if path.exists():
            parts.append(read_markdown(path).lower())
    return "\n".join(parts)


def infer_surface(change_name: str, context: str, override: dict[str, Any]) -> tuple[str, list[str]]:
    if isinstance(override.get("surface"), str):
        return str(override["surface"]), ["override"]

    lowered_name = change_name.lower()
    for surface, keywords in SURFACE_KEYWORDS.items():
        if any(keyword in lowered_name or keyword in context for keyword in keywords):
            return surface, ["heuristic"]
    return "frontend", ["default"]


def infer_category(change_name: str, context: str, override: dict[str, Any]) -> tuple[str, list[str]]:
    if isinstance(override.get("category"), str):
        return str(override["category"]), ["override"]

    lowered_name = change_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered_name or keyword in context for keyword in keywords):
            return category, ["heuristic"]
    if change_name.startswith(("define-", "establish-")):
        return "foundation", ["heuristic"]
    if change_name.startswith(("design-", "model-")):
        return "feature", ["heuristic"]
    return "general", ["default"]


def infer_priority(change_name: str, category: str, override: dict[str, Any]) -> tuple[str | None, list[str]]:
    if override.get("priority") in PRIORITY_RANK:
        return str(override["priority"]), ["override"]

    if change_name.startswith("sync-") or category in {"workflow", "planning"}:
        return "P2", ["heuristic"]
    if category in {"foundation", "data", "security"}:
        return "P0", ["heuristic"]
    if category in {"identity", "governance", "topology", "feature"}:
        return "P1", ["heuristic"]
    return None, ["default"]


def infer_dependencies(record: ChangeRecord, known_changes: set[str], context: str, override: dict[str, Any]) -> tuple[list[str], list[str]]:
    if isinstance(override.get("dependencies"), list):
        deps = [str(dep) for dep in override["dependencies"] if isinstance(dep, str) and dep in known_changes and dep != record.change_name]
        return sorted(dict.fromkeys(deps)), ["override"]

    deps = [ref for ref in REFERENCE_PATTERN.findall(context) if ref in known_changes and ref != record.change_name]
    return sorted(dict.fromkeys(deps)), ["artifact"] if deps else ["default"]


def priority_sort_value(priority: str | None) -> int:
    return PRIORITY_RANK.get(priority or "", max(PRIORITY_RANK.values()) + 1)


def category_sort_value(category: str) -> int:
    return CATEGORY_RANK.get(category, max(CATEGORY_RANK.values()) + 1)


def build_ordering_metadata_map(repo_root: Path) -> dict[str, OrderingMetadata]:
    records = [record for record in iter_change_records(repo_root, include_archived=False) if not record.archived]
    if not records:
        return {}

    overrides = load_ordering_overrides()
    known_changes = {record.change_name for record in records}
    contexts = {record.change_name: read_change_context(record) for record in records}
    partial: dict[str, dict[str, Any]] = {}

    for record in records:
        override = overrides.get(record.change_name, {})
        context = contexts[record.change_name]
        surface, surface_sources = infer_surface(record.change_name, context, override)
        category, category_sources = infer_category(record.change_name, context, override)
        priority, priority_sources = infer_priority(record.change_name, category, override)
        dependencies, dependency_sources = infer_dependencies(record, known_changes, context, override)
        partial[record.change_name] = {
            "surface": surface,
            "category": category,
            "priority": priority,
            "dependencies": dependencies,
            "sources": sorted(set(surface_sources + category_sources + priority_sources + dependency_sources)),
        }

    dependents: dict[str, set[str]] = defaultdict(set)
    indegree = {record.change_name: 0 for record in records}
    for change_name, metadata in partial.items():
        for dependency in metadata["dependencies"]:
            if dependency not in indegree:
                continue
            dependents[dependency].add(change_name)
            indegree[change_name] += 1

    def sort_key(change_name: str) -> tuple[int, int, str]:
        metadata = partial[change_name]
        return (
            priority_sort_value(metadata["priority"]),
            category_sort_value(metadata["category"]),
            change_name,
        )

    ready = sorted([change_name for change_name, count in indegree.items() if count == 0], key=sort_key)
    ordered: list[str] = []
    while ready:
        change_name = ready.pop(0)
        ordered.append(change_name)
        for dependent in sorted(dependents.get(change_name, set()), key=sort_key):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=sort_key)

    remaining = sorted([change_name for change_name, count in indegree.items() if count > 0], key=sort_key)
    ordered.extend(change_name for change_name in remaining if change_name not in ordered)

    result: dict[str, OrderingMetadata] = {}
    for index, change_name in enumerate(ordered, start=1):
        metadata = partial[change_name]
        result[change_name] = OrderingMetadata(
            priority=metadata["priority"],
            surface=metadata["surface"],
            category=metadata["category"],
            suggested_sequence=index * 10,
            dependencies=metadata["dependencies"],
            sources=metadata["sources"],
        )
    return result


def extract_manual_notes(existing_body: str | None) -> str:
    if existing_body:
        match = re.search(re.escape(MANUAL_BEGIN) + r"\n?(.*?)\n?" + re.escape(MANUAL_END), existing_body, re.DOTALL)
        if match:
            content = match.group(1).strip("\n")
            return content or default_manual_notes_content()
    return default_manual_notes_content()


def default_manual_notes_content() -> str:
    return "## Notas manuales\n_Agrega aqui notas humanas opcionales. Esta seccion se conserva entre ejecuciones de sincronizacion._"


def strip_ordering_metadata_block(manual_notes: str) -> str:
    stripped = ORDERING_BLOCK_PATTERN.sub("", manual_notes).strip()
    return stripped or default_manual_notes_content()


def render_ordering_metadata(metadata: OrderingMetadata) -> str:
    lines = [
        ORDERING_BEGIN,
        "## Metadatos de orden sugeridos",
        f"- Priority: `{metadata.priority}`" if metadata.priority else "- Priority: _sin inferencia segura_",
        f"- Surface: `{metadata.surface}`",
        f"- Category: `{metadata.category}`",
        f"- Suggested sequence: `{metadata.suggested_sequence}`",
    ]
    if metadata.dependencies:
        lines.append("- Dependencies:")
        lines.extend(f"  - `{dependency}`" for dependency in metadata.dependencies)
    else:
        lines.append("- Dependencies: _ninguna inferida con seguridad_")
    lines.append(f"- Source: `{', '.join(metadata.sources)}`")
    lines.append(ORDERING_END)
    return "\n".join(lines)


def merge_manual_notes(manual_notes: str, ordering_metadata: OrderingMetadata | None) -> str:
    base = strip_ordering_metadata_block(manual_notes)
    if not ordering_metadata:
        return base
    return f"{base}\n\n{render_ordering_metadata(ordering_metadata)}"


def render_metadata_lines(record: ChangeRecord, inventory: ArtifactInventory, status: str | None) -> list[str]:
    lines = [
        "Resumen de seguimiento del cambio OpenSpec para revision en GitHub Project.",
        "",
        "## Metadatos del cambio",
        f"- Tag proyecto: `{DEFAULT_CONFIG['project_tag']}`",
        f"- Cambio: `{record.change_name}`",
        f"- Ruta OpenSpec: `{inventory.root}`",
    ]
    if status:
        lines.append(f"- Estado solicitado para sincronizacion: `{status}`")
    for key in sorted(record.metadata):
        value = record.metadata[key]
        if isinstance(value, (dict, list)):
            continue
        lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")
    return lines


def render_inventory_lines(inventory: ArtifactInventory) -> list[str]:
    lines = ["## Inventario de artefactos", "### Artefactos principales"]
    for name in ("proposal", "design", "tasks"):
        artifact_path = inventory.core[name]
        if artifact_path:
            lines.append(f"- {name}: `{artifact_path}`")
        else:
            lines.append(f"- {name}: _no presente_")

    lines.append("### Especificaciones")
    if inventory.specs:
        lines.extend(f"- `{path}`" for path in inventory.specs)
    else:
        lines.append("- _ninguna encontrada_")

    lines.append("### Documentacion complementaria")
    if inventory.supplemental:
        lines.extend(f"- `{path}`" for path in inventory.supplemental)
    else:
        lines.append("- _ningun documento encontrado_")
    return lines


def build_body(
    record: ChangeRecord,
    repo_root: Path,
    requested_status: str | None,
    ordering_metadata: OrderingMetadata | None,
    existing_body: str | None = None,
) -> tuple[str, bool]:
    inventory = discover_artifacts(record.directory, repo_root)
    sections = {
        "proposal": render_core_section("Propuesta", record.directory / "proposal.md"),
        "design": render_core_section("Diseno", record.directory / "design.md"),
        "tasks": render_core_section("Tareas", record.directory / "tasks.md"),
    }
    manual_notes = merge_manual_notes(extract_manual_notes(existing_body), ordering_metadata)

    body, truncated = compose_body(record, inventory, requested_status, sections, manual_notes)
    if len(body) <= SNAPSHOT_LIMIT:
        return body, truncated

    truncated = True
    if sections["design"]:
        sections["design"] = truncate_section_to_reference("Diseno", inventory.core["design"])
        body, _ = compose_body(record, inventory, requested_status, sections, manual_notes, truncated=True)
    if len(body) <= SNAPSHOT_LIMIT:
        return body, True

    if sections["proposal"]:
        sections["proposal"] = truncate_section_to_reference("Propuesta", inventory.core["proposal"])
        body, _ = compose_body(record, inventory, requested_status, sections, manual_notes, truncated=True)
    if len(body) <= HARD_BODY_LIMIT:
        return body, True

    inventory = ArtifactInventory(
        root=inventory.root,
        core=inventory.core,
        specs=inventory.specs[:10],
        supplemental=inventory.supplemental[:10],
    )
    body, _ = compose_body(record, inventory, requested_status, sections, manual_notes, truncated=True)
    if len(body) > HARD_BODY_LIMIT:
        raise SyncError(f"generated body exceeds hard limit for {record.change_name}")
    return body, True


def render_core_section(title: str, path: Path) -> str | None:
    if not path.exists():
        return None
    content = read_markdown(path)
    if path.name == "tasks.md":
        content = normalize_task_checkboxes(content)
    if not content:
        return f"## {title}\n_El archivo del artefacto esta vacio._"
    return f"## {title}\n\n{content}"


def normalize_task_checkboxes(content: str) -> str:
    if not content:
        return content

    lines: list[str] = []
    checkbox_pattern = re.compile(r"^(\s*[-*]\s*)\[(?:\s|x|X)?\](\s+.*)?$")

    for line in content.split("\n"):
        match = checkbox_pattern.match(line)
        if not match:
            lines.append(line)
            continue

        prefix = match.group(1)
        suffix = match.group(2) or ""
        marker = "x" if "[x]" in line.lower() else " "
        lines.append(f"{prefix}[{marker}]{suffix}")

    return "\n".join(lines)


def truncate_section_to_reference(title: str, artifact_path: str | None) -> str | None:
    if not artifact_path:
        return None
    return f"## {title}\n\n{TRUNCATION_NOTE}\n\nConsulta `{artifact_path}`."


def compose_body(
    record: ChangeRecord,
    inventory: ArtifactInventory,
    requested_status: str | None,
    sections: dict[str, str | None],
    manual_notes: str,
    truncated: bool = False,
) -> tuple[str, bool]:
    lines: list[str] = [MANAGED_BEGIN]
    lines.extend(render_metadata_lines(record, inventory, requested_status))
    lines.append("")
    lines.extend(render_inventory_lines(inventory))
    if truncated:
        lines.append("")
        lines.append("## Notas del resumen")
        lines.append(f"- {TRUNCATION_NOTE[1:-1]}")

    for name in ("proposal", "design", "tasks"):
        section = sections.get(name)
        if section:
            lines.append("")
            lines.append(section)

    lines.append(MANAGED_END)
    lines.append("")
    lines.append(MANUAL_BEGIN)
    lines.append(manual_notes.strip())
    lines.append(MANUAL_END)
    body = "\n".join(lines).strip() + "\n"
    return body, truncated


def normalize_for_compare(text: str | None) -> str:
    return normalize_markdown(text or "")


def gh_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = {"query": query, "variables": variables}
    command = ["gh", "api", "graphql", "--input", "-"]
    result = subprocess.run(command, input=json.dumps(payload), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SyncError(result.stderr.strip() or result.stdout.strip() or "gh api graphql failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SyncError(f"invalid gh graphql response: {exc}") from exc


def fetch_project_item(item_id: str) -> dict[str, Any]:
    data = gh_graphql(QUERY_PROJECT_ITEM, {"itemId": item_id})
    node = (data.get("data") or {}).get("node")
    if not node:
        raise SyncError(f"project item not found: {item_id}")
    return node


def update_draft_issue(draft_issue_id: str, title: str, body: str) -> None:
    gh_graphql(MUTATION_UPDATE_DRAFT, {"draftIssueId": draft_issue_id, "title": title, "body": body})


def create_draft_issue(title: str, body: str) -> dict[str, Any]:
    data = gh_graphql(MUTATION_CREATE_DRAFT, {"projectId": DEFAULT_CONFIG["project_id"], "title": title, "body": body})
    project_item = ((data.get("data") or {}).get("addProjectV2DraftIssue") or {}).get("projectItem")
    if not project_item:
        raise SyncError("failed to create project draft item")
    return project_item


def update_single_select(item_id: str, field_id: str, option_id: str) -> None:
    gh_graphql(
        MUTATION_UPDATE_SINGLE_SELECT,
        {
            "projectId": DEFAULT_CONFIG["project_id"],
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )


def persist_project_item_id(record: ChangeRecord, project_item_id: str) -> None:
    text = record.metadata_path.read_text(encoding="utf-8")
    if "project_item_id:" in text:
        updated = re.sub(r"(?m)^project_item_id:\s*.*$", f"project_item_id: {project_item_id}", text)
    else:
        updated = text.rstrip() + f"\nproject_item_id: {project_item_id}\n"
    record.metadata_path.write_text(updated, encoding="utf-8")


def draft_title(change_name: str) -> str:
    tag = DEFAULT_CONFIG["project_tag"]
    return f"[{tag}] OpenSpec cambio: {change_name.replace('-', ' ')}"


def shell_quote(value: str) -> str:
    return subprocess.list2cmdline([value])


def build_recovery_command(
    change_name: str,
    status: str | None,
    priority: str | None,
    size: str | None,
    dry_run: bool,
    persist_mapping: bool,
    print_body: bool,
    project_item_override: str | None,
) -> str:
    parts = ["python3", ".opencode/skills/project-sync/project_sync.py", "--change", shell_quote(change_name)]
    if project_item_override:
        parts.extend(["--project-item-id", shell_quote(project_item_override)])
    if status:
        parts.extend(["--status", shell_quote(status)])
    if priority:
        parts.extend(["--priority", shell_quote(priority)])
    if size:
        parts.extend(["--size", shell_quote(size)])
    if dry_run:
        parts.append("--dry-run")
    if not persist_mapping:
        parts.append("--no-persist-mapping")
    if print_body:
        parts.append("--print-body")
    return " ".join(parts)


def new_field_result(field_name: str, value: str) -> dict[str, Any]:
    return {"field": field_name, "value": value, "status": "pending", "action": "pending"}


def new_body_result(action: str = "skip") -> dict[str, Any]:
    return {"status": "pending", "action": action}


def body_sync_pending(action: str, reason: str, recovery_command: str, *, error: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "sync_pending",
        "action": action,
        "reason": reason,
        "recovery": recovery_command,
    }
    if error:
        payload["error"] = error
    return payload


def sync_change(
    record: ChangeRecord,
    repo_root: Path,
    ordering_metadata_map: dict[str, OrderingMetadata],
    status: str | None,
    priority: str | None,
    size: str | None,
    dry_run: bool,
    persist_mapping: bool,
    project_item_override: str | None,
    print_body: bool,
) -> dict[str, Any]:
    recovery_command = build_recovery_command(
        record.change_name,
        status,
        priority,
        size,
        dry_run,
        persist_mapping,
        print_body,
        project_item_override,
    )
    result: dict[str, Any] = {
        "change": record.change_name,
        "archived": record.archived,
        "metadata_path": str(record.metadata_path.relative_to(repo_root)).replace(os.sep, "/"),
        "recovery": recovery_command,
    }
    item_id = project_item_override or record.project_item_id
    current_body: str | None = None
    draft_issue_id: str | None = None
    body_sync = new_body_result()
    field_updates: list[dict[str, Any]] = []
    content_type: str | None = None
    ordering_metadata = ordering_metadata_map.get(record.change_name)
    derived_priority = priority or (ordering_metadata.priority if ordering_metadata else None)

    if item_id:
        result["project_item_id"] = item_id
    else:
        result["project_item_id"] = None

    if item_id:
        try:
            node = fetch_project_item(item_id)
            content = node.get("content") or {}
            result["project_item_type"] = node.get("type")
            content_type = content.get("__typename")
            result["content_type"] = content_type
            if content_type == "DraftIssue":
                draft_issue_id = content.get("id")
                current_body = content.get("body") or ""
            else:
                body_sync = body_sync_pending(
                    "skipped",
                    "mapped item is not a DRAFT_ISSUE; body sync skipped to avoid overwriting issue or PR content",
                    recovery_command,
                )
        except Exception as exc:
            body_sync = body_sync_pending("skipped", f"project item fetch failed: {exc}", recovery_command, error=str(exc))

    if ordering_metadata:
        result["ordering_metadata"] = {
            "priority": ordering_metadata.priority,
            "surface": ordering_metadata.surface,
            "category": ordering_metadata.category,
            "suggested_sequence": ordering_metadata.suggested_sequence,
            "dependencies": ordering_metadata.dependencies,
            "sources": ordering_metadata.sources,
        }

    generated_body, truncated = build_body(record, repo_root, status, ordering_metadata, current_body)
    result["truncated"] = truncated
    if print_body:
        result["body"] = generated_body

    created = False
    if not item_id:
        body_sync = {"status": "pending" if dry_run else "updated", "action": "create"}
        if not dry_run:
            try:
                created_item = create_draft_issue(draft_title(record.change_name), generated_body)
                item_id = created_item.get("id")
                draft_issue_id = ((created_item.get("content") or {}).get("id"))
                result["project_item_id"] = item_id
                result["content_type"] = ((created_item.get("content") or {}).get("__typename"))
                created = True
                if persist_mapping and item_id:
                    persist_project_item_id(record, item_id)
                    result["mapping_persisted"] = True
                else:
                    result["mapping_persisted"] = False
            except Exception as exc:
                body_sync = body_sync_pending(
                    "create",
                    "draft issue creation failed; retry with the recovery command",
                    recovery_command,
                    error=str(exc),
                )
        else:
            result["mapping_persisted"] = False
    elif content_type == "DraftIssue":
        if normalize_for_compare(current_body) == normalize_for_compare(generated_body):
            body_sync = {"status": "unchanged", "action": "unchanged"}
        else:
            body_sync = {"status": "pending" if dry_run else "updated", "action": "update"}
            if not dry_run and draft_issue_id:
                try:
                    update_draft_issue(draft_issue_id, draft_title(record.change_name), generated_body)
                except Exception as exc:
                    body_sync = body_sync_pending(
                        "update",
                        "draft issue body update failed; retry with the recovery command",
                        recovery_command,
                        error=str(exc),
                    )

    for field_name, value in (("status", status), ("priority", derived_priority), ("size", size)):
        if not value or not item_id:
            continue
        field_result = new_field_result(field_name, value)
        if field_name == "priority":
            field_result["source"] = "explicit" if priority else "derived"
        if dry_run:
            field_result["status"] = "pending"
        else:
            try:
                update_single_select(item_id, DEFAULT_CONFIG[f"{field_name}_field_id"], OPTION_IDS[field_name][value])
                field_result["status"] = "updated"
                field_result["action"] = "updated"
            except Exception as exc:
                field_result["status"] = "failed"
                field_result["action"] = "update"
                field_result["error"] = str(exc)
                field_result["recovery"] = recovery_command
        field_updates.append(field_result)

    if item_id is None and body_sync.get("status") in {"failed", "sync_pending"}:
        for field_result in field_updates:
            field_result["status"] = "sync_pending"
            field_result["reason"] = "project item id unavailable because draft creation failed"
            field_result["recovery"] = recovery_command

    result["body_sync"] = body_sync
    result["field_updates"] = field_updates
    result["created"] = created
    result["dry_run"] = dry_run
    return result


def choose_records(repo_root: Path, args: argparse.Namespace) -> list[ChangeRecord]:
    if args.backfill:
        include_archived = args.include_archived and not args.active_only
        return [record for record in iter_change_records(repo_root, include_archived=include_archived) if record.project_item_id]
    assert args.change
    return [find_change_record(repo_root, change_name) for change_name in args.change]


def summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "body_created": 0,
        "body_updated": 0,
        "body_unchanged": 0,
        "body_sync_pending": 0,
        "body_failed": 0,
        "field_updated": 0,
        "field_pending": 0,
        "field_failed": 0,
        "item_failed": 0,
    }
    for result in results:
        body_sync = result.get("body_sync") or {}
        action = body_sync.get("action")
        body_status = body_sync.get("status")
        if action == "create":
            summary["body_created"] += 1
        elif action == "update":
            summary["body_updated"] += 1
        elif body_status == "unchanged":
            summary["body_unchanged"] += 1
        if body_status == "sync_pending":
            summary["body_sync_pending"] += 1
        elif body_status == "failed":
            summary["body_failed"] += 1

        for field_result in result.get("field_updates", []):
            field_status = field_result.get("status")
            if field_status == "updated":
                summary["field_updated"] += 1
            elif field_status in {"pending", "sync_pending"}:
                summary["field_pending"] += 1
            elif field_status == "failed":
                summary["field_failed"] += 1

        if body_status == "failed" or any(field.get("status") == "failed" for field in result.get("field_updates", [])):
            summary["item_failed"] += 1
    return summary


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    records = choose_records(repo_root, args)
    ordering_metadata_map = build_ordering_metadata_map(repo_root)
    results: list[dict[str, Any]] = []

    for record in records:
        try:
            result = sync_change(
                record,
                repo_root,
                ordering_metadata_map,
                args.status,
                args.priority,
                args.size,
                args.dry_run,
                args.persist_mapping,
                args.project_item_id,
                args.print_body,
            )
            result["status"] = "ok"
        except Exception as exc:
            recovery_command = build_recovery_command(
                record.change_name,
                args.status,
                args.priority,
                args.size,
                args.dry_run,
                args.persist_mapping,
                args.print_body,
                args.project_item_id,
            )
            result = {
                "change": record.change_name,
                "archived": record.archived,
                "status": "failed",
                "error": str(exc),
                "recovery": recovery_command,
                "body_sync": {
                    "status": "failed",
                    "action": "skipped",
                    "error": str(exc),
                    "recovery": recovery_command,
                },
                "field_updates": [],
            }
        results.append(result)

    payload = {"summary": summarize(results), "results": results}
    print(json.dumps(payload, indent=2))
    return 1 if payload["summary"]["item_failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
