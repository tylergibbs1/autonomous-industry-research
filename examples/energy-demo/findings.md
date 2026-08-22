# Illustrative energy research run

> This is a deterministic workflow demonstration. Its fixture records are not a current literature review and its result is not evidence about a real grid.

## Actionable finding

The highest-ranked illustrative opportunity was **Stress-test storage sizing under variable synthetic supply** (score 3.48/5 after risk penalty). In the preregistered toy simulation, doubling energy capacity while holding power constant produced a mean relative reduction in unmet synthetic demand of **1.4%** (normal-approximation 95% CI 1.3% to 1.4%). The preregistered threshold was 15%; the run result was `falsified_in_toy_model`.

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
python3 skills/research/autonomous-industry-research/scripts/research_harness.py audit --run-dir examples/energy-demo
```

The frozen experiment is `experiment-spec.json`; raw paired outputs are in `experiment-results.json`; hashes are in `manifest.json`.
