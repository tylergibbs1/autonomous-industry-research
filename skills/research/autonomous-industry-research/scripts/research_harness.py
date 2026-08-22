#!/usr/bin/env python3
"""Deterministic scaffold and safe toy experiment runner for industry research.

The harness intentionally has no model or web dependency. Agent hosts perform live
research; this module owns durable artifacts, scoring, a registered demo experiment,
and reproducibility audits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"
REGISTERED_EXPERIMENTS = {"toy-energy-storage-v1"}
WEIGHTS = {
    "public_benefit": 0.25,
    "decision_value": 0.15,
    "neglectedness": 0.15,
    "computational_tractability": 0.15,
    "evidence_readiness": 0.10,
    "time_to_impact": 0.10,
    "equity_access": 0.10,
}

BLOCK_PATTERNS = (
    "pathogen enhancement",
    "increase transmissibility",
    "evade immune response",
    "toxin optimization",
    "wet-lab protocol",
    "explosive synthesis",
    "weapon design",
    "credential theft",
    "ransomware",
    "destructive payload",
    "autonomous trading",
)
REVIEW_PATTERNS = (
    "biotechnology",
    "healthcare",
    "clinical",
    "patient",
    "genomic",
    "chemistry",
    "nuclear",
    "defense",
    "critical infrastructure",
    "finance",
)

DEMO_EVIDENCE = (
    {
        "claim_id": "fixture-tech-1",
        "claim": "The illustrative system contains variable renewable supply, demand, and storage.",
        "source_url": "fixture://toy-energy-system/technology",
        "source_title": "Illustrative technology fixture",
        "publisher": "autonomous-industry-research demo",
        "published_at": None,
        "source_type": "illustrative_fixture",
        "support": "supported",
        "quote_or_locator": "Embedded deterministic fixture",
        "lane": "technology",
        "notes": "Not external evidence and not a statement about the real energy industry.",
    },
    {
        "claim_id": "fixture-impact-1",
        "claim": "The toy decision objective is to reduce unmet simulated demand.",
        "source_url": "fixture://toy-energy-system/impact",
        "source_title": "Illustrative impact fixture",
        "publisher": "autonomous-industry-research demo",
        "published_at": None,
        "source_type": "illustrative_fixture",
        "support": "supported",
        "quote_or_locator": "Embedded deterministic fixture",
        "lane": "humanitarian-need",
        "notes": "The metric is a demonstration choice, not a validated social-impact model.",
    },
    {
        "claim_id": "fixture-gap-1",
        "claim": "Storage capacity is an adjustable parameter in the toy simulation.",
        "source_url": "fixture://toy-energy-system/gap",
        "source_title": "Illustrative gap fixture",
        "publisher": "autonomous-industry-research demo",
        "published_at": None,
        "source_type": "illustrative_fixture",
        "support": "supported",
        "quote_or_locator": "Embedded deterministic fixture",
        "lane": "unresolved-problems",
        "notes": "This creates a testable toy hypothesis but does not establish a real research gap.",
    },
    {
        "claim_id": "fixture-risk-1",
        "claim": "Toy simulations can mislead when their assumptions are treated as real-world evidence.",
        "source_url": "fixture://toy-energy-system/risk",
        "source_title": "Illustrative limitations fixture",
        "publisher": "autonomous-industry-research demo",
        "published_at": None,
        "source_type": "illustrative_fixture",
        "support": "supported",
        "quote_or_locator": "Embedded deterministic fixture",
        "lane": "failure-modes",
        "notes": "This limitation is carried into the final report.",
    },
)


class HarnessError(RuntimeError):
    """A user-correctable harness error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_json(value).encode("utf-8"))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(canonical_json(record) + "\n")


def risk_gate(industry: str, question: str = "") -> dict[str, Any]:
    text = f"{industry} {question}".lower()
    blocked = sorted({term for term in BLOCK_PATTERNS if term in text})
    review = sorted({term for term in REVIEW_PATTERNS if term in text})
    if blocked:
        level = "blocked"
        reason = "The request matches a prohibited operational research category."
    elif review:
        level = "human_review"
        reason = "The domain is high-stakes; literature work may proceed, but experiment execution needs review."
    else:
        level = "allowed"
        reason = "No high-stakes or prohibited category was detected by the conservative lexical gate."
    return {
        "level": level,
        "reason": reason,
        "matched_block_terms": blocked,
        "matched_review_terms": review,
        "limitations": "This lexical gate is defense in depth, not a substitute for model and human review.",
    }


