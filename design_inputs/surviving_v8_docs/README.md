# LAOS v8.0 — Architect-Controlled Agent Operating System

LAOS v8 is a private control framework for a **highly capable Software Architect AI**. The Architect uses LAOS to understand a software project, decide the architecture and execution strategy, and compile tightly bounded instructions for weaker desktop or coding agents.

**The master LAOS framework is never given to the weaker agent.** A weaker agent receives only the public execution rules and one signed Action Capsule for the single action it is currently authorised to perform. Future work, hidden checks, Architect reasoning, release authority, and signing keys remain private.

## Exact purpose

For a new application, the Architect turns Nilhan's approved goal into a validated project blueprint, a private control pack, and a sequence of proof-gated micro-actions. For an existing application, the Architect first compiles read-only capture instructions; weaker investigation agents return structured, source-backed App Intelligence; the Architect validates that evidence, forms its own understanding, and only then compiles continuation actions.

The goal is to make weaker agents perform far beyond ordinary broad-prompt execution by making skipped steps, scope drift, stale context, false completion, test weakening, and unsupported claims difficult to hide—and, where possible, technically impossible.

## Core operating rule

```text
Nilhan
  → highly capable Software Architect AI + private LAOS
  → private Architect Control Pack
  → one signed Action Capsule
  → weaker execution agent
  → deterministic checks + immutable evidence + independent review
  → next action only after acceptance
```

## What v8 enforces

- Strict Draft 2020-12 schemas generated from typed models.
- One canonical repository manifest for capture, continuation, sealing, checks, and evidence.
- Repository sealing before a weaker agent begins.
- Transactional SQLite state, leases, nonces, authenticated sessions, and hash-chained events.
- One-action-at-a-time execution: `UNDERSTAND → PLAN → IMPLEMENT → VERIFY → EVIDENCE → HANDOFF → REVIEW`.
- Separate criterion-level closure; a task cannot close merely because all actions say “done.”
- Private/public pack separation with leak scanning and signed Action Capsules.
- Shell-free command execution through a broker; high-risk checks fail closed without a real sandbox.
- Evidence stored under the repository-root `Evidence/` folder, content-addressed and bound to fresh source truth.
- Authenticated independent review; a builder cannot approve its own work.
- Controlled, idempotent external side effects with approval, verification receipts, and compensation plans.
- Read-only existing-application capture followed by Architect acceptance and freshness-checked continuation.
- Deterministic release artifacts, safe extraction, SBOM, provenance, checksums, and post-extraction retesting.

## Begin here

- Nilhan: `START_HERE_FOR_NILHAN.md`
- Strong Software Architect AI: `START_HERE_FOR_ARCHITECT_AI.md`
- Existing-app investigator: `START_HERE_FOR_CAPTURE_AGENT.md`
- Weaker implementation agent: `START_HERE_FOR_IMPLEMENTATION_AGENT.md`
- Independent reviewer: `START_HERE_FOR_REVIEWER.md`
- Full operating guide: `docs/MASTER_V8_GUIDE.md`

## Fast local checks

```bash
python -m pytest -q
PYTHONPATH=src python -m laos version
PYTHONPATH=src python -m laos doctor
PYTHONPATH=src python -m laos schema validate ProjectBlueprint examples/new_app_blueprint.example.json
```

## Honest boundary

LAOS is a workflow and evidence control plane. It is not, by itself, an operating-system security boundary. High-risk agents and commands must run inside a real container, VM, microVM, or managed coding sandbox with narrow mounts, no unrelated credentials, and network disabled or externally allowlisted. See `docs/TRUST_AND_SECURITY_MODEL.md`, `docs/SANDBOX_REQUIREMENTS.md`, and `docs/LIMITATIONS_AND_HUMAN_APPROVALS.md`.
