#!/usr/bin/env bash
set -e

SKILL_DIR=".claude/skills/axiom-csc"
mkdir -p "$SKILL_DIR"

curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-core/main/.claude/skills/axiom-csc/SKILL.md -o "$SKILL_DIR/SKILL.md"

echo "✅ Axiom Core skill installed into $SKILL_DIR/SKILL.md"
