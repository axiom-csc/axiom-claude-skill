#!/usr/bin/env bash
set -e
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

AXIOM_VERSION="v1.0.0"
REPO_BASE="https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/${AXIOM_VERSION}/.claude/skills/axiom-csc"
SKILL_DIR=".claude/skills/axiom-csc"

# ── Uninstall ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "uninstall" ]]; then
  echo -e "${BLUE}==> Uninstalling Axiom CSC...${NC}"
  python3 - <<'PYEOF'
import json, pathlib, sys
p = pathlib.Path(".claude/settings.json")
if p.exists():
    try:
        s = json.loads(p.read_text())
        pre = s.get("hooks", {}).get("PreToolUse", [])
        filtered = [e for e in pre if "axiom-csc" not in e.get("hooks", [{}])[0].get("command", "")]
        if len(filtered) < len(pre):
            s["hooks"]["PreToolUse"] = filtered
            p.write_text(json.dumps(s, indent=2))
            print("  Hook entry removed from .claude/settings.json")
        else:
            print("  No axiom-csc entry found in settings.json")
    except Exception as e:
        print(f"  Could not update settings.json: {e}", file=sys.stderr)
else:
    print("  No .claude/settings.json found")
PYEOF
  if [[ -d "$SKILL_DIR" ]]; then
    rm -rf "$SKILL_DIR"
    echo -e "${GREEN}  Removed $SKILL_DIR${NC}"
  fi
  CFG="$HOME/.config/axiom-csc/config.json"
  if [[ -f "$CFG" ]]; then
    read -r -p "  Remove telemetry config at $CFG? [y/N] " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
      rm -f "$CFG"
      echo -e "${GREEN}  Removed telemetry config${NC}"
    fi
  fi
  echo -e "${GREEN}✓ Uninstall complete${NC}"
  exit 0
fi

# ── Python version check ───────────────────────────────────────────────────
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null || {
  echo -e "${RED}Error: Python 3.8 or higher is required (found $(python3 --version 2>&1)).${NC}"
  exit 1
}

echo -e "${BLUE}==> Installing Axiom CSC ${AXIOM_VERSION}...${NC}"
mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/references" "$SKILL_DIR/hooks"

curl -fsSL "$REPO_BASE/SKILL.md"                      -o "$SKILL_DIR/SKILL.md"
curl -fsSL "$REPO_BASE/hooks/pre_tool_use.py"         -o "$SKILL_DIR/hooks/pre_tool_use.py"
curl -fsSL "$REPO_BASE/scripts/lower_ast.py"          -o "$SKILL_DIR/scripts/lower_ast.py"
curl -fsSL "$REPO_BASE/scripts/eval_lemma.py"         -o "$SKILL_DIR/scripts/eval_lemma.py"
curl -fsSL "$REPO_BASE/scripts/axiom_init.py"         -o "$SKILL_DIR/scripts/axiom_init.py"
curl -fsSL "$REPO_BASE/scripts/axiom.py"              -o "$SKILL_DIR/scripts/axiom.py"
curl -fsSL "$REPO_BASE/scripts/axiom_flush.py"        -o "$SKILL_DIR/scripts/axiom_flush.py"
curl -fsSL "$REPO_BASE/references/INVARIANTS_SPEC.md" -o "$SKILL_DIR/references/INVARIANTS_SPEC.md"
chmod +x "$SKILL_DIR/hooks/"*.py "$SKILL_DIR/scripts/"*.py

# ── Register PreToolUse hook in .claude/settings.json ─────────────────────
python3 - <<'PYEOF'
import json, pathlib
p = pathlib.Path(".claude/settings.json")
p.parent.mkdir(parents=True, exist_ok=True)
try:
    s = json.loads(p.read_text()) if p.exists() else {}
except Exception:
    s = {}
cmd = "python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py"
entry = {"matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",
         "hooks": [{"type": "command", "command": cmd}]}
h = s.setdefault("hooks", {})
pre = h.setdefault("PreToolUse", [])
h["PreToolUse"] = [e for e in pre if "axiom-csc" not in e.get("hooks",[{}])[0].get("command","")] + [entry]
p.write_text(json.dumps(s, indent=2))
print(f"  Hook registered in {p}")
PYEOF

