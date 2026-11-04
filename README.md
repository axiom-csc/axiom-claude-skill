# axiom-claude-skill

> Bring deterministic constraint enforcement to your Claude Code workflow.

Install Axiom Core Continuous Structural Compiler as a local Claude Code skill. Once installed, Claude runs every code change and logic path through a three-pass evaluation pipeline: Noema, Lemma, Manam.

## Install

curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/install.sh | bash

Requires Claude Code CLI.

## What it does

Pass 1 - Noema: Extracts typed Base Entities from task context
Pass 2 - Lemma: Evaluates entities against hard logical invariants
Pass 3 - Manam: Enforces 3-state logic: TRUE / FALSE / UNKNOWN

On UNKNOWN, Claude halts and asks exactly the right question instead of guessing.

## Modes

- [AXIOM: STRICT] - default, fail-closed on any unknown
- [AXIOM: AUDIT] - appends telemetry block showing entity extraction results
- [AXIOM: REPAIR] - auto-rewrites violating code blocks before output

## Engine

This skill is a lightweight adaptation of Axiom Core (https://github.com/axiom-csc/axiom-core) - a Python rule-verification engine with deterministic graph evaluation. The full engine runs at ~0.09ms p50 on commodity CPU.

## License

MIT - Axiom CSC (https://github.com/axiom-csc)