def score_opportunity(scores: dict[str, float], risk_penalty: float) -> float:
    missing = sorted(set(WEIGHTS) - set(scores))
    extra = sorted(set(scores) - set(WEIGHTS))
    if missing or extra:
        raise HarnessError(f"Invalid score keys; missing={missing}, extra={extra}")
    for name, value in scores.items():
        if not isinstance(value, (int, float)) or not 0 <= value <= 5:
            raise HarnessError(f"Score {name} must be a number from 0 to 5")
    if not isinstance(risk_penalty, (int, float)) or not 0 <= risk_penalty <= 2:
        raise HarnessError("risk_penalty must be a number from 0 to 2")
    weighted = sum(scores[name] * WEIGHTS[name] for name in WEIGHTS)
    return round(weighted - risk_penalty, 4)


def append_event(run_dir: Path, actor: str, action: str, inputs: Any, output: Any) -> None:
    path = run_dir / "events.jsonl"
    sequence = 1
    if path.exists():
        with path.open("r", encoding="utf-8") as existing:
            sequence = sum(1 for _ in existing) + 1
    event = {
        "sequence": sequence,
        "timestamp": utc_now(),
        "actor": actor,
        "action": action,
        "input_digest": digest_value(inputs),
        "output_digest": digest_value(output),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(event) + "\n")


def ensure_new_directory(run_dir: Path) -> None:
    if run_dir.exists() and any(run_dir.iterdir()):
        raise HarnessError(f"Run directory is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)


def create_scaffold(industry: str, question: str, run_dir: Path) -> dict[str, Any]:
    industry = industry.strip()
    question = question.strip()
    if not industry:
        raise HarnessError("industry must not be empty")
    ensure_new_directory(run_dir)
    safety = risk_gate(industry, question)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "industry": industry,
        "question": question or f"Which research gaps in {industry} could produce high public benefit?",
        "research_lanes": [
            {"id": "frontier", "role": "Read-only frontier scout", "stop": "Budget reached or two dry rounds"},
            {"id": "technology", "role": "Read-only technology scout", "stop": "Budget reached or two dry rounds"},
            {"id": "deployment", "role": "Read-only deployment scout", "stop": "Budget reached or two dry rounds"},
            {"id": "humanitarian-need", "role": "Read-only impact scout", "stop": "Budget reached or two dry rounds"},
            {"id": "failure-modes", "role": "Read-only safety and skeptic scout", "stop": "Budget reached or two dry rounds"},
        ],
        "budgets": {
            "max_parallel_workers": 5,
            "max_searches_per_lane": 8,
            "max_shortlisted_sources": 40,
            "max_experiment_attempts": 1,
        },
        "barriers": ["evidence_deduplication", "opportunity_ranking", "final_synthesis"],
        "single_writer_stages": ["curation", "scoring", "experiment_execution", "reporting"],
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "harness_version": VERSION,
        "created_at": utc_now(),
        "industry": industry,
        "question": plan["question"],
        "status": {
            "allowed": "initialized",
            "human_review": "awaiting_human_review",
            "blocked": "blocked",
        }[safety["level"]],
        "safety_gate": safety,
        "artifact_digests": {},
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "research-plan.json", plan)
    write_jsonl(run_dir / "evidence.jsonl", [])
    write_json(run_dir / "opportunities.json", {"schema_version": SCHEMA_VERSION, "opportunities": []})
    write_json(run_dir / "hypotheses.json", {"schema_version": SCHEMA_VERSION, "hypotheses": []})
    append_event(run_dir, "coordinator", "initialize_run", {"industry": industry, "question": question}, manifest)
    return manifest


