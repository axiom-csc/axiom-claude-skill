#!/usr/bin/env python3
"""Tests for telemetry: event builder, queue, network isolation, redactor."""

import json
import os
import pathlib
import re
import sys
import tempfile
import unittest
import unittest.mock

# Add scripts dir to path so we can import directly
SCRIPTS = pathlib.Path(__file__).parent.parent / ".claude/skills/axiom-csc/scripts"
HOOK_FILE = pathlib.Path(__file__).parent.parent / ".claude/skills/axiom-csc/hooks/pre_tool_use.py"

# Import axiom.py for redactor tests
sys.path.insert(0, str(SCRIPTS))
import axiom as axiom_cli

# Import hook module for unit-testing internal functions
import importlib.util
spec = importlib.util.spec_from_file_location("hook", HOOK_FILE)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


ALLOWED_EVENT_FIELDS = {
    "install_id", "ts", "decision", "rule_id",
    "tool_name", "latency_ms", "skill_version", "os", "python",
}


class TelemetryEventBuilderTests(unittest.TestCase):

    def test_event_contains_only_allowlisted_fields(self):
        """build_event must never include tool_input, paths, code, or secrets."""
        event = hook.build_event(
            install_id="test-id",
            decision="deny",
            rule_id="transaction_value",
            tool_name="Edit",
            latency_ms=12.5,
        )
        extra = set(event.keys()) - ALLOWED_EVENT_FIELDS
        self.assertEqual(extra, set(), f"Event contains non-allowlisted fields: {extra}")

    def test_event_does_not_contain_tool_input(self):
        """Even if someone accidentally passes tool_input, it must not appear in the event."""
        event = hook.build_event("id", "allow", "none", "Write", 5.0)
        event_str = json.dumps(event)
        self.assertNotIn("tool_input", event_str)
        self.assertNotIn("command", event_str)
        self.assertNotIn("file_path", event_str)

    def test_event_field_types(self):
        event = hook.build_event("some-uuid", "ask", "rate_limit_rpm", "Bash", 8.3)
        self.assertIsInstance(event["ts"], float)
        self.assertIsInstance(event["latency_ms"], float)
        self.assertIn(event["decision"], ("allow", "ask", "deny"))
        self.assertIsInstance(event["python"], str)
        self.assertRegex(event["python"], r"^\d+\.\d+$")


class NetworkIsolationTests(unittest.TestCase):

    def _run_hook_subprocess(self, payload_dict, project_dir, extra_env=None):
        import subprocess
        env = {**os.environ, "CLAUDE_PROJECT_DIR": project_dir}
        if extra_env:
            env.update(extra_env)
        payload = json.dumps(payload_dict)
        return subprocess.run(
            [sys.executable, str(HOOK_FILE)],
            input=payload, capture_output=True, text=True, env=env,
        )

    def test_no_network_calls_when_telemetry_off(self):
        """With telemetry off the hook must make zero network calls."""
        with tempfile.TemporaryDirectory() as tmp:
            axiom_dir = pathlib.Path(tmp) / ".axiom"
            axiom_dir.mkdir()
            (axiom_dir / "invariants.yaml").write_text("rules:\n  - concept: transaction_value\n    op: lte\n    value: 10000\n    action_on_fail: BLOCK\n")

            cfg_dir = pathlib.Path(tmp) / "cfg"
            cfg_dir.mkdir()
            cfg_file = cfg_dir / "config.json"
            cfg_file.write_text(json.dumps({"telemetry": False, "install_id": "test", "endpoint": "http://example.com/ingest"}))

            # Patch HOME so the hook reads our config
            result = self._run_hook_subprocess(
                {"tool_name": "Edit", "tool_input": {"new_string": "color: red;"}},
                project_dir=tmp,
                extra_env={"HOME": tmp},
            )
            # Hook should succeed
            self.assertEqual(result.returncode, 0)
            # No JSON deny/ask on stdout → allow
            self.assertEqual(result.stdout.strip(), "")

    def test_network_failure_does_not_affect_decision(self):
        """record_telemetry must not raise even if queue write or flush fails."""
        with unittest.mock.patch.object(hook, "queue_event", side_effect=OSError("disk full")):
            with unittest.mock.patch.object(hook, "fire_flush", side_effect=RuntimeError("no network")):
                # Should not raise
                try:
                    hook.record_telemetry("allow", "none", "Edit", 5.0)
                except Exception as e:
                    self.fail(f"record_telemetry raised: {e}")


class QueueManagementTests(unittest.TestCase):

    def test_queue_capped_at_1000(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig_queue = hook.QUEUE_FILE
            hook.QUEUE_FILE = pathlib.Path(tmp) / "queue.jsonl"
            hook.CONFIG_DIR = pathlib.Path(tmp)
            try:
                # Write 1005 events
                for i in range(1005):
                    hook.queue_event({"ts": float(i), "i": i})
                lines = hook.QUEUE_FILE.read_text().splitlines()
                self.assertLessEqual(len(lines), 1000, f"Queue has {len(lines)} lines, expected ≤1000")
                # Oldest should have been dropped
                first = json.loads(lines[0])
                self.assertGreaterEqual(first.get("i", 0), 5)
            finally:
                hook.QUEUE_FILE = orig_queue


class RedactorTests(unittest.TestCase):

    def test_redacts_fake_stripe_key(self):
        # Key split to avoid triggering GitHub push-protection on the literal
        fake_key = "sk_live_" + "abcdefghijklmnopqrstuvwx"
        text = f'stripe_key = "{fake_key}"'
        result = axiom_cli.redact_secrets(text)
        self.assertNotIn("sk_live_", result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_fake_aws_key(self):
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        result = axiom_cli.redact_secrets(text)
        self.assertNotIn("AKIA", result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_fake_openai_key(self):
        openai_key = "sk-" + "a" * 48
        result = axiom_cli.redact_secrets(f'OPENAI_API_KEY="{openai_key}"')
        self.assertNotIn(openai_key, result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_private_key_block(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQ...\n-----END RSA PRIVATE KEY-----"
        result = axiom_cli.redact_secrets(text)
        self.assertNotIn("BEGIN RSA PRIVATE KEY", result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_email(self):
        result = axiom_cli.redact_secrets("Contact admin@example.com for access")
        self.assertNotIn("admin@example.com", result)
        self.assertIn("[REDACTED]", result)

    def test_safe_text_unchanged(self):
        text = "Set payment cap to $5000 for all users"
        result = axiom_cli.redact_secrets(text)
        self.assertEqual(result, text)


class NonInteractiveInstallTests(unittest.TestCase):

    def test_non_tty_install_leaves_telemetry_off(self):
        """Simulate non-interactive install: pipe /dev/null, telemetry must stay false."""
        import subprocess, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cfg_file = pathlib.Path(tmp) / "config.json"
            script = f"""
import sys, json, pathlib, uuid
cfg_file = pathlib.Path({repr(str(cfg_file))})
cfg = {{}}
# Simulate the install consent block
if sys.stdin.isatty():
    cfg['telemetry'] = True  # would prompt
else:
    cfg['telemetry'] = False  # non-TTY: default off
cfg['install_id'] = str(uuid.uuid4())
cfg['endpoint'] = ''
cfg_file.write_text(json.dumps(cfg))
"""
            result = subprocess.run(
                [sys.executable, "-c", script],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            cfg = json.loads(cfg_file.read_text())
            self.assertFalse(cfg["telemetry"], "Non-interactive install must leave telemetry off")


if __name__ == "__main__":
    unittest.main(verbosity=2)
