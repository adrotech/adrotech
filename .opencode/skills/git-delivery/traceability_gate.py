#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TRACE_COMMIT_PATTERN = re.compile(r"TRACE-COMMIT\s*:\s*([0-9a-fA-F]{7,40})")
TRACE_TASK_PATTERN = re.compile(r"TRACE-TASK\s*:\s*([A-Za-z0-9_.\-/#]+)")
TASK_ITEM_PATTERN = re.compile(r"^\s*[-*]\s*\[(?P<state>[ xX])\]\s*(?P<body>.+?)\s*$")
TASK_ID_PATTERN = re.compile(r"^(?P<task_id>\d+(?:\.\d+)*)\s+(?P<description>.+)$")


@dataclass(frozen=True)
class TaskItem:
    task_id: str
    description: str
    completed: bool


@dataclass(frozen=True)
class CommitItem:
    sha: str
    subject: str


class GateError(RuntimeError):
    pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gate de trazabilidad 100%: valida y sincroniza comentarios TRACE-COMMIT y TRACE-TASK."
        )
    )
    parser.add_argument("--change", required=True, help="Nombre del change OpenSpec.")
    parser.add_argument("--repo", required=True, help="Repositorio owner/repo.")
    parser.add_argument("--issue-number", type=int, required=True, help="Issue de seguimiento.")
    parser.add_argument(
        "--base-ref",
        default="origin/develop",
        help="Referencia base para calcular commits relevantes del branch.",
    )
    parser.add_argument("--pr-number", type=int, help="PR a inspeccionar (opcional).")
    parser.add_argument(
        "--tasks-file",
        help="Ruta alternativa al tasks.md (útil para tests).",
    )
    parser.add_argument(
        "--commits-file",
        help="JSON local con commits [{\"sha\":..., \"subject\":...}] para modo offline.",
    )
    parser.add_argument(
        "--comments-file",
        help="JSON local con comentarios [{\"body\":...}] para modo offline.",
    )
    parser.add_argument(
        "--continuity",
        default="Continuar con el siguiente paso operativo del change.",
        help="Texto de continuidad para comentarios autogenerados.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No publica comentarios; solo reporta faltantes y comando de recuperación.",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Imprime también un resumen JSON parseable.",
    )
    return parser.parse_args(argv)


