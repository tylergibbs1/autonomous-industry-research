# Research report: autonomous multi-agent industry research

Research completed 2026-08-22 using primary and official sources. Product APIs evolve; implementation adapters should re-check current documentation before deployment.

## Executive conclusion

Implement this system as a **reusable agent skill plus a deterministic runtime harness**, not as a skill alone and not initially as a large bespoke multi-agent framework.

The skill is the portable, progressively disclosed procedure: how to decompose an industry, verify sources, rank gaps, formulate hypotheses, and decide when to stop. The harness is the enforcement layer: structured state, safety routes, approvals, fixed budgets, registered experiments, sandbox policy, provenance, hashes, traces, and evaluations. A production UI or hosted service can later wrap the same contracts with OpenAI Agents SDK or Responses, Anthropic’s Agent SDK/Claude Code, or Vercel AI SDK and Workflow SDK.

## Documented guidance versus this design

| Topic | Documented guidance | Architectural recommendation here |
|---|---|---|
| Start simple | Anthropic distinguishes fixed workflows from model-directed agents and recommends the simplest solution that works because agents trade cost and latency for performance. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Start with one coordinator and optional parallel read-only lanes. Enable more workers only when coverage evals justify them. |
| Multi-agent fit | Anthropic reports its multi-agent research system works best on breadth-first queries with independent directions; its internal system outperformed a single-agent baseline by 90.2% but used roughly 15× chat tokens. [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | Fan out evidence lanes, then compress results into claim records. Do not parallelize canonical writes or experiment modification. |
| Agent runtime | OpenAI documents Agents SDK for SDK-managed loops, specialists, handoffs, guardrails, traces, and resumable approvals; Responses is the lower-level choice when the application owns orchestration. [Agents SDK overview](https://developers.openai.com/api/docs/guides/agents) | Keep provider adapters thin. The provider-neutral coordinator owns the scientific state machine and can delegate model turns to either surface. |
| Tools and approvals | OpenAI advises structured extraction from untrusted data, tool approvals, guardrails, and trace graders; it warns that arbitrary text influencing calls raises prompt-injection risk. [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety) | Retrieved content is data only. It becomes atomic claim records before affecting a later stage. External writes, high-stakes experiments, and egress require explicit approval. |
| Context | Anthropic describes context as finite and subject to diminishing returns; skills, focused tools, compaction, and subagents help curate it. [Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Claude Code context](https://code.claude.com/docs/en/how-claude-code-works) | Store full sources and trajectories on disk. Give each worker one lane and return structured claims, not long prose summaries. Keep stable prompts and schemas cache-friendly. |
| Evals | OpenAI recommends task-specific, eval-driven development, logging, automated scoring where possible, continuous evaluation, and calibration with human judgment. [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) | Evaluate claim support, source quality, gap novelty, safety routing, experiment reproducibility, and final-report calibration separately. Avoid one opaque “research quality” score. |
| Durable and HITL workflows | Vercel’s current AI SDK guidance provides agent tool approvals, durable/resumable `WorkflowAgent`, timeouts, sandbox abstractions, and streaming; Workflow SDK checkpoints long runs and can suspend for external approval. [AI SDK 7](https://vercel.com/blog/ai-sdk-7), [durable execution](https://vercel.com/blog/a-new-programming-model-for-durable-execution) | A Vercel deployment should map each typed stage to a workflow step, stream artifact/status events, and suspend at explicit approval gates. Durability belongs below prompts. |
| Subagents and examples | Vercel’s subagent guide uses isolated fresh contexts and notes that subagent tools cannot request approval. Its official AI SDK repository includes agent, sandbox, streaming, and UI examples; Vercel’s Slack Agent template demonstrates a durable approval/resume flow. [Subagents](https://ai-sdk.dev/docs/agents/subagents), [vercel/ai](https://github.com/vercel/ai), [Slack Agent template](https://examples.vercel.com/templates/nitro/slack-agent-template) | Keep subagent tools read-only and non-sensitive. Put approval-requiring operations on the durable coordinator, which is also the sole canonical writer. |
| Skills | OpenAI and Claude describe skills as `SKILL.md` folders with metadata, instructions, and optional scripts/references, loaded through progressive disclosure. [OpenAI build skills](https://learn.chatgpt.com/docs/build-skills), [Claude Code skills](https://code.claude.com/docs/en/slash-commands) | Ship the research procedure in the common skill shape. Bundle deterministic helpers, but keep deployment-specific adapters outside the core instructions. |

## What “skill” means across ecosystems

The shared concept is a filesystem bundle that gives an agent reusable procedural knowledge without placing the full content in every prompt.

- **Codex/OpenAI:** A skill is a directory with required `SKILL.md` name and description plus optional scripts, references, assets, and UI metadata. Codex begins with metadata and reads the body only when selected. OpenAI also exposes versioned skill bundles through the API. [Build skills](https://learn.chatgpt.com/docs/build-skills), [agent computer environments](https://openai.com/index/equip-responses-api-computer-environment/), [openai/skills](https://github.com/openai/skills)
- **Claude Code/Anthropic:** Skills follow the Agent Skills open standard. Their descriptions are discoverable and bodies load on demand; Claude Code adds invocation controls and can run a skill in a forked context or preload skills into subagents. Skills provide reusable content, while subagents provide isolated execution contexts. [Claude Code skills](https://code.claude.com/docs/en/slash-commands), [subagents](https://code.claude.com/docs/en/sub-agents)
- **Broader tooling:** The practical interoperable denominator is the folder, `SKILL.md` YAML frontmatter, Markdown procedure, and referenced resources. Host-specific fields should be optional. Matt Pocock’s repository demonstrates small composable skills grouped under `skills/`, with a Claude plugin manifest and installation through `skills.sh`. [mattpocock/skills](https://github.com/mattpocock/skills)

This project mirrors that repository shape while adding `agents/openai.yaml` for Codex UI metadata and keeping the core `SKILL.md` portable.

## Lessons from Karpathy’s autoresearch

[Karpathy’s autoresearch](https://github.com/karpathy/autoresearch) is deliberately small: a fixed evaluation file, one modifiable training file, a Markdown program for the agent, a fixed five-minute budget, one metric, an append-only results ledger, and keep/discard decisions. Its README explicitly calls `program.md` a lightweight skill.

Patterns adopted:

- Fixed experiment budget and comparator.
- One hypothesis/change at a time.
- A narrow modifiable surface and immutable evaluation boundary.
- Output redirected to logs rather than flooding model context.
- Machine-readable result memory and preservation of crashes/negative results.
- Simplicity as a criterion, not metric gain alone.

Changes made for general scientific and safety use:

- No indefinite loop. A broad industry-research agent stops on preregistered conditions, dry search rounds, or budgets.
- No destructive Git reset as the primary memory mechanism. Rejected ideas stay in the evidence and experiment ledger.
- No arbitrary model-generated code in the bundled runner. Only registered experiments execute.
- No single-metric claim of human benefit. Opportunity scoring exposes multiple value dimensions and a separate safety penalty.
- No assumption that a toy computational win transfers to a real system. External validity and stakeholder review remain explicit.

## Recommended scientific workflow

1. Route the request through a conservative safety and data-classification gate.
2. Build a research DAG with independent evidence lanes and fixed budgets.
3. Fan out read-only scouts; require claim-level provenance and primary sources.
4. Adversarially verify every shortlisted citation against the exact claim.
5. Build a frontier map separating established evidence, disagreement, inference, and unknowns.
6. Overproduce candidate gaps, deduplicate, and score them with visible value judgments.
7. Red-team novelty, assumptions, stakeholders, and misuse before choosing one.
8. Freeze one falsifiable hypothesis and experiment protocol.
9. Execute registered code in disposable, credential-free, resource-limited compute.
10. Analyze effect sizes, uncertainty, negative controls, sensitivity, and clean reproduction.
11. Ask a fresh reviewer to downgrade claims that exceed sources or the simulated environment.
12. Produce a report with facts, results, interpretation, recommendations, and limitations clearly separated.

## Evaluation plan

Evaluate the whole system with a suite of representative industries and adversarial prompts.

| Layer | Example metric |
|---|---|
| Safety routing | Recall on blocked/high-review cases; false-positive rate on benign landscape research |
| Evidence | Citation entailment precision; primary-source share; unsupported-claim rate; source diversity |
| Coverage | Expert-rated frontier coverage; supported new claims per search/tool budget; duplicate rate |
| Gap selection | Expert novelty/decision-value ratings; prior-art refutation rate; ranking stability under rubric perturbation |
| Hypothesis | Completeness of intervention, comparator, metric, effect, assumptions, and falsification rule |
| Experiment | Spec/code match; deterministic replay; negative-control pass; timeout and resource-limit enforcement |
| Analysis | Effect-size correctness; uncertainty calibration; multiple-testing and leakage checks |
| Final report | Claim/source traceability; separation of fact/result/recommendation; calibrated confidence |
| Operations | Cost, latency, tokens, tool calls, retries, cache hit rate, approval wait time |

Use deterministic graders for schemas, hashes, math, citations, and sandbox invariants; model graders for nuanced novelty and relevance; and domain experts to calibrate the model graders. Compare single-agent and multi-agent modes on the same cases before paying the multi-agent cost.

## Safety and governance recommendations

- Default to literature-only mode in biotechnology, healthcare, chemistry, nuclear, defense, finance, and critical infrastructure until reviewed.
- Use synthetic or authorized aggregate data; isolate personal, genomic, patient, proprietary, and export-controlled material.
- Keep credentials in the harness, never in the model-generated compute environment.
- Disable egress. Temporarily grant narrowly scoped access only after approval and log it.
- Pin dependency images and data hashes. Do not install packages during experiments.
- Treat papers, web pages, repositories, and datasets as untrusted inputs that cannot issue instructions.
- Retain full audit trails, negative results, approval identity, and code/spec digests.
- Do not output wet-lab protocols, operational weapon or cyber guidance, individual clinical decisions, or autonomous real-world control.

OpenAI’s current Codex guidance emphasizes clear technical boundaries, explicit higher-risk actions, and agent-native telemetry; its agent-computer guidance recommends separating harness and compute and keeping credentials away from generated code. [Running Codex safely](https://openai.com/index/running-codex-safely/), [Agents SDK evolution](https://openai.com/index/the-next-evolution-of-the-agents-sdk/)

## Vercel implementation path

If this becomes a web product:

- Use AI SDK’s current agent abstraction for each specialist and typed tool contracts.
- Use Workflow SDK/`WorkflowAgent` for the durable coordinator, with one checkpointed step per artifact transition.
- Stream stage status and typed artifact events to the UI; persist the canonical artifacts independently of the chat transcript.
- Use tool approvals for paid search, sensitive connectors, egress, and experiment execution.
- Do not put approval-requiring tools inside subagents; Vercel’s documented subagent pattern does not support those approvals.
- Run experiment code in Vercel Sandbox or an equivalent microVM, not in the application process.
- Route model providers behind a provider abstraction and record exact provider/model/version in each trace.

Vercel documents `ToolLoopAgent` as a reusable multi-step reasoning-and-tool loop and its current stack as AI SDK plus durable workflows, sandboxed compute, routing, and observability. [ToolLoopAgent](https://ai-sdk.dev/docs/reference/ai-sdk-core/tool-loop-agent), [Agent Stack](https://vercel.com/blog/agent-stack)

## Known limitations of this prototype

- It does not call a live model or web-search provider; the host agent supplies those capabilities.
- The lexical safety gate is defense in depth, not a semantic classifier or policy engine.
- The local child-process runner is not a hardened network sandbox.
- The included energy evidence is illustrative and cannot support claims about the actual industry.
- The confidence interval in the toy demo captures stochastic scenarios, not structural model uncertainty.
- Novelty and social benefit ultimately require expert and stakeholder judgment.

These limitations are intentional: the prototype demonstrates the reliable spine without pretending that model access or a toy simulation creates scientific validity.
