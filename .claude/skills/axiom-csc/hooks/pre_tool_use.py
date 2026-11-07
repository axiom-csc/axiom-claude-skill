#!/usr/bin/env python3
"""axiom-csc PreToolUse hook - intercepts Claude Code tool calls before execution.

Detection is regex and AST-pattern based, not semantic. A motivated agent or attacker
can bypass these checks with minor obfuscation. This tool catches the most common
accidental violations, not adversarial ones. For adversarial resistance, pair it
with container isolation and branch protection.
"""

import json
import os
import platform
import sys
import time
from pathlib import Path

SKILL_VERSION = "1.2.2"

# Versions of Claude Code this hook has been tested against (major version numbers).
# If CLAUDE_CODE_VERSION is set and outside this range a warning is printed to stderr.
# The warning never changes the hook's decision.
_TESTED_CC_MAJOR = {1, 2}


def _check_version_compat() -> None:
    ver = os.environ.get("CLAUDE_CODE_VERSION", "")
    if not ver:
        return
    try:
        major = int(ver.split(".")[0])
        if major not in _TESTED_CC_MAJOR:
            print(
                f"[axiom-csc] ⚠️ Untested Claude Code version {ver} — "
                "hook may behave unexpectedly. "
                "Check github.com/axiom-csc/axiom-claude-skill for updates.",
                file=sys.stderr,
            )
    except (ValueError, IndexError):
        pass
INTERCEPTED_TOOLS = {"Bash", "Edit", "Write", "MultiEdit", "NotebookEdit"}

# Mode markers — a tool_input value containing one of these flips the
# hook's disposition for that call. Only AUDIT is implemented today.
AUDIT_TAG = "[AXIOM: AUDIT]"


def detect_mode(tool_input):
    """Return "AUDIT" if any string value in tool_input carries the AUDIT tag,
    otherwise "STRICT". The hook does not see the user's prompt directly, so
    the tag has to ride along in a tool_input field (command, new_string,
    content, description, …)."""
    if not isinstance(tool_input, dict):
        return "STRICT"
    for v in tool_input.values():
        if isinstance(v, str) and AUDIT_TAG in v:
            return "AUDIT"
    return "STRICT"

# --stdin mode: human-readable stderr + exit codes instead of JSON stdout.
# Any agent that can pipe JSON tool calls through a subprocess can use this mode.
STDIN_MODE = "--stdin" in sys.argv

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AXIOM_DIR = PROJECT_DIR / ".axiom"
STATE_FILE = AXIOM_DIR / "state.json"
AUDIT_LOG = AXIOM_DIR / "audit.log"
LOCAL_LOG = AXIOM_DIR / "local_log.jsonl"
LOCAL_LOG_MAX = 50
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

CONFIG_DIR = Path.home() / ".config" / "axiom-csc"
CONFIG_FILE = CONFIG_DIR / "config.json"
QUEUE_FILE = CONFIG_DIR / "queue.jsonl"
QUEUE_MAX = 1000

# When the pipeline itself errors (scripts missing, timeout, etc.):
# "allow" = fail-open, "ask" = ask user (default), "deny" = fail-closed
PIPELINE_ERROR_BEHAVIOR = os.environ.get("AXIOM_PIPELINE_ERROR", "ask")


# ── State / audit ──────────────────────────────────────────────────────────

def load_state():
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except Exception:
        return {}


def save_state(state):
    try:
        AXIOM_DIR.mkdir(exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def log_audit(action, entity, rule, context):
    try:
        AUDIT_LOG.parent.mkdir(exist_ok=True)
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps({
                "ts": time.time(), "action": action,
                "entity": entity, "rule": rule, "context": context[:200],
            }) + "\n")
    except Exception:
        pass