def demo_opportunities() -> list[dict[str, Any]]:
    raw = [
        {
            "id": "opp-storage-sizing",
            "title": "Stress-test storage sizing under variable synthetic supply",
            "gap_status": "illustrative_only",
            "scores": {
                "public_benefit": 4.0,
                "decision_value": 4.5,
                "neglectedness": 2.0,
                "computational_tractability": 5.0,
                "evidence_readiness": 3.5,
                "time_to_impact": 3.5,
                "equity_access": 3.0,
            },
            "risk_penalty": 0.25,
            "rationale": "A safe paired simulation can demonstrate the workflow, but fixture evidence cannot establish a real gap.",
            "supporting_claim_ids": ["fixture-tech-1", "fixture-gap-1", "fixture-impact-1"],
        },
        {
            "id": "opp-demand-response",
            "title": "Compare synthetic demand-response policies",
            "gap_status": "illustrative_only",
            "scores": {
                "public_benefit": 3.5,
                "decision_value": 3.5,
                "neglectedness": 1.5,
                "computational_tractability": 4.5,
                "evidence_readiness": 2.5,
                "time_to_impact": 3.0,
                "equity_access": 3.5,
            },
            "risk_penalty": 0.25,
            "rationale": "Computationally tractable, but less directly supported by the fixture.",
            "supporting_claim_ids": ["fixture-impact-1", "fixture-risk-1"],
        },
        {
            "id": "opp-grid-control",
            "title": "Autonomously control a real grid",
            "gap_status": "rejected",
            "scores": {
                "public_benefit": 4.0,
                "decision_value": 5.0,
                "neglectedness": 1.0,
                "computational_tractability": 0.0,
                "evidence_readiness": 0.0,
                "time_to_impact": 0.5,
                "equity_access": 1.0,
            },
            "risk_penalty": 2.0,
            "rationale": "Rejected because real-world actuation is outside the safe experiment boundary.",
            "supporting_claim_ids": ["fixture-risk-1"],
        },
    ]
    for item in raw:
        item["weighted_score"] = score_opportunity(item["scores"], item["risk_penalty"])
    return sorted(raw, key=lambda item: item["weighted_score"], reverse=True)


def build_experiment_spec() -> dict[str, Any]:
    seeds = list(range(101, 131))
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "toy-energy-storage-v1",
        "experiment_version": "1",
        "preregistered_at": utc_now(),
        "hypothesis_id": "hyp-storage-capacity",
        "environment": "Synthetic 168-hour demand, solar, and wind trajectories",
        "comparator": {"storage_capacity_mwh": 24.0, "power_mw": 8.0, "round_trip_efficiency": 0.90},
        "intervention": {"storage_capacity_mwh": 48.0, "power_mw": 8.0, "round_trip_efficiency": 0.90},
        "seeds": seeds,
        "replications": len(seeds),
        "primary_metric": "relative_reduction_unmet_mwh",
        "minimum_effect": 0.15,
        "secondary_metrics": ["mean_unmet_mwh", "mean_curtailed_mwh", "reliability"],
        "analysis": "Paired mean difference with normal-approximation 95% confidence interval across fixed seeds.",
        "falsification_rule": "Falsify if mean relative reduction is below 0.15 or any output is non-finite.",
        "abort_criteria": ["timeout", "non-finite metric", "unregistered experiment", "worker failure"],
        "resource_limits": {"wall_seconds": 20, "cpu_seconds": 15, "memory_mb": 512, "file_size_mb": 10},
        "execution_policy": {
            "code": "registered_only",
            "network": "not_used; hardened isolation requires container/microVM",
            "secrets": "cleared_child_environment",
            "external_writes": "none",
        },
        "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation()},
    }


def generate_scenario(seed: int, hours: int = 168) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    demand: list[float] = []
    renewable: list[float] = []
    wind_state = rng.uniform(0.2, 0.8)
    for hour in range(hours):
        day_phase = 2 * math.pi * (hour % 24) / 24
        demand_value = 10.0 + 2.2 * math.sin(day_phase - 0.8) + rng.gauss(0, 0.75)
        solar = max(0.0, 9.0 * math.sin(math.pi * ((hour % 24) - 6) / 12))
        wind_state = min(1.0, max(0.0, 0.82 * wind_state + 0.18 * rng.random()))
        wind = 5.5 * wind_state
        cloud = 0.55 + 0.45 * rng.random()
        demand.append(max(1.0, demand_value))
        renewable.append(max(0.0, solar * cloud + wind))
    return demand, renewable


