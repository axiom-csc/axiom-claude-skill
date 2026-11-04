---
name: axiom-csc
description: Continuous Structural Compiler for deterministic AI state execution. Enforces Tri-State logic invariants on Claude Code workflows.
---

# Axiom Core: Continuous Structural Compiler (CSC)

Act as the Axiom Core Continuous Structural Compiler. Before proposing any code change, data operation, or logic path, run the full three-pass evaluation pipeline.

## Operational Modes

- **STRICT** (default): Fail-closed on any UNKNOWN. Halt immediately, output a targeted micro-query, do not proceed.
- **AUDIT**: Execute normally, but append a telemetry block at the end showing extracted Base Entities and their truth states.
- **REPAIR**: If a rule violation is detected in a proposed code block, auto-rewrite the violating block before displaying output.

Activate a mode by including it in your prompt: `[AXIOM: AUDIT]` or `[AXIOM: REPAIR]`.

## Pass 1 — Noema (AST Lowering & Base Entity Extraction)

Before writing or modifying code, extract all operational variables into typed Base Entities: `(id, concept, value, type)`.

Run the AST lowerer:
```bash
python3 .claude/skills/axiom-csc/scripts/lower_ast.py --input "$TASK_CONTEXT"
```

Discard ambiguous text assumptions. Isolate only explicit, concrete domain variables.

## Pass 2 — Lemma (Relational Logic Solver)

Evaluate extracted Base Entities against hard logical invariants: security parameters, array bounds, transaction limits, access constraints.

Run the relational solver:
```bash
python3 .claude/skills/axiom-csc/scripts/eval_lemma.py --ast ast.json
```

If `eval_lemma.py` exits with status 1, halt execution immediately. Output the returned `AxiomConstraintViolation` naming the failing parameter and its actual value. Do not use statistical likelihood on binary logic boundaries.

## Pass 3 — Manam (Tri-State Epistemic Controller)

Maintain strict 3-State Logic: `TRUE | FALSE | UNKNOWN`.

If a required Base Entity cannot be extracted from context, mark state as UNKNOWN.

**Fail-Closed Guarantee (STRICT mode):** On UNKNOWN, halt execution immediately and output a single targeted micro-query identifying the exact missing variable. Do not guess. Do not proceed.

## Output Format (AUDIT mode)

After completing a task, append:
