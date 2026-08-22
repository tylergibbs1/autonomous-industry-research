# Computational experiment protocol

Before execution, confirm all items.

## Scientific validity

- Freeze one falsifiable primary hypothesis and one primary metric.
- Define the comparator, minimum meaningful effect, population or simulated environment, seeds, replications, exclusion rules, and stopping rule.
- Prefer paired designs when baseline and intervention can share the same random scenario.
- Include at least one negative control or invariant and one sensitivity analysis.
- Separate exploratory metrics from confirmatory metrics.
- Report effect size and uncertainty, not only a pass/fail label.

## Reproducibility

- Hash every input and freeze the experiment specification before running.
- Pin runtime and dependency versions; do not install dependencies during a run.
- Record seeds, command, environment metadata, stdout, stderr, exit status, duration, and output hashes.
- Re-run from a clean directory and compare primary outputs within a declared tolerance.
- Preserve crashes, null results, and rejected hypotheses.

## Safety

- Use synthetic, public aggregate, or explicitly authorized local data.
- Execute only reviewed code from the registered experiment boundary.
- Remove secrets and disable network and external integrations.
- Limit CPU, memory, processes, file size, and wall time.
- Stop on sandbox failure, unexpected file access, missing provenance, non-finite metrics, or divergence from the frozen specification.

## Interpretation

Ask a fresh reviewer to search for confounding, leakage, unrealistic assumptions, multiple-comparison errors, invalid uncertainty estimates, and conclusions that exceed the model’s scope. A simulation result is evidence about the simulation, not automatic evidence about the real world.