def dispatch_scenario(
    demand: list[float], renewable: list[float], capacity: float, power: float, efficiency: float
) -> dict[str, float]:
    state = 0.5 * capacity
    charge_efficiency = math.sqrt(efficiency)
    discharge_efficiency = math.sqrt(efficiency)
    unmet = 0.0
    curtailed = 0.0
    served = 0.0
    total_demand = sum(demand)
    for load, supply in zip(demand, renewable):
        balance = supply - load
        if balance >= 0:
            input_energy = min(balance, power, (capacity - state) / charge_efficiency)
            state += input_energy * charge_efficiency
            curtailed += balance - input_energy
            served += load
        else:
            deficit = -balance
            output_energy = min(deficit, power, state * discharge_efficiency)
            state -= output_energy / discharge_efficiency
            unmet += deficit - output_energy
            served += load - (deficit - output_energy)
    return {
        "unmet_mwh": unmet,
        "curtailed_mwh": curtailed,
        "reliability": served / total_demand,
        "ending_state_mwh": state,
    }


def mean_ci(values: list[float]) -> dict[str, float]:
    mean = statistics.fmean(values)
    if len(values) < 2:
        return {"mean": mean, "lower_95": mean, "upper_95": mean}
    stderr = statistics.stdev(values) / math.sqrt(len(values))
    return {"mean": mean, "lower_95": mean - 1.96 * stderr, "upper_95": mean + 1.96 * stderr}


def run_toy_energy_experiment(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("experiment_id") != "toy-energy-storage-v1":
        raise HarnessError("Unregistered experiment")
    seeds = spec.get("seeds")
    if not isinstance(seeds, list) or not seeds or len(seeds) > 1000 or not all(isinstance(seed, int) for seed in seeds):
        raise HarnessError("seeds must be a non-empty list of at most 1000 integers")
    comparator = spec["comparator"]
    intervention = spec["intervention"]
    paired: list[dict[str, Any]] = []
    relative_reductions: list[float] = []
    absolute_reductions: list[float] = []
    for seed in seeds:
        demand, renewable = generate_scenario(seed)
        baseline = dispatch_scenario(
            demand,
            renewable,
            float(comparator["storage_capacity_mwh"]),
            float(comparator["power_mw"]),
            float(comparator["round_trip_efficiency"]),
        )
        candidate = dispatch_scenario(
            demand,
            renewable,
            float(intervention["storage_capacity_mwh"]),
            float(intervention["power_mw"]),
            float(intervention["round_trip_efficiency"]),
        )
        absolute = baseline["unmet_mwh"] - candidate["unmet_mwh"]
        relative = absolute / baseline["unmet_mwh"] if baseline["unmet_mwh"] > 0 else 0.0
        absolute_reductions.append(absolute)
        relative_reductions.append(relative)
        paired.append({"seed": seed, "comparator": baseline, "intervention": candidate, "relative_reduction": relative})
    all_numbers = [
        number
        for row in paired
        for group in (row["comparator"], row["intervention"])
        for number in group.values()
    ] + relative_reductions
    if not all(math.isfinite(number) for number in all_numbers):
        raise HarnessError("Experiment produced a non-finite metric")
    primary = mean_ci(relative_reductions)
    effect_passed = primary["mean"] >= float(spec["minimum_effect"])
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": spec["experiment_id"],
        "spec_digest": digest_value(spec),
        "replications": len(paired),
        "primary_metric": {"name": spec["primary_metric"], **primary},
        "absolute_reduction_unmet_mwh": mean_ci(absolute_reductions),
        "comparator_means": {
            key: statistics.fmean(row["comparator"][key] for row in paired)
            for key in ("unmet_mwh", "curtailed_mwh", "reliability")
        },
        "intervention_means": {
            key: statistics.fmean(row["intervention"][key] for row in paired)
            for key in ("unmet_mwh", "curtailed_mwh", "reliability")
        },
        "hypothesis_threshold": spec["minimum_effect"],
        "hypothesis_result": "passes_toy_threshold" if effect_passed else "falsified_in_toy_model",
        "paired_runs": paired,
        "limitations": [
            "Synthetic trajectories are not calibrated to a real grid.",
            "The dispatch policy is deliberately simple.",
            "The result supports only a claim about this toy simulation.",
        ],
    }
    result["result_digest"] = digest_value(result)
    return result


