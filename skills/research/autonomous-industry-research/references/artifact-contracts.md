# Artifact contracts

Use JSON or JSON Lines for machine state and Markdown only for the final human narrative.

## Evidence record

Each line in `evidence.jsonl` contains:

- `claim_id`: stable identifier.
- `claim`: one atomic statement.
- `source_url`, `source_title`, `publisher`, `published_at`, `accessed_at`.
- `source_type`: official documentation, standard, peer-reviewed paper, patent, dataset, regulatory filing, or clearly labeled secondary source.
- `support`: `supported`, `partially_supported`, `contradicted`, or `unverified`.
- `quote_or_locator`: a short excerpt or precise section/page locator.
- `lane`: research lane.
- `notes`: limitations, conflicts, and inference boundaries.

Do not merge multiple claims into one record. A URL without an opened and checked source is `unverified`.

## Opportunity rubric

Score each component from 0–5 and preserve the explanation:

| Component | Weight | High score means |
|---|---:|---|
| Public benefit | 0.25 | Large, plausible benefit to people or the environment |
| Decision value | 0.15 | Result would change a concrete decision |
| Neglectedness | 0.15 | Important uncertainty has little adequate work |
| Computational tractability | 0.15 | A safe local experiment can materially reduce uncertainty |
| Evidence readiness | 0.10 | Inputs and baselines exist and are usable |
| Time to impact | 0.10 | A useful result could translate relatively soon |
| Equity/access | 0.10 | Benefits are accessible and harms are not displaced |

Subtract a 0–2 risk penalty for misuse, safety, privacy, environmental, or governance concerns. Report both the weighted score and the risk penalty. A high score does not override the safety gate.

## Hypothesis

`hypotheses.json` records the intervention, comparator, simulated population/environment, primary metric, direction, minimum effect, assumptions, falsification rule, and supporting claim IDs. Freeze it before executing the experiment.

## Experiment specification

`experiment-spec.json` records:

- a registered `experiment_id` and version;
- input artifact hashes;
- deterministic seeds and number of replications;
- comparator and intervention parameters;
- primary and secondary metrics;
- statistical analysis and uncertainty method;
- success, failure, and abort criteria;
- CPU, memory, file-size, and wall-time budgets;
- sandbox and network policy;
- exact command and runtime version.

## Findings

`findings.md` must separate:

1. supported external facts with citations;
2. results produced by this run;
3. interpretations and uncertainty;
4. architectural or product recommendations;
5. safety limitations and non-authorized uses;
6. exact reproduction commands.
