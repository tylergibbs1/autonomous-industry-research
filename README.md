# Autonomous Industry Research

A portable agent skill and local harness for evidence-grounded industry research, research-gap prioritization, falsifiable hypothesis design, and safe computational experiments.

## Quick start

Install as a skill for Codex, Claude Code, Cursor, and other hosts supported by the skills installer:

```bash
npx skills@latest add tylergibbs1/autonomous-industry-research
```

Then invoke `/autonomous-industry-research:autonomous-industry-research` in Claude Code, or mention `$autonomous-industry-research` in Codex.

Or start a research run with the harness directly:

```bash
python3 skills/research/autonomous-industry-research/scripts/research_harness.py init \
  --industry agriculture \
  --question "Which safe computational research gaps could improve water efficiency?" \
  --run-dir /tmp/agriculture-research
```

## How it works

The central design choice is deliberate: language-model agents perform open-ended reading and criticism, while deterministic code owns safety gates, scoring, experiment registration, process limits, provenance, hashes, and reproducibility checks.

A coordinator hands independent evidence lanes to isolated, read-only workers, while synthesis, scoring, file writes, and experiment execution stay single-writer. A fresh adversarial reviewer checks citations and final scientific claims. The harness records every run as durable artifacts and refuses to overwrite a non-empty run directory. See [Architecture](docs/ARCHITECTURE.md) for the full design.

## What is included

- **Cross-agent skill**: a `SKILL.md` following the Agent Skills folder convention and the small, composable repository style used by [mattpocock/skills](https://github.com/mattpocock/skills).
- **Research architecture**: coordinator/worker roles with adversarial citation and scientific review.
- **Zero-dependency Python harness**: accepts any low-risk industry, creates durable run artifacts, and never overwrites a non-empty run directory.
- **Toy experiment**: a registered, deterministic energy-storage experiment that demonstrates paired seeds, preregistration, captured logs, hashes, and audit checks. Sample output is in [`examples/energy-demo/`](examples/energy-demo/).
- **Architecture report**: a source-backed report covering OpenAI, Anthropic, Vercel, agent skills, and Karpathy’s autoresearch.
- **Tests**: unit and workflow evaluations.

## Usage

The harness has three commands: `init`, `demo`, and `audit`. Run the explicit illustrative demo, then audit it:

```bash
python3 skills/research/autonomous-industry-research/scripts/research_harness.py demo \
  --industry energy \
  --run-dir /tmp/energy-demo

python3 skills/research/autonomous-industry-research/scripts/research_harness.py audit \
  --run-dir /tmp/energy-demo
```

The demo is not a current energy literature review. Its `fixture://` sources and report are clearly labeled so no toy result can be mistaken for a domain finding.

For Claude Code plugin development from a checkout:

```bash
claude --plugin-dir .
```

## Safety boundary

The bundled runner does not execute arbitrary model-generated or retrieved code. It runs registered experiments in a temporary child process, clears the environment, captures logs, applies best-effort resource limits, and enforces a timeout. It is a narrow local control, not a hardened general-purpose sandbox. Production extensions should use a container or microVM with egress disabled, no host secrets, immutable inputs, and explicit approval before external effects.

## Read next

- [Research and recommendations](docs/RESEARCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Shared vocabulary](CONTEXT.md)
- [Skill instructions](skills/research/autonomous-industry-research/SKILL.md)

## Development

```bash
python3 -m unittest discover -s tests -v
python3 evals/run_evals.py
```

## License

[MIT](LICENSE)