def run_command(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        raise GateError(
            f"Fallo ejecutando: {' '.join(command)}\nstdout: {stdout}\nstderr: {stderr}"
        )
    return completed.stdout


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_tasks_file(repo_root: Path, change_name: str) -> Path:
    return repo_root / "openspec" / "changes" / change_name / "tasks.md"


def parse_tasks(tasks_path: Path) -> list[TaskItem]:
    if not tasks_path.is_file():
        raise GateError(f"No existe tasks.md en {tasks_path}")

    items: list[TaskItem] = []
    for raw_line in tasks_path.read_text(encoding="utf-8").splitlines():
        task_match = TASK_ITEM_PATTERN.match(raw_line)
        if not task_match:
            continue

        body = task_match.group("body").strip()
        task_id_match = TASK_ID_PATTERN.match(body)
        if not task_id_match:
            continue

        task_id = task_id_match.group("task_id")
        description = task_id_match.group("description").strip()
        state = task_match.group("state").lower()
        items.append(TaskItem(task_id=task_id, description=description, completed=state == "x"))

    if not items:
        raise GateError(
            "No se detectaron tasks parseables en tasks.md. "
            "Usa formato '- [ ] 1.1 Descripcion' o '- [x] 1.1 Descripcion'."
        )
    return items


def read_commits_from_file(path: Path) -> list[CommitItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    commits: list[CommitItem] = []
    for item in payload:
        sha = str(item.get("sha", "")).strip()
        subject = str(item.get("subject", "")).strip() or "Sin asunto"
        if sha:
            commits.append(CommitItem(sha=sha, subject=subject))
    return commits


def commits_from_branch(repo_root: Path, base_ref: str) -> list[CommitItem]:
    output = run_command(
        ["git", "log", "--pretty=format:%H\t%s", f"{base_ref}..HEAD"],
        cwd=repo_root,
    )
    commits: list[CommitItem] = []
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t", maxsplit=1)
        sha = parts[0].strip()
        subject = parts[1].strip() if len(parts) > 1 else "Sin asunto"
        commits.append(CommitItem(sha=sha, subject=subject))
    return commits


def commits_from_pr(repo_root: Path, repo: str, pr_number: int) -> list[CommitItem]:
    output = run_command(
        ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "commits"],
        cwd=repo_root,
    )
    payload = json.loads(output)
    commits: list[CommitItem] = []
    for item in payload.get("commits", []):
        sha = str(item.get("oid", "")).strip()
        subject = str(item.get("messageHeadline", "")).strip() or "Sin asunto"
        if sha:
            commits.append(CommitItem(sha=sha, subject=subject))
    return commits


def read_comments_from_file(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    comments: list[str] = []
    for item in payload:
        body = str(item.get("body", ""))
        if body.strip():
            comments.append(body)
    return comments


def read_issue_comments(repo_root: Path, repo: str, issue_number: int) -> list[str]:
    output = run_command(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "comments"],
        cwd=repo_root,
    )
    payload = json.loads(output)
    return [str(item.get("body", "")) for item in payload.get("comments", []) if str(item.get("body", "")).strip()]


def extract_trace_markers(comments: list[str]) -> tuple[set[str], set[str]]:
    traced_commits: set[str] = set()
    traced_tasks: set[str] = set()

    for body in comments:
        for commit_match in TRACE_COMMIT_PATTERN.findall(body):
            traced_commits.add(commit_match.lower())
        for task_match in TRACE_TASK_PATTERN.findall(body):
            traced_tasks.add(task_match.strip())

    return traced_commits, traced_tasks


def has_commit_marker(traced_commits: set[str], sha: str) -> bool:
    sha_normalized = sha.lower()
    return any(
        sha_normalized.startswith(marker) or marker.startswith(sha_normalized)
        for marker in traced_commits
    )


def commit_comment_body(repo: str, change: str, commit: CommitItem, continuity: str) -> str:
    return (
        "## Avance de trazabilidad de entrega\n\n"
        f"TRACE-COMMIT: {commit.sha}\n"
        f"TRACE-TASK: {change}#commit-{commit.sha[:12]}\n\n"
        "### Resumen\n"
        f"- Commit relevante trazado para `{change}`.\n"
        f"- Asunto: {commit.subject}\n\n"
        "### Commit\n"
        f"- Commit ID: `{commit.sha}`\n"
        f"- Link: https://github.com/{repo}/commit/{commit.sha}\n\n"
        "### Continuidad\n"
        f"- Siguiente paso: {continuity}\n"
    )


def task_comment_body(change: str, task: TaskItem, continuity: str) -> str:
    trace_task = f"{change}#{task.task_id}"
    return (
        "## Avance de tarea de spec\n\n"
        f"TRACE-TASK: {trace_task}\n\n"
        "### Resumen\n"
        f"- Tarea `{task.task_id}` trazada para cierre de delivery.\n"
        f"- Descripcion: {task.description}\n\n"
        "### Continuidad\n"
        f"- Siguiente paso: {continuity}\n"
    )


def publish_comment(repo_root: Path, repo: str, issue_number: int, body: str) -> None:
    run_command(
        ["gh", "issue", "comment", str(issue_number), "--repo", repo, "--body", body],
        cwd=repo_root,
    )


def build_recovery_command(args: argparse.Namespace) -> str:
    command = [
        "python3 .opencode/skills/git-delivery/traceability_gate.py",
        f"--change {args.change}",
        f"--repo {args.repo}",
        f"--issue-number {args.issue_number}",
        f"--base-ref {args.base_ref}",
    ]
    if args.pr_number:
        command.append(f"--pr-number {args.pr_number}")
    command.append("--dry-run")
    return " ".join(command)


def run_gate(args: argparse.Namespace) -> dict[str, object]:
    repo_root = repository_root()
    tasks_path = Path(args.tasks_file).resolve() if args.tasks_file else default_tasks_file(repo_root, args.change)

    tasks = parse_tasks(tasks_path)
    completed_tasks = [task for task in tasks if task.completed]

    if args.commits_file:
        commits = read_commits_from_file(Path(args.commits_file).resolve())
    elif args.pr_number:
        commits = commits_from_pr(repo_root, args.repo, args.pr_number)
    else:
        commits = commits_from_branch(repo_root, args.base_ref)

    if args.comments_file:
        comments = read_comments_from_file(Path(args.comments_file).resolve())
    else:
        comments = read_issue_comments(repo_root, args.repo, args.issue_number)

    traced_commits, traced_tasks = extract_trace_markers(comments)

    missing_commits = [commit for commit in commits if not has_commit_marker(traced_commits, commit.sha)]
    missing_tasks = [task for task in completed_tasks if f"{args.change}#{task.task_id}" not in traced_tasks]

    posted_commit_markers: list[str] = []
    posted_task_markers: list[str] = []
    if not args.dry_run and not args.comments_file:
        for commit in missing_commits:
            publish_comment(repo_root, args.repo, args.issue_number, commit_comment_body(args.repo, args.change, commit, args.continuity))
            posted_commit_markers.append(commit.sha)
        for task in missing_tasks:
            publish_comment(repo_root, args.repo, args.issue_number, task_comment_body(args.change, task, args.continuity))
            posted_task_markers.append(task.task_id)

    commit_total = len(commits)
    task_total = len(completed_tasks)
    commit_done = commit_total - len(missing_commits)
    task_done = task_total - len(missing_tasks)

    status = "ok"
    recovery = None
    if missing_commits or missing_tasks:
        status = "sync_pending" if args.dry_run or args.comments_file else "ok"
        recovery = (
            "python3 .opencode/skills/git-delivery/traceability_gate.py "
            f"--change {args.change} --repo {args.repo} --issue-number {args.issue_number} "
            f"--base-ref {args.base_ref}"
            + (f" --pr-number {args.pr_number}" if args.pr_number else "")
        )

    return {
        "status": status,
        "change": args.change,
        "issue": args.issue_number,
        "coverage": {
            "commits": f"{commit_done}/{commit_total}",
            "tasks": f"{task_done}/{task_total}",
        },
        "missing": {
            "commit_count": len(missing_commits),
            "task_count": len(missing_tasks),
            "commit_shas": [commit.sha for commit in missing_commits],
            "task_ids": [task.task_id for task in missing_tasks],
        },
        "posted": {
            "commit_markers": posted_commit_markers,
            "task_markers": posted_task_markers,
        },
        "recovery": recovery,
    }


def print_human_summary(result: dict[str, object]) -> None:
    status = result["status"]
    coverage = result["coverage"]
    missing = result["missing"]

    print(f"status: {status}")
    print(f"commits: {coverage['commits']}")
    print(f"tasks: {coverage['tasks']}")

    if missing["commit_count"] or missing["task_count"]:
        print(f"faltantes commits: {missing['commit_count']}")
        print(f"faltantes tasks: {missing['task_count']}")
        if result.get("recovery"):
            print("recovery:")
            print(result["recovery"])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        result = run_gate(args)
    except GateError as error:
        recovery = build_recovery_command(args)
        print("status: blocked", file=sys.stderr)
        print(f"causa: {error}", file=sys.stderr)
        print("recovery:", file=sys.stderr)
        print(recovery, file=sys.stderr)
        if args.output_json:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "cause": str(error),
                        "recovery": recovery,
                    },
                    ensure_ascii=False,
                )
            )
        return 2

    print_human_summary(result)
    if args.output_json:
        print(json.dumps(result, ensure_ascii=False))

    return 0 if result["status"] == "ok" else 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
