#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "skills" / "research" / "autonomous-industry-research" / "scripts" / "research_harness.py"
SPEC = importlib.util.spec_from_file_location("research_harness", HARNESS_PATH)
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


def main() -> int:
    cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
    route_results = []
    for case in cases:
        actual = harness.risk_gate(case["industry"], case["question"])["level"]
        route_results.append({"id": case["id"], "expected": case["expected_route"], "actual": actual, "passed": actual == case["expected_route"]})

    with tempfile.TemporaryDirectory() as temp_name:
        run_dir = Path(temp_name) / "demo"
        demo = harness.run_demo("energy", "evaluation workflow", run_dir)
        workflow = {
            "audit_passed": demo["audit"]["passed"],
            "artifacts_present": all(
                (run_dir / name).exists()
                for name in (
                    "manifest.json",
                    "research-plan.json",
                    "evidence.jsonl",
                    "opportunities.json",
                    "hypotheses.json",
                    "experiment-spec.json",
                    "experiment-results.json",
                    "experiment.log",
                    "findings.md",
                    "audit.json",
                )
            ),
            "primary_metric_finite": all(
                value == value and abs(value) != float("inf")
                for key, value in demo["primary_metric"].items()
                if key != "name"
            ),
        }
    workflow["passed"] = all(workflow.values())
    output = {
        "routing": route_results,
        "routing_accuracy": sum(item["passed"] for item in route_results) / len(route_results),
        "workflow": workflow,
    }
    output["passed"] = output["routing_accuracy"] == 1.0 and workflow["passed"]
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
