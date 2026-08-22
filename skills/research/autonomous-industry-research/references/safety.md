# Safety gate

Apply this gate before research planning and again before experiment execution.

## Allowed without an extra checkpoint

- Public-source landscape research.
- Toy, synthetic, or aggregate-data simulations with no real-world actuation.
- Local analysis of user-provided, non-sensitive data.
- Reproduction of published computational results when licenses and resource limits permit it.

## Require human review

- Healthcare, biotechnology, chemistry, nuclear, defense, critical infrastructure, or financial domains even when the planned work is computational.
- Personal, patient, genomic, proprietary, export-controlled, or otherwise sensitive data.
- Paid compute, large downloads, external API writes, publication, deployment, purchases, or messages to third parties.
- A conclusion likely to influence clinical care, public safety, employment, credit, insurance, markets, or regulation.

At review, show the evidence sources, proposed code boundary, data classification, primary endpoint, maximum resources, expected failure modes, and exact external effects.

## Block

- Wet-lab protocols, pathogen enhancement, toxin optimization, genetic modification instructions, or operational biological experimentation.
- Chemical synthesis optimization for toxic, explosive, controlled, or weaponizable compounds.
- Weapon design, targeting, evasion, or capability enhancement.
- Cyber exploitation, credential theft, persistence, destructive payloads, or attacks on systems without explicit authorization.
- Diagnosis or treatment decisions for an individual, autonomous trading, or other high-stakes actions without a qualified human decision-maker.
- Experiments that access secrets, escape the run directory, install arbitrary dependencies, execute retrieved code, or communicate with real systems.

When blocked, explain the boundary and offer a benign alternative such as literature mapping, safety evaluation, synthetic-data analysis, defensive auditing, or a toy model.

## Execution boundary

Treat all model-authored code as untrusted. The bundled local runner is intentionally narrow: it accepts only registered experiment identifiers, clears the child environment, applies best-effort process limits, captures output, and enforces a timeout. It is not a hardened container and does not provide a general network-isolated code sandbox. For extensible or production execution, use a container or microVM with:

- no network by default;
- read-only inputs and a dedicated writable output mount;
- no host credentials or cloud metadata access;
- CPU, memory, process, file-size, and wall-time limits;
- pinned images and dependencies;
- immutable input digests and complete stdout/stderr capture;
- explicit approval before enabling egress or external side effects.
