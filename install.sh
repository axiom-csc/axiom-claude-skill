#!/usr/bin/env bash
set -e
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo -e "${BLUE}==> Installing Axiom CSC Skill for Claude Code...${NC}"
SKILL_DIR=".claude/skills/axiom-csc"
mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/references"
REPO="https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/.claude/skills/axiom-csc"
curl -fsSL "$REPO/SKILL.md"                      -o "$SKILL_DIR/SKILL.md"
curl -fsSL "$REPO/scripts/lower_ast.py"          -o "$SKILL_DIR/scripts/lower_ast.py"
curl -fsSL "$REPO/scripts/eval_lemma.py"         -o "$SKILL_DIR/scripts/eval_lemma.py"
curl -fsSL "$REPO/scripts/axiom_init.py"         -o "$SKILL_DIR/scripts/axiom_init.py"
curl -fsSL "$REPO/references/INVARIANTS_SPEC.md" -o "$SKILL_DIR/references/INVARIANTS_SPEC.md"
chmod +x "$SKILL_DIR/scripts/"*.py
echo -e "${GREEN}✓ Installed to $SKILL_DIR${NC}"
echo -e "${YELLOW}Run: python3 $SKILL_DIR/scripts/axiom_init.py .${NC}"
