import importlib.util
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "project_sync.py"
SPEC = importlib.util.spec_from_file_location("project_sync", MODULE_PATH)
assert SPEC is not None
project_sync = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_sync
assert SPEC.loader is not None
SPEC.loader.exec_module(project_sync)


class ProjectSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.change_dir = self.repo_root / "openspec" / "changes" / "example-change"
        (self.change_dir / "specs" / "feature-a").mkdir(parents=True)
        (self.change_dir / ".openspec.yaml").write_text(
            "schema: spec-driven\ncreated: 2026-04-12\nproject_item_id: PVTI_123\n",
            encoding="utf-8",
        )
        (self.change_dir / "proposal.md").write_text("## Why\n\nProposal body.\n", encoding="utf-8")
        (self.change_dir / "design.md").write_text("## Design\n\nDesign body.\n", encoding="utf-8")
        (self.change_dir / "tasks.md").write_text("## Tasks\n\n- [ ] Task one\n", encoding="utf-8")
        (self.change_dir / "overview.md").write_text("Overview.\n", encoding="utf-8")
        (self.change_dir / "specs" / "feature-a" / "spec.md").write_text("Spec body.\n", encoding="utf-8")
        self.record = project_sync.find_change_record(self.repo_root, "example-change")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discover_artifacts_includes_specs_and_supplemental(self):
        inventory = project_sync.discover_artifacts(self.change_dir, self.repo_root)
        self.assertEqual(inventory.core["proposal"], "openspec/changes/example-change/proposal.md")
        self.assertEqual(inventory.specs, ["openspec/changes/example-change/specs/feature-a/spec.md"])
        self.assertEqual(inventory.supplemental, ["openspec/changes/example-change/overview.md"])

    def test_build_body_renders_managed_sections_and_preserves_manual_notes(self):
        ordering_metadata = project_sync.OrderingMetadata(
            priority="P0",
            surface="frontend",
            category="foundation",
            suggested_sequence=10,
            dependencies=["dependency-a"],
            sources=["override"],
        )
        existing = (
            f"{project_sync.MANAGED_BEGIN}\nlegacy\n{project_sync.MANAGED_END}\n\n"
            f"{project_sync.MANUAL_BEGIN}\n## Notas manuales\nKeep me\n{project_sync.MANUAL_END}\n"
        )
        body, truncated = project_sync.build_body(self.record, self.repo_root, "Ready", ordering_metadata, existing)
        self.assertFalse(truncated)
        self.assertIn("- Cambio: `example-change`", body)
        self.assertIn("## Inventario de artefactos", body)
        self.assertIn("## Propuesta", body)
        self.assertIn("## Diseno", body)
        self.assertIn("## Tareas", body)
        self.assertIn("Keep me", body)
        self.assertIn("## Metadatos de orden sugeridos", body)
        self.assertIn("- Suggested sequence: `10`", body)

    def test_build_body_truncates_design_before_tasks(self):
        (self.change_dir / "design.md").write_text("X\n" * 50000, encoding="utf-8")
        body, truncated = project_sync.build_body(self.record, self.repo_root, "In progress", None, None)
        self.assertTrue(truncated)
        self.assertIn(project_sync.TRUNCATION_NOTE, body)
        self.assertIn("Consulta `openspec/changes/example-change/design.md`.", body)
        self.assertIn("- [ ] Task one", body)

    def test_build_body_normalizes_malformed_task_checkboxes(self):
        (self.change_dir / "tasks.md").write_text(
            "## Tasks\n\n- [] malformed open\n- [X] completed uppercase\n* [] malformed star\n",
            encoding="utf-8",
        )

        body, truncated = project_sync.build_body(self.record, self.repo_root, "Ready", None, None)

        self.assertFalse(truncated)
        self.assertIn("- [ ] malformed open", body)
        self.assertIn("- [x] completed uppercase", body)
        self.assertIn("* [ ] malformed star", body)

    def test_merge_manual_notes_replaces_existing_ordering_block(self):
        manual_notes = (
            "## Notas manuales\nKeep me\n\n"
            f"{project_sync.ORDERING_BEGIN}\nlegacy\n{project_sync.ORDERING_END}"
        )
        ordering_metadata = project_sync.OrderingMetadata(
            priority="P1",
            surface="frontend",
            category="feature",
            suggested_sequence=30,
            dependencies=[],
            sources=["heuristic"],
        )

        merged = project_sync.merge_manual_notes(manual_notes, ordering_metadata)

        self.assertIn("Keep me", merged)
        self.assertIn("Suggested sequence: `30`", merged)
        self.assertNotIn("legacy", merged)

    def test_draft_title_uses_spanish_prefix(self):
        self.assertEqual(project_sync.draft_title("example-change"), "[adrotech] OpenSpec cambio: example change")

    def test_archived_change_name_strips_date_prefix(self):
        self.assertEqual(
            project_sync.archived_change_name("2026-04-11-harden-release-workflow-preflight"),
            "harden-release-workflow-preflight",
        )

    def test_recovery_command_preserves_requested_flags(self):
        command = project_sync.build_recovery_command(
            "example-change",
            "In progress",
            "P1",
            "M",
            True,
            False,
            True,
            "PVTI_override",
        )
        self.assertIn("--change example-change", command)
        self.assertIn('--status "In progress"', command)
        self.assertIn("--priority P1", command)
        self.assertIn("--size M", command)
        self.assertIn("--project-item-id PVTI_override", command)
        self.assertIn("--dry-run", command)
        self.assertIn("--no-persist-mapping", command)
        self.assertIn("--print-body", command)

    def test_non_draft_item_marks_body_sync_pending_but_updates_fields(self):
        with mock.patch.object(
            project_sync,
            "fetch_project_item",
            return_value={"type": "ISSUE", "content": {"__typename": "Issue", "id": "ISSUE_1", "body": ""}},
        ), mock.patch.object(project_sync, "update_single_select") as update_single_select:
            result = project_sync.sync_change(
                self.record,
                self.repo_root,
                {"example-change": project_sync.OrderingMetadata("P1", "frontend", "feature", 20, [], ["override"])},
                "Ready",
                None,
                None,
                False,
                True,
                None,
                False,
            )

        self.assertEqual(result["body_sync"]["status"], "sync_pending")
        self.assertEqual(result["field_updates"][0]["status"], "updated")
        self.assertEqual(update_single_select.call_count, 2)

    def test_field_failure_does_not_hide_successful_body_update(self):
        with mock.patch.object(
            project_sync,
            "fetch_project_item",
            return_value={
                "type": "DRAFT_ISSUE",
                "content": {"__typename": "DraftIssue", "id": "DI_1", "body": "old body"},
            },
        ), mock.patch.object(project_sync, "update_draft_issue") as update_draft_issue, mock.patch.object(
            project_sync,
            "update_single_select",
            side_effect=project_sync.SyncError("field update failed"),
        ):
            result = project_sync.sync_change(
                self.record,
                self.repo_root,
                {"example-change": project_sync.OrderingMetadata("P1", "frontend", "feature", 20, [], ["override"])},
                "Ready",
                None,
                None,
                False,
                True,
                None,
                False,
            )

        self.assertEqual(result["body_sync"]["status"], "updated")
        self.assertEqual(result["field_updates"][0]["status"], "failed")
        update_draft_issue.assert_called_once()

    def test_body_update_failure_returns_sync_pending_with_recovery(self):
        with mock.patch.object(
            project_sync,
            "fetch_project_item",
            return_value={
                "type": "DRAFT_ISSUE",
                "content": {"__typename": "DraftIssue", "id": "DI_1", "body": "old body"},
            },
        ), mock.patch.object(
            project_sync,
            "update_draft_issue",
            side_effect=project_sync.SyncError("body update failed"),
        ), mock.patch.object(project_sync, "update_single_select") as update_single_select:
            result = project_sync.sync_change(
                self.record,
                self.repo_root,
                {"example-change": project_sync.OrderingMetadata("P1", "frontend", "feature", 20, [], ["override"])},
                "Ready",
                None,
                None,
                False,
                True,
                None,
                False,
            )

        self.assertEqual(result["body_sync"]["status"], "sync_pending")
        self.assertEqual(result["body_sync"]["action"], "update")
        self.assertIn("recovery", result["body_sync"])
        self.assertEqual(result["field_updates"][0]["status"], "updated")
        self.assertEqual(update_single_select.call_count, 2)

    def test_create_failure_returns_sync_pending_and_marks_field_updates_pending(self):
        metadata_path = self.change_dir / ".openspec.yaml"
        metadata_path.write_text("schema: spec-driven\ncreated: 2026-04-12\n", encoding="utf-8")
        record_without_mapping = project_sync.find_change_record(self.repo_root, "example-change")

        with mock.patch.object(
            project_sync,
            "create_draft_issue",
            side_effect=project_sync.SyncError("create failed"),
        ):
            result = project_sync.sync_change(
                record_without_mapping,
                self.repo_root,
                {"example-change": project_sync.OrderingMetadata("P1", "frontend", "feature", 20, [], ["override"])},
                "Ready",
                None,
                "M",
                False,
                True,
                None,
                False,
            )

        self.assertEqual(result["body_sync"]["status"], "sync_pending")
        self.assertEqual(result["body_sync"]["action"], "create")
        self.assertEqual(result["project_item_id"], None)
        self.assertEqual(result["field_updates"], [])

    def test_sync_change_derives_priority_when_not_explicitly_requested(self):
        with mock.patch.object(
            project_sync,
            "fetch_project_item",
            return_value={
                "type": "DRAFT_ISSUE",
                "content": {"__typename": "DraftIssue", "id": "DI_1", "body": "old body"},
            },
        ), mock.patch.object(project_sync, "update_draft_issue"), mock.patch.object(
            project_sync,
            "update_single_select",
        ) as update_single_select:
            result = project_sync.sync_change(
                self.record,
                self.repo_root,
                {"example-change": project_sync.OrderingMetadata("P0", "frontend", "foundation", 10, [], ["override"])},
                None,
                None,
                None,
                False,
                True,
                None,
                False,
            )

        self.assertEqual(result["field_updates"][0]["field"], "priority")
        self.assertEqual(result["field_updates"][0]["value"], "P0")
        self.assertEqual(result["field_updates"][0]["source"], "derived")
        update_single_select.assert_called_once()

    def test_backfill_defaults_to_active_only_and_can_include_archived(self):
        archive_dir = self.repo_root / "openspec" / "changes" / "archive" / "2026-04-11-archived-change"
        archive_dir.mkdir(parents=True)
        (archive_dir / ".openspec.yaml").write_text(
            "schema: spec-driven\ncreated: 2026-04-11\nproject_item_id: PVTI_ARCHIVE\n",
            encoding="utf-8",
        )

        args_default = Namespace(backfill=True, active_only=False, include_archived=False, change=None)
        args_archived = Namespace(backfill=True, active_only=False, include_archived=True, change=None)

        default_records = project_sync.choose_records(self.repo_root, args_default)
        archived_records = project_sync.choose_records(self.repo_root, args_archived)

        self.assertEqual([record.change_name for record in default_records], ["example-change"])
        self.assertEqual(
            [record.change_name for record in archived_records],
            ["example-change", "archived-change"],
        )

    def test_build_ordering_metadata_map_uses_dependency_graph(self):
        foundation_dir = self.repo_root / "openspec" / "changes" / "foundation-change"
        feature_dir = self.repo_root / "openspec" / "changes" / "feature-change"
        foundation_dir.mkdir(parents=True)
        feature_dir.mkdir(parents=True)
        (foundation_dir / ".openspec.yaml").write_text("schema: spec-driven\ncreated: 2026-04-12\n", encoding="utf-8")
        (feature_dir / ".openspec.yaml").write_text("schema: spec-driven\ncreated: 2026-04-12\n", encoding="utf-8")
        (foundation_dir / "proposal.md").write_text("Frontend foundation.\n", encoding="utf-8")
        (feature_dir / "proposal.md").write_text("Depends on `foundation-change`.\n", encoding="utf-8")

        metadata_map = project_sync.build_ordering_metadata_map(self.repo_root)

        self.assertLess(
            metadata_map["foundation-change"].suggested_sequence,
            metadata_map["feature-change"].suggested_sequence,
        )
        self.assertEqual(metadata_map["feature-change"].dependencies, ["foundation-change"])


if __name__ == "__main__":
    unittest.main()