def _apply_resource_limits(spec: dict[str, Any]) -> None:
    try:
        import resource

        limits = spec["resource_limits"]
        resource.setrlimit(resource.RLIMIT_CPU, (int(limits["cpu_seconds"]), int(limits["cpu_seconds"])))
        memory = int(limits["memory_mb"]) * 1024 * 1024
        if sys.platform.startswith("linux"):
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        elif hasattr(resource, "RLIMIT_DATA"):
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))
        file_size = int(limits["file_size_mb"]) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_size, file_size))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except (ImportError, KeyError, OSError, ValueError):
        pass


def execute_registered_experiment(spec_path: Path, output_path: Path, log_path: Path) -> dict[str, Any]:
    spec = read_json(spec_path)
    experiment_id = spec.get("experiment_id")
    if experiment_id not in REGISTERED_EXPERIMENTS:
        raise HarnessError(f"Experiment is not registered: {experiment_id!r}")
    timeout = int(spec.get("resource_limits", {}).get("wall_seconds", 20))
    with tempfile.TemporaryDirectory(prefix="air-experiment-") as temp_name:
        temp_dir = Path(temp_name)
        frozen_spec = temp_dir / "experiment-spec.json"
        worker_output = temp_dir / "experiment-results.json"
        frozen_spec.write_bytes(spec_path.read_bytes())
        env = {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONHASHSEED": "0",
        }
        command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--spec", str(frozen_spec), "--output", str(worker_output)]
        recorded_command = [
            "python3",
            "research_harness.py",
            "_worker",
            "--spec",
            "<sandbox>/experiment-spec.json",
            "--output",
            "<sandbox>/experiment-results.json",
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                preexec_fn=(lambda: _apply_resource_limits(spec)) if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired as error:
            log_path.write_text((error.stdout or "") + "\nTIMEOUT\n" + (error.stderr or ""), encoding="utf-8")
            raise HarnessError(f"Experiment exceeded {timeout}s timeout") from error
        duration = time.monotonic() - started
        log_path.write_text(
            f"command={canonical_json(recorded_command)}\nexit_code={completed.returncode}\nduration_seconds={duration:.6f}\n"
            f"--- stdout ---\n{completed.stdout}\n--- stderr ---\n{completed.stderr}",
            encoding="utf-8",
        )
        if completed.returncode != 0 or not worker_output.exists():
            raise HarnessError(f"Experiment worker failed with exit code {completed.returncode}; see {log_path}")
        result = read_json(worker_output)
        result["execution"] = {
            "exit_code": completed.returncode,
            "duration_seconds": duration,
            "command": recorded_command,
            "environment_keys": sorted(env),
            "temporary_working_directory": True,
        }
        write_json(output_path, result)
        return result


def findings_markdown(run_dir: Path, opportunities: list[dict[str, Any]], spec: dict[str, Any], result: dict[str, Any]) -> str:
    top = opportunities[0]
    primary = result["primary_metric"]
    reproduction = (
        "python3 skills/research/autonomous-industry-research/scripts/research_harness.py "
        f"audit --run-dir {run_dir.as_posix()}"
    )
    return f"""# Illustrative energy research run

> This is a deterministic workflow demonstration. Its fixture records are not a current literature review and its result is not evidence about a real grid.

## Actionable finding

The highest-ranked illustrative opportunity was **{top['title']}** (score {top['weighted_score']:.2f}/5 after risk penalty). In the preregistered toy simulation, doubling energy capacity while holding power constant produced a mean relative reduction in unmet synthetic demand of **{primary['mean']:.1%}** (normal-approximation 95% CI {primary['lower_95']:.1%} to {primary['upper_95']:.1%}). The preregistered threshold was {spec['minimum_effect']:.0%}; the run result was `{result['hypothesis_result']}`.

## Interpretation

This validates the harness flow and deterministic experiment boundary. It does not validate a storage recommendation. A real study needs checked external evidence, calibrated data, realistic dispatch and cost models, multiple policy baselines, and stakeholder review.

## Skeptic review

- The opportunity is explicitly `illustrative_only`; fixture claims cannot establish neglectedness or novelty.
- Capacity was increased without a cost constraint, so improvement is unsurprising and not an optimization result.
- The normal confidence interval characterizes variation across synthetic seeds, not model-form uncertainty.
- The local runner executes only registered code, but hardened network isolation requires a container or microVM.

## Reproduce and audit

From the repository root:

```bash
{reproduction}
```

The frozen experiment is `experiment-spec.json`; raw paired outputs are in `experiment-results.json`; hashes are in `manifest.json`.
"""


def finalize_manifest(run_dir: Path, status: str) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    append_event(run_dir, "coordinator", "finalize_run", {"status": manifest.get("status")}, {"status": status})
    digests: dict[str, str] = {}
    for path in sorted(run_dir.iterdir()):
        if path.is_file() and path.name not in {"manifest.json", "audit.json"}:
            digests[path.name] = digest_file(path)
    manifest["status"] = status
    manifest["completed_at"] = utc_now()
    manifest["artifact_digests"] = digests
    write_json(manifest_path, manifest)
    return manifest


def audit_run(run_dir: Path, write: bool = False) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise HarnessError(f"Missing manifest: {manifest_path}")
    manifest = read_json(manifest_path)
    checks: list[dict[str, Any]] = []
    for name, expected in sorted(manifest.get("artifact_digests", {}).items()):
        path = run_dir / name
        actual = digest_file(path) if path.exists() else None
        checks.append({"check": f"digest:{name}", "passed": actual == expected, "expected": expected, "actual": actual})
    spec_path = run_dir / "experiment-spec.json"
    if spec_path.exists():
        spec = read_json(spec_path)
        checks.append(
            {
                "check": "registered_experiment",
                "passed": spec.get("experiment_id") in REGISTERED_EXPERIMENTS,
                "actual": spec.get("experiment_id"),
            }
        )
        checks.append(
            {
                "check": "fixed_seeds",
                "passed": isinstance(spec.get("seeds"), list) and len(spec["seeds"]) == spec.get("replications"),
                "actual": len(spec.get("seeds", [])),
            }
        )
    evidence_path = run_dir / "evidence.jsonl"
    evidence_valid = True
    evidence_count = 0
    if evidence_path.exists():
        for line in evidence_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            evidence_count += 1
            record = json.loads(line)
            evidence_valid = evidence_valid and all(
                record.get(key) for key in ("claim_id", "claim", "source_url", "source_title", "source_type", "support")
            )
    checks.append({"check": "evidence_schema_minimum", "passed": evidence_valid, "actual": evidence_count})
    passed = all(item["passed"] for item in checks)
    audit = {
        "schema_version": SCHEMA_VERSION,
        "audited_at": utc_now(),
        "run_dir": str(run_dir),
        "passed": passed,
        "checks": checks,
        "limitations": "Hashes detect post-finalization mutation; they do not establish scientific truth or hardened sandboxing.",
    }
    if write:
        write_json(run_dir / "audit.json", audit)
    return audit


def run_demo(industry: str, question: str, run_dir: Path) -> dict[str, Any]:
    manifest = create_scaffold(industry, question, run_dir)
    if manifest["safety_gate"]["level"] != "allowed":
        raise HarnessError("Demo execution requires an allowed safety-gate result")
    evidence = [{**item, "accessed_at": utc_now()} for item in DEMO_EVIDENCE]
    write_jsonl(run_dir / "evidence.jsonl", evidence)
    append_event(run_dir, "parallel_scouts", "collect_fixture_evidence", {"lanes": 4}, {"claims": len(evidence)})
    append_event(run_dir, "citation_verifier", "verify_fixture_claims", {"claims": len(evidence)}, {"supported": len(evidence)})

    opportunities = demo_opportunities()
    write_json(
        run_dir / "opportunities.json",
        {"schema_version": SCHEMA_VERSION, "rubric_weights": WEIGHTS, "opportunities": opportunities},
    )
    append_event(run_dir, "single_writer_synthesizer", "rank_opportunities", evidence, opportunities)

    hypothesis = {
        "id": "hyp-storage-capacity",
        "status": "preregistered",
        "statement": "In the toy 168-hour environment, increasing storage energy capacity from 24 to 48 MWh while holding power at 8 MW will reduce mean unmet demand by at least 15% across paired seeds.",
        "intervention": "48 MWh storage, 8 MW power",
        "comparator": "24 MWh storage, 8 MW power",
        "primary_metric": "relative_reduction_unmet_mwh",
        "minimum_effect": 0.15,
        "falsification_rule": "Mean relative reduction below 0.15 or any non-finite output.",
        "assumptions": ["Synthetic trajectories are adequate for a workflow demo", "Greedy dispatch is fixed across arms"],
        "supporting_claim_ids": ["fixture-tech-1", "fixture-gap-1", "fixture-impact-1"],
    }
    write_json(run_dir / "hypotheses.json", {"schema_version": SCHEMA_VERSION, "hypotheses": [hypothesis]})
    append_event(run_dir, "hypothesis_designer", "preregister_hypothesis", opportunities[0], hypothesis)

    spec = build_experiment_spec()
    write_json(run_dir / "experiment-spec.json", spec)
    append_event(run_dir, "protocol_reviewer", "freeze_experiment", hypothesis, spec)
    result = execute_registered_experiment(
        run_dir / "experiment-spec.json", run_dir / "experiment-results.json", run_dir / "experiment.log"
    )
    append_event(run_dir, "sandbox_runner", "execute_registered_experiment", spec, result)
    report = findings_markdown(run_dir, opportunities, spec, result)
    (run_dir / "findings.md").write_text(report, encoding="utf-8")
    append_event(run_dir, "skeptic", "review_and_report", result, {"report_digest": digest_bytes(report.encode("utf-8"))})
    final_manifest = finalize_manifest(run_dir, "completed_demo")
    audit = audit_run(run_dir, write=True)
    return {"manifest": final_manifest, "audit": audit, "primary_metric": result["primary_metric"]}


def worker_command(spec_path: Path, output_path: Path) -> int:
    try:
        spec = read_json(spec_path)
        result = run_toy_energy_experiment(spec)
        write_json(output_path, result)
        print(canonical_json({"status": "ok", "result_digest": result["result_digest"]}))
        return 0
    except Exception as error:  # Worker boundary must serialize all failures.
        print(canonical_json({"status": "error", "error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 2


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description=__doc__)
    main.add_argument("--version", action="version", version=VERSION)
    commands = main.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Create a durable research run scaffold")
    init.add_argument("--industry", required=True)
    init.add_argument("--question", default="")
    init.add_argument("--run-dir", type=Path, required=True)

    demo = commands.add_parser("demo", help="Run the explicit illustrative energy workflow")
    demo.add_argument("--industry", default="energy")
    demo.add_argument("--question", default="Demonstrate safe research-gap ranking and a reproducible toy experiment")
    demo.add_argument("--run-dir", type=Path, required=True)

    audit = commands.add_parser("audit", help="Verify hashes and reproducibility invariants")
    audit.add_argument("--run-dir", type=Path, required=True)

    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("--spec", type=Path, required=True)
    worker.add_argument("--output", type=Path, required=True)
    return main


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            result = create_scaffold(args.industry, args.question, args.run_dir)
        elif args.command == "demo":
            result = run_demo(args.industry, args.question, args.run_dir)
        elif args.command == "audit":
            result = audit_run(args.run_dir, write=False)
        elif args.command == "_worker":
            return worker_command(args.spec, args.output)
        else:
            raise HarnessError(f"Unknown command: {args.command}")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not isinstance(result, dict) or result.get("passed", True) else 1
    except (HarnessError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
