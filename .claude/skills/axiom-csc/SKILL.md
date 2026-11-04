---
name: axiom-csc
description: Stop Claude from guessing your security, auth, and system constraints. Deterministic Tri-State guardrails for Claude Code across any domain.
---

# Axiom Core: Continuous Structural Compiler (CSC)

Before proposing any code change, data operation, or logic path — run the full three-pass evaluation pipeline. Do NOT rely on statistical guesswork for hard constraints.

## Operational Modes

- **STRICT** (default): Fail-closed on any UNKNOWN. Halt and ask. Never proceed.
- **AUDIT**: Execute normally, append telemetry block showing every extracted entity and its disposition.
- **REPAIR**: Detect violations in a proposed code block, auto-rewrite before output.

Activate: include `[AXIOM: AUDIT]` or `[AXIOM: REPAIR]` in your prompt.

## Pass 1 — Noema (Multi-Domain AST Lowering)

Extract all operational variables into typed Base Entities: `(id, concept, value, type)`.

Domains: auth roles, payment values, rate limits, file sizes, DB row limits, API quotas, timeouts, retry counts.

```bash
python3 .claude/skills/axiom-csc/scripts/lower_ast.py --input "$TASK_CONTEXT"
```

## Pass 2 — Lemma (Relational Logic Solver)

Evaluate extracted Base Entities against `.axiom/invariants.yaml` deterministically.

```bash
python3 .claude/skills/axiom-csc/scripts/eval_lemma.py --ast ast.json --rules .axiom/invariants.yaml
```

- Exit 0 → ALLOW
- Exit 1 → BLOCK (output AxiomConstraintViolation, halt)
- Exit 2 → ASK (output targeted micro-query, halt)

## Pass 3 — Manam (Tri-State Epistemic Controller)

Maintain strict 3-State Logic: `TRUE | FALSE | UNKNOWN`.

On UNKNOWN: halt, issue one precise question naming the exact missing variable. Never guess.

## First-time setup

```bash
python3 .claude/skills/axiom-csc/scripts/axiom_init.py .
```

Scans your workspace and generates `.axiom/invariants.yaml` automatically.

## Output Format (AUDIT mode)