def write_local_log(tool_name, tool_input, decision, rule, reason):
    try:
        entry = json.dumps({
            "ts": time.time(), "tool_name": tool_name,
            "tool_input": str(tool_input)[:500],
            "decision": decision, "rule": rule, "reason": reason,
        })
        lines = []
        if LOCAL_LOG.exists():
            lines = LOCAL_LOG.read_text().splitlines()
        lines.append(entry)
        if len(lines) > LOCAL_LOG_MAX:
            lines = lines[-LOCAL_LOG_MAX:]
        AXIOM_DIR.mkdir(exist_ok=True)
        LOCAL_LOG.write_text("\n".join(lines) + "\n")
    except Exception:
        pass


# ── Telemetry ──────────────────────────────────────────────────────────────

def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    except Exception:
        return {}


def build_event(install_id, decision, rule_id, tool_name, latency_ms):
    # Strict allowlist — only these exact fields; no tool_input, no paths, no code
    return {
        "install_id": install_id,
        "ts": time.time(),
        "decision": decision,
        "rule_id": rule_id,
        "tool_name": tool_name,
        "latency_ms": round(latency_ms, 2),
        "skill_version": SKILL_VERSION,
        "os": platform.system().lower(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }


def queue_event(event):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        lines = QUEUE_FILE.read_text().splitlines() if QUEUE_FILE.exists() else []
        lines.append(json.dumps(event))
        if len(lines) > QUEUE_MAX:
            lines = lines[-QUEUE_MAX:]
        QUEUE_FILE.write_text("\n".join(lines) + "\n")
    except Exception:
        pass


def fire_flush(endpoint):
    try:
        import subprocess
        flush_script = SCRIPTS_DIR / "axiom_flush.py"
        if flush_script.exists():
            subprocess.Popen(
                [sys.executable, str(flush_script), endpoint],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True,
            )
    except Exception:
        pass


def record_telemetry(decision, rule_id, tool_name, latency_ms):
    try:
        cfg = load_config()
        if not cfg.get("telemetry"):
            return
        endpoint = cfg.get("endpoint", "")
        if not endpoint:
            return
        event = build_event(cfg.get("install_id", "unknown"), decision, rule_id, tool_name, latency_ms)
        queue_event(event)
        fire_flush(endpoint)
    except Exception:
        pass


# ── Hook output ────────────────────────────────────────────────────────────

def emit_decision(decision: str, reason: str):
    """Emit a permission decision.

    Claude Code (default): JSON on stdout + exit 0 (Claude reads the JSON).
    --stdin mode: human-readable message on stderr + exit code (1=deny, 2=ask, 0=allow).
    """
    if STDIN_MODE:
        print(reason, file=sys.stderr)
        sys.exit(1 if decision == "deny" else 2 if decision == "ask" else 0)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def get_context(tool_input):
    for field in ("command", "new_string", "content", "description"):
        if field in tool_input and tool_input[field]:
            return str(tool_input[field])
    return str(tool_input)


# ── Pipeline ───────────────────────────────────────────────────────────────

def run_pipeline(context, rules_path, tool_name="", file_path=""):
    import subprocess
    ast_file = AXIOM_DIR / "ast.json"
    AXIOM_DIR.mkdir(exist_ok=True)
    lower = SCRIPTS_DIR / "lower_ast.py"
    lemma = SCRIPTS_DIR / "eval_lemma.py"
    if not lower.exists() or not lemma.exists():
        return None, f"axiom-csc scripts not found in {SCRIPTS_DIR}"
    r1 = subprocess.run(
        [sys.executable, str(lower), "--input", context, "--out", str(ast_file),
         "--tool-name", tool_name, "--file-path", file_path],
        capture_output=True, text=True, timeout=5,
    )
    if r1.returncode != 0:
        return None, r1.stderr.strip() or "lower_ast.py failed"
    r2 = subprocess.run(
        [sys.executable, str(lemma), "--ast", str(ast_file), "--rules", str(rules_path)],
        capture_output=True, text=True, timeout=5,
    )
    return r2.returncode, r2.stdout + r2.stderr


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    _check_version_compat()
    start = time.monotonic()
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in INTERCEPTED_TOOLS:
        sys.exit(0)

    rules_path = AXIOM_DIR / "invariants.yaml"
    if not rules_path.exists():
        print(
            "[axiom-csc] No .axiom/invariants.yaml found — no rules to enforce. "
            "Run: python3 .claude/skills/axiom-csc/scripts/axiom_init.py . to generate one.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    context = get_context(tool_input)
    if not context.strip():
        sys.exit(0)

    file_path = str(tool_input.get("file_path", tool_input.get("path", "")))
    mode = detect_mode(tool_input)
    exit_code, output = run_pipeline(context, rules_path, tool_name=tool_name, file_path=file_path)
    elapsed_ms = (time.monotonic() - start) * 1000

    state = load_state()
    state["last_eval_ms"] = round(elapsed_ms, 3)

    # AUDIT mode: run the pipeline for its side effects (entity extraction,
    # decision capture) but always allow the call through. The would-be
    # disposition is logged to the local log and telemetry so the user can
    # inspect what STRICT would have done.
    if mode == "AUDIT":
        would = {1: "deny", 2: "ask", None: PIPELINE_ERROR_BEHAVIOR}.get(exit_code, "allow")
        summary = (output or "").strip().replace("\n", "; ")[:400] or "all checks passed"
        save_state(state)
        log_audit("AUDIT", f"would_{would}", "audit_mode", context)
        write_local_log(tool_name, context, "allow", f"audit:would_{would}", summary)
        record_telemetry("allow", f"audit:would_{would}", tool_name, elapsed_ms)
        print(
            f"[axiom-csc] AUDIT ({round(elapsed_ms, 1)}ms) — would have: {would}; {summary}",
            file=sys.stderr,
        )
        sys.exit(0)

    if exit_code is None:
        state["pipeline_errors"] = state.get("pipeline_errors", 0) + 1
        save_state(state)
        msg = f"axiom-csc pipeline error — {output}"
        write_local_log(tool_name, context, PIPELINE_ERROR_BEHAVIOR, "pipeline_error", msg)
        record_telemetry(PIPELINE_ERROR_BEHAVIOR, "pipeline_error", tool_name, elapsed_ms)
        if PIPELINE_ERROR_BEHAVIOR == "allow":
            print(f"[axiom-csc] {msg} (fail-open)", file=sys.stderr)
            sys.exit(0)
        elif PIPELINE_ERROR_BEHAVIOR == "deny":
            emit_decision("deny", msg)
        else:
            emit_decision("ask", f"{msg}. Verify before proceeding, or set AXIOM_PIPELINE_ERROR=allow to skip.")

    elif exit_code == 1:
        state["blocked_attempts"] = state.get("blocked_attempts", 0) + 1
        save_state(state)
        log_audit("BLOCK", "constraint", "invariant_violation", context)
        summary = output.strip().replace("\n", "; ")[:400]
        first_rule = next((w for w in output.split() if "_" in w), "unknown_rule")
        write_local_log(tool_name, context, "deny", first_rule, summary)
        record_telemetry("deny", first_rule, tool_name, elapsed_ms)
        emit_decision("deny", f"[axiom-csc] Invariant violation: {summary}")

    elif exit_code == 2:
        save_state(state)
        summary = output.strip().replace("\n", "; ")[:400]
        first_rule = next((w for w in output.split() if "'" in w), "unknown_rule").strip("'")
        write_local_log(tool_name, context, "ask", first_rule, summary)
        record_telemetry("ask", first_rule, tool_name, elapsed_ms)
        emit_decision("ask", f"[axiom-csc] Clarification needed: {summary}")

    else:
        save_state(state)
        write_local_log(tool_name, context, "allow", "none", "all checks passed")
        record_telemetry("allow", "none", tool_name, elapsed_ms)
        print(f"[axiom-csc] ✓ invariants OK ({round(elapsed_ms, 1)}ms)", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[axiom-csc] hook error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
