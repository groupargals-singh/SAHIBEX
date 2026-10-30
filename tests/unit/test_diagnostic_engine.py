from pathlib import Path
import tempfile
import unittest

from core.diagnostics.diagnostic_engine import collect_diagnostics


class DiagnosticEngineTests(unittest.TestCase):
    def test_report_is_read_only_and_marks_source_discovery_not_live_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "core/brain").mkdir(parents=True)
            (root / "verification").mkdir()
            (root / "logs").mkdir()
            (root / "core/brain/master_brain.py").write_text("class MasterBrain: pass\n")
            report = collect_diagnostics(root, now=1234)
            self.assertEqual(report["mode"], "READ_ONLY")
            self.assertEqual(report["generated_at_unix"], 1234)
            master = next(item for item in report["brains"] if item["name"] == "Master Brain")
            self.assertEqual(master["status"], "DISCOVERED_NOT_LIVE_TESTED")
            self.assertTrue(master["file_present"])
            self.assertIn("does not prove", " ".join(report["limitations"]))

    def test_real_repository_discovers_all_internal_roles_and_registrations(self):
        from core.diagnostics.diagnostic_engine import ROOT
        report = collect_diagnostics(ROOT)
        self.assertEqual(report["role_summary"]["defined_roles"], 61)
        self.assertEqual(report["role_summary"]["unique_role_ids"], 61)
        self.assertEqual(report["role_summary"]["registered_handlers"], 61)
        self.assertEqual(report["role_summary"]["unregistered_handlers"], 0)
        self.assertFalse(report["role_summary"]["runtime_invocation_verified"])
        self.assertTrue(all(item["status"] == "HANDLER_REGISTERED_NOT_FUNCTION_TESTED"
                            for item in report["internal_roles"]))
        self.assertTrue(all(edge["live_traced"] is False for edge in report["data_flow_edges"]))

    def test_log_traceback_extracts_source_file_line_and_redacts_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "logs").mkdir()
            (root / "logs/runtime.log").write_text(
                'Traceback (most recent call last):\n'
                '  File "/tmp/sahibex/core/brain/example.py", line 42, in run\n'
                'RuntimeError: failed with token=TOPSECRET\n'
            )
            report = collect_diagnostics(root, now=1234)
            self.assertGreaterEqual(report["summary"]["recent_error_records"], 1)
            item = next(item for item in report["errors"] if item["source_line"] == 42)
            self.assertEqual(item["source_file"], "/tmp/sahibex/core/brain/example.py")
            self.assertEqual(item["function"], "run")
            self.assertNotIn("TOPSECRET", item["message"])


if __name__ == "__main__":
    unittest.main()
