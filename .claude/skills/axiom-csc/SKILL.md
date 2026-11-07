---
name: axiom-csc
version: 1.2.2
description: Stop Claude from guessing your security, auth, and system constraints. Deterministic Tri-State guardrails for Claude Code across any domain.
compatibility: claude-code
---

# Axiom Core: Continuous Structural Compiler (CSC)

Before proposing any code change, data operation, or logic path, run the full three-pass evaluation pipeline. Do NOT rely on statistical guesswork for hard constraints.

**PreToolUse hook:** `.claude/skills/axiom-csc/hooks/pre_tool_use.py` intercepts Bash and file-edit commands before execution. Checks run against `.axiom/invariants.yaml`.

**First-time setup:** If `.axiom/invariants.yaml` does not exist, run:
```bash
python3 .claude/skills/axiom-csc/scripts/axiom_init.py .
```

## Operational Modes

- **STRICT** (default): Fail-closed on any UNKNOWN. Halt and ask. Never proceed.
- **AUDIT**: Execute normally, append telemetry block showing every extracted entity and disposition.
- **REPAIR**: Detect violations in a proposed code block, auto-rewrite before output.

Activate: include `[AXIOM: AUDIT]` or `[AXIOM: REPAIR]` in your prompt.

## Pass 1 - Noema (Multi-Domain AST Lowering)

Extract all operational variables into typed Base Entities: `(id, concept, value, type)`.
Domains: auth roles, payment values, rate limits, file sizes, DB row limits, API quotas, timeouts, retry counts.

```bash
python3 .claude/skills/axiom-csc/scripts/lower_ast.py --input "$TASK_CONTEXT"
```

## Pass 2 - Lemma (Relational Logic Solver)

```bash
python3 .claude/skills/axiom-csc/scripts/eval_lemma.py --ast ast.json --rules .axiom/invariants.yaml
```

- Exit 0 -> ALLOW
- Exit 1 -> BLOCK (output AxiomConstraintViolation, halt)
- Exit 2 -> ASK (output targeted micro-query, halt)

## Pass 3 - Manam (Tri-State Epistemic Controller)

Maintain strict 3-State Logic: `TRUE | FALSE | UNKNOWN`.
On UNKNOWN: halt, issue one precise question. Write resolved answers to `.axiom/state.json` for subsequent turns.

## Session State (.axiom/state.json)

Resolved entities persist across turns. Verified entities are cached, block count tracked, resolved ASK answers written back so the next turn skips that check.

## Output Format (AUDIT mode)

```
--- AXIOM TELEMETRY ---
Entities extracted : <n>
Lemma violations   : <n>
Unknown states     : <n>
Disposition        : ALLOW | BLOCK | ASK
Latency            : <ms>ms
-----------------------
```

For advanced rule syntax, see `.claude/skills/axiom-csc/references/INVARIANTS_SPEC.md`.
