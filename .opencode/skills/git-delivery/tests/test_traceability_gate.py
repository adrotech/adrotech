import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "traceability_gate.py"
SPEC = importlib.util.spec_from_file_location("traceability_gate", MODULE_PATH)
assert SPEC is not None
traceability_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = traceability_gate
assert SPEC.loader is not None
SPEC.loader.exec_module(traceability_gate)


class TraceabilityGateTests(unittest.TestCase):
    def test_parse_tasks_extracts_completed_and_open(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = Path(temp_dir) / "tasks.md"
            tasks_file.write_text(
                """
## Tasks

- [x] 1.1 Implementar script
- [ ] 1.2 Documentar flujo
""".strip(),
                encoding="utf-8",
            )

            tasks = traceability_gate.parse_tasks(tasks_file)

            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].task_id, "1.1")
            self.assertTrue(tasks[0].completed)
            self.assertEqual(tasks[1].task_id, "1.2")
            self.assertFalse(tasks[1].completed)

    def test_extract_trace_markers_is_idempotent(self):
        comments = [
            "TRACE-COMMIT: abcdef1\nTRACE-TASK: change-x#1.1",
            "TRACE-COMMIT: abcdef1\nTRACE-TASK: change-x#1.1",
        ]

        traced_commits, traced_tasks = traceability_gate.extract_trace_markers(comments)

        self.assertEqual(traced_commits, {"abcdef1"})
        self.assertEqual(traced_tasks, {"change-x#1.1"})

    def test_run_gate_reports_sync_pending_when_missing_and_dry_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tasks_file = temp_path / "tasks.md"
            commits_file = temp_path / "commits.json"
            comments_file = temp_path / "comments.json"

            tasks_file.write_text(
                """
## Tasks

- [x] 1.1 Integrar gate
- [x] 1.2 Publicar comentario
""".strip(),
                encoding="utf-8",
            )
            commits_file.write_text(
                json.dumps(
                    [
                        {"sha": "abcdef1234567", "subject": "feat: gate"},
                        {"sha": "1234567abcdef0", "subject": "docs: update"},
                    ]
                ),
                encoding="utf-8",
            )
            comments_file.write_text(
                json.dumps(
                    [
                        {"body": "TRACE-COMMIT: abcdef1\nTRACE-TASK: change-x#1.1"},
                    ]
                ),
                encoding="utf-8",
            )

            args = traceability_gate.parse_args(
                [
                    "--change",
                    "change-x",
                    "--repo",
                    "owner/repo",
                    "--issue-number",
                    "123",
                    "--tasks-file",
                    str(tasks_file),
                    "--commits-file",
                    str(commits_file),
                    "--comments-file",
                    str(comments_file),
                    "--dry-run",
                ]
            )

            result = traceability_gate.run_gate(args)

            self.assertEqual(result["status"], "sync_pending")
            self.assertEqual(result["coverage"]["commits"], "1/2")
            self.assertEqual(result["coverage"]["tasks"], "1/2")
            self.assertEqual(result["missing"]["commit_count"], 1)
            self.assertEqual(result["missing"]["task_count"], 1)


if __name__ == "__main__":
    unittest.main()
