# Autonomous Industry Research

A portable agent skill and local harness for evidence-grounded industry research, research-gap prioritization, falsifiable hypothesis design, and safe computational experiments.

The central design choice is deliberate: language-model agents perform open-ended reading and criticism, while deterministic code owns safety gates, scoring, experiment registration, process limits, provenance, hashes, and reproducibility checks.

## What is included

- A cross-agent `SKILL.md` following the Agent Skills folder convention and the small, composable repository style used by [mattpocock/skills](https://github.com/mattpocock/skills).
- A coordinator/worker research architecture with adversarial citation and scientific review.
- A zero-dependency Python harness that accepts any low-risk industry, creates durable run artifacts, and never overwrites a non-empty run directory.
- A registered, deterministic toy energy-storage experiment that demonstrates paired seeds, preregistration, captured logs, hashes, and audit checks.
- A source-backed architecture report covering OpenAI, Anthropic, Vercel, agent skills, and Karpathy’s autoresearch.
- Unit and workflow evaluations.

## Quick start

```bash
python3 skills/research/autonomous-industry-research/scripts/research_harness.py init \
  --industry agriculture \
  --question "Which safe computational research gaps could improve water efficiency?" \
  --run-dir /tmp/agriculture-research
```

Run the explicit illustrative demo:

```bash
python3 skills/research/autonomous-industry-research/scripts/research_harness.py demo \
  --industry energy \
  --run-dir /tmp/energy-demo

python3 skills/research/autonomous-industry-research/scripts/research_harness.py audit \
  --run-dir /tmp/energy-demo
```

The demo is not a current energy literature review. Its `fixture://` sources and report are clearly labeled so no toy result can be mistaken for a domain finding.

## Install as a skill

For Codex, Claude Code, Cursor, and other hosts supported by the skills installer:

```bash
npx skills@latest add tylergibbs1/autonomous-industry-research
```

For Claude Code plugin development from a checkout:

```bash
claude --plugin-dir .
```

Then invoke `/autonomous-industry-research:autonomous-industry-research` in Claude Code, or mention `$autonomous-industry-research` in Codex.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 evals/run_evals.py
```

## Read next

- [Research and recommendations](docs/RESEARCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Shared vocabulary](CONTEXT.md)
- [Skill instructions](skills/research/autonomous-industry-research/SKILL.md)

## Safety boundary

The bundled runner does not execute arbitrary model-generated or retrieved code. It runs registered experiments in a temporary child process, clears the environment, captures logs, applies best-effort resource limits, and enforces a timeout. It is a narrow local control, not a hardened general-purpose sandbox. Production extensions should use a container or microVM with egress disabled, no host secrets, immutable inputs, and explicit approval before external effects.

## License

MIT
