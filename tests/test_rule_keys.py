#!/usr/bin/env python3
"""Regression tests for YAML rule-key handling in eval_lemma.

Pins two behaviours that were previously doc/code mismatches:

1. Rules key on ``concept:`` (the code reads ``current['concept']``).
2. A rule written with ``field:`` is silently dropped by the built-in
   YAML parser, so the user's threshold never applies and the baked-in
   DEFAULT_RULES limit stays in force.

Also enforces ``action_on_fail`` routing: ``BLOCK`` → exit 1,
``ASK`` → exit 2, missing/unknown → BLOCK (safe default). The
matching ``action_on_missing`` field routes ``required`` rules
the same way.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

LEMMA = (
    pathlib.Path(__file__).parent.parent
    / ".claude/skills/axiom-csc/scripts/eval_lemma.py"
)


def run_lemma(rules_text: str, ast_data: dict) -> tuple[int, str, str]:
    """Run eval_lemma.py against an in-memory rules file + ast.json."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    rules_path = tmp / "invariants.yaml"
    ast_path = tmp / "ast.json"
    rules_path.write_text(rules_text)
    ast_path.write_text(json.dumps(ast_data))
    result = subprocess.run(
        [sys.executable, str(LEMMA), "--ast", str(ast_path), "--rules", str(rules_path)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class RuleKeyTests(unittest.TestCase):

    def test_concept_key_raises_the_bound(self):
        """A concept-keyed rule with value 50000 should allow 40000 even though
        DEFAULT_RULES caps transaction_value at 10000 — the user's rule covers
        the concept so the default is not merged in."""
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: BLOCK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 40000}]}
        code, stdout, stderr = run_lemma(rules, ast)
        self.assertEqual(
            code,
            0,
            f"concept-keyed limit of 50000 should allow 40000; "
            f"exit={code} stdout={stdout!r} stderr={stderr!r}",
        )

    def test_field_key_is_silently_dropped(self):
        """A rule written with 'field:' instead of 'concept:' is dropped by
        _parse_yaml_rules (only rules with current['concept'] get appended).
        The DEFAULT_RULES cap of 10000 therefore stays in force, and 40000
        is blocked."""
        rules = textwrap.dedent(
            """\
            rules:
              - field: transaction_value
                op: lte
                value: 50000
                action_on_fail: BLOCK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 40000}]}
        code, stdout, stderr = run_lemma(rules, ast)
        self.assertEqual(
            code,
            1,
            f"'field:'-keyed rule should be silently dropped so the default "
            f"10000 limit blocks 40000; exit={code} stdout={stdout!r} "
            f"stderr={stderr!r}",
        )
        self.assertIn("transaction_value", stdout)
        self.assertIn("lte 10000", stdout)

    def test_concept_key_blocks_when_exceeded(self):
        """Sanity check: a concept-keyed rule still blocks when the value
        exceeds its own threshold."""
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: BLOCK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}
        code, stdout, stderr = run_lemma(rules, ast)
        self.assertEqual(
            code,
            1,
            f"75000 should violate lte 50000; "
            f"exit={code} stdout={stdout!r} stderr={stderr!r}",
        )
        self.assertIn("lte 50000", stdout)

    def test_action_on_fail_block_routes_to_exit_1(self):
        """action_on_fail: BLOCK → solve() returns 1 on violation."""
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: BLOCK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}
        code, stdout, _ = run_lemma(rules, ast)
        self.assertEqual(code, 1, f"exit={code} stdout={stdout!r}")
        self.assertIn("BLOCK", stdout)

    def test_action_on_fail_ask_routes_to_exit_2(self):
        """action_on_fail: ASK → violation produces an ASK (exit 2), not a BLOCK.

        This is the wire-through fix: previously solve() ignored the field
        entirely and always returned 1 on a numeric violation.
        """
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: ASK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}
        code, stdout, _ = run_lemma(rules, ast)
        self.assertEqual(
            code, 2, f"ASK should yield exit 2, not BLOCK; exit={code} stdout={stdout!r}"
        )
        self.assertIn("ASK", stdout)
        self.assertIn("transaction_value", stdout)

    def test_action_on_fail_missing_defaults_to_block(self):
        """A rule missing action_on_fail still BLOCKs on violation (safe default).

        axiom_init.py always emits action_on_fail, but hand-written yaml may
        omit it; we must not silently downgrade to ALLOW.
        """
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}
        code, stdout, _ = run_lemma(rules, ast)
        self.assertEqual(code, 1, f"exit={code} stdout={stdout!r}")

    def test_action_on_fail_unknown_value_defaults_to_block(self):
        """An unrecognised action_on_fail value (typo, WARN, etc.) falls back
        to BLOCK rather than downgrading to ALLOW."""
        rules = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: WARN
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}
        code, stdout, _ = run_lemma(rules, ast)
        self.assertEqual(
            code, 1, f"Unknown action_on_fail must default to BLOCK; exit={code} stdout={stdout!r}"
        )

    def test_banned_rule_action_on_fail_ask(self):
        """Banned-shape rules also honour action_on_fail: ASK."""
        rules = textwrap.dedent(
            """\
            rules:
              - concept: auth_hardcoded_id
                banned: true
                action_on_fail: ASK
            """
        )
        ast = {"nodes": [{"concept": "auth_hardcoded_id", "value": 1}]}
        code, stdout, _ = run_lemma(rules, ast)
        self.assertEqual(code, 2, f"exit={code} stdout={stdout!r}")
        self.assertIn("ASK", stdout)

    def test_action_on_missing_block_routes_required_to_exit_1(self):
        """required rules honour action_on_missing: BLOCK as well as ASK."""
        rules_ask = textwrap.dedent(
            """\
            rules:
              - concept: role_assignment
                required: true
                action_on_missing: ASK
            """
        )
        rules_block = textwrap.dedent(
            """\
            rules:
              - concept: role_assignment
                required: true
                action_on_missing: BLOCK
            """
        )
        ast = {"nodes": []}
        code_ask, _, _ = run_lemma(rules_ask, ast)
        code_block, _, _ = run_lemma(rules_block, ast)
        self.assertEqual(code_ask, 2, f"ASK should be exit 2; got {code_ask}")
        self.assertEqual(code_block, 1, f"BLOCK should be exit 1; got {code_block}")


if __name__ == "__main__":
    unittest.main()
