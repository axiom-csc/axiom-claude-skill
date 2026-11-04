# axiom-claude-skill

> Bring deterministic constraint enforcement to your Claude Code workflow in one command.

## Install

    curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/install.sh | bash

Requires Claude Code CLI.

## What it does

Once installed, Claude runs every code change and logic path through a three-pass evaluation pipeline before producing output.

Pass 1 - Noema: Extracts typed Base Entities from task context
Pass 2 - Lemma: Evaluates entities against hard logical invariants  
Pass 3 - Manam: Enforces 3-state logic: TRUE / FALSE / UNKNOWN

On UNKNOWN, Claude halts and asks exactly the right question instead of guessing.

## Modes

STRICT (default): Fail-closed on any UNKNOWN, halts and asks
AUDIT [AXIOM: AUDIT]: Executes normally, appends telemetry block
REPAIR [AXIOM: REPAIR]: Auto-rewrites violating code before output

## Example

    [AXIOM: AUDIT] Refactor the payment processing function to handle amounts over $10,000.

Claude extracts payment_amount, evaluates it against declared limits, then either proceeds with a telemetry summary or halts with a targeted question.

AUDIT output:

    --- AXIOM TELEMETRY ---
    Entities extracted : 3
    Lemma violations   : 1
    Unknown states     : 0
    Disposition        : BLOCK
    -----------------------

## Manual install

    mkdir -p .claude/skills/axiom-csc
    curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/.claude/skills/axiom-csc/SKILL.md -o .claude/skills/axiom-csc/SKILL.md

## Engine

This skill is a lightweight adaptation of Axiom Core (https://github.com/axiom-csc/axiom-core) — a Python rule-verification engine with deterministic graph evaluation running at ~0.09ms p50 on commodity CPU.

The skill brings the Noema/Lemma/Manam architecture into Claude Code as a native skill, with no binary or server required.

## License

MIT - Axiom CSC (https://github.com/axiom-csc)
