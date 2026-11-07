#!/usr/bin/env python3
"""Tests for AUDIT mode: [AXIOM: AUDIT] in tool_input flips the hook to
log-but-allow without changing STRICT behaviour for untagged calls.

STRICT remains the default. REPAIR is not implemented and is intentionally
not exercised here."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

HOOK = (
    pathlib.Path(__file__).parent.parent
    / ".claude/skills/axiom-csc/hooks/pre_tool_use.py"
)

MINIMAL_RULES = textwrap.dedent(
    """\
    rules:
      - concept: transaction_value
        op: lte
        value: 10000
        action_on_fail: BLOCK
    """
)


def run_hook(tool_name, tool_input, project_dir):
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": project_dir}
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload, capture_output=True, text=True, env=env,
    )
    try:
        out_json = json.loads(r.stdout.strip()) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        out_json = {"_raw": r.stdout}
    return r.returncode, out_json, r.stderr


class AuditModeTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        (pathlib.Path(self.tmp) / ".axiom").mkdir()
        (pathlib.Path(self.tmp) / ".axiom" / "invariants.yaml").write_text(MINIMAL_RULES)

    def _local_log(self):
        log = pathlib.Path(self.tmp) / ".axiom" / "local_log.jsonl"
        if not log.exists():
            return []
        return [json.loads(l) for l in log.read_text().splitlines() if l.strip()]

    def test_strict_default_still_denies(self):
        """Regression: an untagged call that violates a rule still DENIES."""
        code, out, stderr = run_hook(
            "Edit",
            {"new_string": "Set transaction limit to $75,000 for enterprise"},
            self.tmp,
        )
        self.assertEqual(code, 0, stderr)
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        self.assertEqual(decision, "deny", f"STRICT default must still deny; got: {out}")

    def test_audit_tagged_violation_is_allowed(self):
        """A violating call with [AXIOM: AUDIT] passes through instead of denying."""
        code, out, stderr = run_hook(
            "Edit",
            {"new_string": "[AXIOM: AUDIT] Set transaction limit to $75,000 for enterprise"},
            self.tmp,
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(out, {}, f"AUDIT must emit no JSON deny/ask; got: {out}")
        self.assertIn("AUDIT", stderr, f"AUDIT stderr marker missing: {stderr!r}")
        self.assertIn("would have: deny", stderr, f"stderr must report would-be disposition: {stderr!r}")

    def test_audit_tagged_clean_call_is_allowed_and_logged(self):
        """An AUDIT call that would have ALLOWED also logs and passes through."""
        code, out, stderr = run_hook(
            "Edit",
            {"new_string": "[AXIOM: AUDIT] color: red; font-size: 14px;"},
            self.tmp,
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(out, {})
        self.assertIn("AUDIT", stderr)
        self.assertIn("would have: allow", stderr)

    def test_audit_tag_in_description_field_is_detected(self):
        """The tag is detected in any tool_input string value, not just new_string."""
        code, out, stderr = run_hook(
            "Bash",
            {
                "command": "echo 'Set rate limit to 5000 rpm'",
                "description": "[AXIOM: AUDIT] test",
            },
            self.tmp,
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(out, {})
        # The command would be allowed anyway (rate_limit_rpm not in MINIMAL_RULES)
        # but the point is that the tag was detected in `description`.
        self.assertIn("AUDIT", stderr)

    def test_audit_mode_writes_local_log_entry(self):
        """AUDIT mode records the would-be disposition in local_log.jsonl."""
        run_hook(
            "Edit",
            {"new_string": "[AXIOM: AUDIT] Set transaction limit to $75,000"},
            self.tmp,
        )
        entries = self._local_log()
        self.assertTrue(entries, "AUDIT mode must still write a local log entry")
        last = entries[-1]
        self.assertEqual(last["decision"], "allow")
        self.assertTrue(
            last["rule"].startswith("audit:would_"),
            f"rule_id should mark the audit routing; got {last['rule']!r}",
        )
        self.assertIn("would_deny", last["rule"])


if __name__ == "__main__":
    unittest.main()
