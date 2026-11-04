#!/usr/bin/env python3
# Axiom PreToolUse Hook
# Fires before every Bash/Edit tool. Blocks if invariants violated.
# Exit 0 = allow. Exit 1 = block.
import sys, json, pathlib, subprocess, time

AST_OUT = ".axiom/_hook_ast.json"
RULES   = ".axiom/invariants.yaml"
STATE   = ".axiom/state.json"
SOLVER  = ".claude/skills/axiom-csc/scripts/eval_lemma.py"
LOWERER = ".claude/skills/axiom-csc/scripts/lower_ast.py"

def load_state():
    p = pathlib.Path(STATE)
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {"verified_entities": {}, "blocked_attempts": 0, "last_eval_ms": 0}

def save_state(state):
    pathlib.Path(STATE).write_text(json.dumps(state, indent=2))

def main():
    try:
        tool_input = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)
    tool_name = tool_input.get("tool", "")
    if tool_name not in ("Bash", "Edit", "Write", "MultiEdit"):
        sys.exit(0)
    parts = []
    for key in ("command", "new_string", "content", "description"):
        v = tool_input.get("input", {}).get(key, "")
        if v: parts.append(str(v))
    context = " ".join(parts)
    if not context.strip():
        sys.exit(0)
    state = load_state()
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, LOWERER, "--input", context, "--out", AST_OUT], capture_output=True)
    if r.returncode != 0:
        sys.exit(0)
    r2 = subprocess.run([sys.executable, SOLVER, "--ast", AST_OUT, "--rules", RULES], capture_output=True, text=True)
    ms = round((time.monotonic() - t0) * 1000, 3)
    state["last_eval_ms"] = ms
    if r2.returncode in (1, 2):
        state["blocked_attempts"] += 1
        save_state(state)
        print(r2.stdout.strip(), file=sys.stderr)
        label = "BLOCKED" if r2.returncode == 1 else "HALTED"
        print(f"[Axiom Hook] {label} ({ms}ms)", file=sys.stderr)
        sys.exit(1)
    save_state(state)
    sys.exit(0)

if __name__ == "__main__":
    main()
