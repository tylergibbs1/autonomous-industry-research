from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    ROOT
    / "skills"
    / "research"
    / "autonomous-industry-research"
    / "scripts"
    / "research_harness.py"
)
SPEC = importlib.util.spec_from_file_location("research_harness", HARNESS_PATH)
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


class SafetyGateTests(unittest.TestCase):
    def test_low_risk_domain_is_allowed(self) -> None:
        self.assertEqual(harness.risk_gate("energy storage")["level"], "allowed")

    def test_high_stakes_domain_requires_review(self) -> None:
        self.assertEqual(harness.risk_gate("biotechnology")["level"], "human_review")

    def test_prohibited_request_is_blocked(self) -> None:
        gate = harness.risk_gate("biotechnology", "optimize pathogen enhancement")
        self.assertEqual(gate["level"], "blocked")


class ScoringTests(unittest.TestCase):
    def test_score_preserves_full_scale(self) -> None:
        scores = {name: 5 for name in harness.WEIGHTS}
        self.assertEqual(harness.score_opportunity(scores, 0), 5.0)

    def test_score_applies_risk_penalty(self) -> None:
        scores = {name: 4 for name in harness.WEIGHTS}
        self.assertEqual(harness.score_opportunity(scores, 1.25), 2.75)

    def test_invalid_component_is_rejected(self) -> None:
        with self.assertRaises(harness.HarnessError):
            harness.score_opportunity({name: 6 for name in harness.WEIGHTS}, 0)


class RunTests(unittest.TestCase):
    def test_scaffold_accepts_any_low_risk_industry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            run_dir = Path(temp_name) / "agriculture-run"
            manifest = harness.create_scaffold("agriculture", "soil monitoring", run_dir)
            self.assertEqual(manifest["industry"], "agriculture")
            self.assertTrue((run_dir / "research-plan.json").exists())
            self.assertEqual(json.loads((run_dir / "opportunities.json").read_text())["opportunities"], [])

    def test_nonempty_run_directory_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            run_dir = Path(temp_name) / "run"
            run_dir.mkdir()
            (run_dir / "user-file.txt").write_text("preserve me")
            with self.assertRaises(harness.HarnessError):
                harness.create_scaffold("energy", "", run_dir)
            self.assertEqual((run_dir / "user-file.txt").read_text(), "preserve me")

    def test_registered_experiment_is_deterministic(self) -> None:
        spec = harness.build_experiment_spec()
        first = harness.run_toy_energy_experiment(spec)
        second = harness.run_toy_energy_experiment(spec)
        self.assertEqual(first["result_digest"], second["result_digest"])
        self.assertEqual(first["primary_metric"], second["primary_metric"])

    def test_unregistered_experiment_is_rejected(self) -> None:
        spec = harness.build_experiment_spec()
        spec["experiment_id"] = "arbitrary-code"
        with self.assertRaises(harness.HarnessError):
            harness.run_toy_energy_experiment(spec)

    def test_child_process_replay_preserves_scientific_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp_dir = Path(temp_name)
            spec_path = temp_dir / "spec.json"
            harness.write_json(spec_path, harness.build_experiment_spec())
            first = harness.execute_registered_experiment(spec_path, temp_dir / "first.json", temp_dir / "first.log")
            second = harness.execute_registered_experiment(spec_path, temp_dir / "second.json", temp_dir / "second.log")
            self.assertEqual(first["result_digest"], second["result_digest"])
            self.assertEqual(first["primary_metric"], second["primary_metric"])

    def test_demo_completes_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            run_dir = Path(temp_name) / "demo"
            result = harness.run_demo("energy", "workflow demonstration", run_dir)
            self.assertTrue(result["audit"]["passed"])
            self.assertEqual(result["manifest"]["status"], "completed_demo")
            self.assertTrue((run_dir / "findings.md").exists())
            self.assertEqual(harness.audit_run(run_dir)["passed"], True)

            (run_dir / "findings.md").write_text("tampered", encoding="utf-8")
            self.assertEqual(harness.audit_run(run_dir)["passed"], False)

    def test_demo_will_not_bypass_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            with self.assertRaises(harness.HarnessError):
                harness.run_demo("healthcare", "workflow demonstration", Path(temp_name) / "demo")


if __name__ == "__main__":
    unittest.main()
