#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}==> Installing Axiom CSC Skill for Claude Code...${NC}"

SKILL_DIR=".claude/skills/axiom-csc"
mkdir -p "$SKILL_DIR/scripts"
mkdir -p "$SKILL_DIR/references"

REPO_BASE="https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/main/.claude/skills/axiom-csc"

echo -e "${BLUE}  Fetching SKILL.md...${NC}"
curl -fsSL "$REPO_BASE/SKILL.md" -o "$SKILL_DIR/SKILL.md"

echo -e "${BLUE}  Fetching scripts...${NC}"
curl -fsSL "$REPO_BASE/scripts/lower_ast.py" -o "$SKILL_DIR/scripts/lower_ast.py"
curl -fsSL "$REPO_BASE/scripts/eval_lemma.py" -o "$SKILL_DIR/scripts/eval_lemma.py"

echo -e "${BLUE}  Fetching references...${NC}"
curl -fsSL "$REPO_BASE/references/INVARIANTS_SPEC.md" -o "$SKILL_DIR/references/INVARIANTS_SPEC.md"

chmod +x "$SKILL_DIR/scripts/"*.py

echo ""
echo -e "${GREEN}✓ Axiom CSC Skill installed to $SKILL_DIR${NC}"
echo -e "${YELLOW}  Restart Claude Code or run /reload-skills to activate.${NC}"
echo ""
echo -e "${BLUE}  Test immediately:${NC}"
echo -e "  python3 $SKILL_DIR/scripts/lower_ast.py --input 'Invoice for \$15,000'"
echo -e "  python3 $SKILL_DIR/scripts/eval_lemma.py"