# ── Telemetry consent (TTY only, default No) ───────────────────────────────
python3 - <<'PYEOF'
import sys, json, pathlib, uuid
cfg_dir = pathlib.Path.home() / ".config" / "axiom-csc"
cfg_file = cfg_dir / "config.json"
try:
    cfg = json.loads(cfg_file.read_text()) if cfg_file.exists() else {}
except Exception:
    cfg = {}
if "telemetry" not in cfg:
    if sys.stdin.isatty():
        try:
            ans = input("\nShare anonymous usage stats to help improve Axiom?\n"
                        "Code, file paths and commands are never sent. (y/N): ").strip().lower()
            cfg["telemetry"] = ans in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            cfg["telemetry"] = False
    else:
        cfg["telemetry"] = False
if "install_id" not in cfg:
    cfg["install_id"] = str(uuid.uuid4())
if "endpoint" not in cfg:
    cfg["endpoint"] = ""
cfg_dir.mkdir(parents=True, exist_ok=True)
cfg_file.write_text(json.dumps(cfg, indent=2))
status = "enabled" if cfg["telemetry"] else "disabled (default)"
print(f"  Telemetry: {status}")
print(f"  Config: {cfg_file}")
PYEOF

# ── Agent compatibility ────────────────────────────────────────────────────
# Parse --agents=cursor,vscode from args, or prompt interactively on a TTY.
AGENTS_ARG=""
for arg in "$@"; do
  case "$arg" in --agents=*) AGENTS_ARG="${arg#--agents=}" ;; esac
done

if [[ -z "$AGENTS_ARG" ]] && [[ -t 0 ]]; then
  echo ""
  echo -e "${BLUE}==> Agent compatibility${NC}"
  echo "Which additional agents do you want to configure?"
  echo "Options: cursor  vscode  (space-separated, or press Enter to skip)"
  echo -e "${YELLOW}Default: Claude Code only (non-interactive install always skips):${NC} "
  read -r AGENTS_ARG || AGENTS_ARG=""
fi

if [[ "$AGENTS_ARG" == *"cursor"* ]]; then
  mkdir -p .cursor
  python3 - <<'PYEOF'
import json, pathlib
p = pathlib.Path(".cursor/hooks.json")
p.parent.mkdir(parents=True, exist_ok=True)
cmd = "python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py"
entry = {"matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",
         "hooks": [{"type": "command", "command": cmd}]}
try:
    s = json.loads(p.read_text()) if p.exists() else {}
except Exception:
    s = {}
h = s.setdefault("PreToolUse", [])
s["PreToolUse"] = [e for e in h if "axiom-csc" not in e.get("hooks",[{}])[0].get("command","")] + [entry]
p.write_text(json.dumps(s, indent=2))
print(f"  Cursor hook registered in {p}")
PYEOF
fi

if [[ "$AGENTS_ARG" == *"vscode"* ]]; then
  mkdir -p .vscode
  python3 - <<'PYEOF'
import json, pathlib
p = pathlib.Path(".vscode/axiom-task.json")
p.parent.mkdir(parents=True, exist_ok=True)
task = {
  "version": "2.0.0",
  "tasks": [{
    "label": "axiom-csc: check file on save",
    "type": "shell",
    "command": "echo '{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"${file}\",\"content\":\"\"}}' | python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py --stdin",
    "presentation": {"reveal": "silent", "panel": "shared"},
    "runOptions": {"runOn": "folderOpen"},
    "problemMatcher": []
  }]
}
p.write_text(json.dumps(task, indent=2))
print(f"  VS Code task written to {p}")
PYEOF
fi

echo ""
echo -e "${GREEN}✓ Axiom armed. Protected against 5 agent failure domains.${NC}"
echo -e "${YELLOW}Next steps:"
echo -e "  1. python3 $SKILL_DIR/scripts/axiom_init.py .   (generate .axiom/invariants.yaml)"
echo -e "  2. python3 $SKILL_DIR/scripts/axiom.py telemetry status"
echo -e "  To uninstall: bash install.sh uninstall"
echo -e "  Other agents:  bash install.sh --agents=cursor,vscode${NC}"
echo ""
echo "Found a bypass? Open an issue: https://github.com/axiom-csc/axiom-claude-skill/issues"
echo "Built something with it? Drop a star: https://github.com/axiom-csc/axiom-claude-skill"
