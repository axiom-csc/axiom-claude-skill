# axiom-claude-skill

> Bring deterministic constraint enforcement to your Claude Code workflow.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blue)](https://claude.ai/code)

LLMs fail on hard rules. Statistical next-token prediction cannot guarantee a `$10,000` limit is never exceeded. This skill enforces it.

Install Axiom Core's Continuous Structural Compiler as a local Claude Code skill. Claude runs every task through a **Noema → Lemma → Manam** pipeline — extracting typed entities, evaluating them against hard invariants, and failing closed on ambiguity — before producing any output.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/install.sh | bash
```

Requires [Claude Code](https://claude.ai/code).

## What it does

| Pass | Component | Role |
|------|-----------|------|
| 1 | **Noema** | Extracts typed Base Entities from task context |
| 2 | **Lemma** | Runs deterministic CPU solver against hard invariants |
| 3 | **Manam** | Enforces 3-state logic: TRUE / FALSE / UNKNOWN |

On **UNKNOWN**, Claude halts and asks exactly the right question instead of guessing.  
On **FALSE**, Claude outputs an `AxiomConstraintViolation` and stops.

## Demo

## Modes

Add to any prompt to activate:

| Mode | Tag | Behavior |
|------|-----|----------|
| STRICT | _(default)_ | Fail-closed on any UNKNOWN or violation |
| AUDIT | `[AXIOM: AUDIT]` | Execute + append telemetry block |
| REPAIR | `[AXIOM: REPAIR]` | Auto-rewrite violating code before output |

## Custom Rules

Create `.axiom/invariants.yaml` in your project root:

```yaml
rules:
  - field: transaction_value
    op: lte
    value: 50000
  - field: percentage_value
    op: lte
    value: 100
```

## Engine

This skill wraps [axiom-csc/axiom-core](https://github.com/axiom-csc/axiom-core) — a Python rule-verification engine with deterministic graph evaluation running at ~0.09ms p50 on commodity CPU.

## License

MIT · [Axiom CSC](https://github.com/axiom-csc)
