#!/usr/bin/env bash
# Axiom CSC demo script — simulates two hook scenarios against a temporary project.
# Run directly: bash scripts/record_demo.sh
# Record with asciinema: asciinema rec demo.cast && bash scripts/record_demo.sh
# Record with VHS: vhs scripts/demo.tape
set -euo pipefail

DEMO_DIR="/tmp/axiom-demo"
SKILL_DIR=".claude/skills/axiom-csc"
HOOK="$SKILL_DIR/hooks/pre_tool_use.py"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Setup ──────────────────────────────────────────────────────────────────
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR/src/payments"
mkdir -p "$DEMO_DIR/$SKILL_DIR/hooks"
mkdir -p "$DEMO_DIR/$SKILL_DIR/scripts"
mkdir -p "$DEMO_DIR/$SKILL_DIR/references"
mkdir -p "$DEMO_DIR/.axiom"
mkdir -p "$DEMO_DIR/.claude"

# Copy hook and scripts from the repo (not from a URL — keeps it reproducible)
cp "$REPO_ROOT/.claude/skills/axiom-csc/hooks/pre_tool_use.py" "$DEMO_DIR/$SKILL_DIR/hooks/"
cp "$REPO_ROOT/.claude/skills/axiom-csc/scripts/lower_ast.py"   "$DEMO_DIR/$SKILL_DIR/scripts/"
cp "$REPO_ROOT/.claude/skills/axiom-csc/scripts/eval_lemma.py"  "$DEMO_DIR/$SKILL_DIR/scripts/"

cat > "$DEMO_DIR/.axiom/invariants.yaml" <<'YAML'
# .axiom/invariants.yaml
rules:
  # source: src/payments/checkout.py
  - concept: transaction_value
    op: lte
    value: 50000
    action_on_fail: BLOCK
YAML

cat > "$DEMO_DIR/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{"type": "command", "command": "python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py"}]
      }
    ]
  }
}
JSON

cat > "$DEMO_DIR/src/payments/checkout.py" <<'PY'
MAX_TRANSACTION = 50000
PY

echo "=== Axiom CSC Demo: Payment Limit Protection ==="
echo ""

# ── Scenario 1: Payment limit violation → DENY ────────────────────────────
echo "--- Scenario 1: raise transaction limit to \$75,000 above policy limit → DENY ---"
PAYLOAD='{"tool_name":"Edit","tool_input":{"file_path":"src/payments/checkout.py","new_string":"# Raise cap to $75,000 for enterprise tier\nMAX_TRANSACTION = 75000"}}'
OUT=$(echo "$PAYLOAD" | CLAUDE_PROJECT_DIR="$DEMO_DIR" python3 "$DEMO_DIR/$HOOK" 2>/dev/null || true)
if [ -n "$OUT" ]; then
  echo "$OUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
h = d.get('hookSpecificOutput', {})
dec = h.get('permissionDecision', '?')
reason = h.get('permissionDecisionReason', '')
print(f'[hook] decision={dec}')
print(f'[hook] reason: {reason[:120]}')
" 2>/dev/null || echo "[hook] $OUT"
else
  echo "[hook] allow (no JSON output)"
fi
echo ""

# ── Scenario 2: CSS style change → ALLOW ──────────────────────────────────
echo "--- Scenario 2: CSS style change → ALLOW ---"
PAYLOAD='{"tool_name":"Edit","tool_input":{"file_path":"src/static/main.css","new_string":"body { color: red; font-size: 14px; }"}}'
STDERR_OUT=$(echo "$PAYLOAD" | CLAUDE_PROJECT_DIR="$DEMO_DIR" python3 "$DEMO_DIR/$HOOK" 2>&1 >/dev/null || true)
echo "[hook] $STDERR_OUT"
echo ""

# ── Cleanup ───────────────────────────────────────────────────────────────
rm -rf "$DEMO_DIR"
echo "Demo complete. /tmp/axiom-demo cleaned up."
