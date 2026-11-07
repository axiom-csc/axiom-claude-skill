#!/usr/bin/env python3
"""Regression tests for YAML rule-key handling in eval_lemma.

Pins two behaviours that were previously doc/code mismatches:

1. Rules key on ``concept:`` (the code reads ``current['concept']``).
2. A rule written with ``field:`` is silently dropped by the built-in
   YAML parser, so the user's threshold never applies and the baked-in
   DEFAULT_RULES limit stays in force.

Also documents (not enforces) the fact that ``action_on_fail`` is
currently metadata — ``solve()`` never reads it. If a future change
wires it up, ``test_action_on_fail_is_currently_ignored`` will fail
and this file + INVARIANTS_SPEC.md should be revisited together.
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

    def test_action_on_fail_is_currently_ignored(self):
        """Documents current behaviour: eval_lemma.solve() never reads the
        'action_on_fail' field. A violating numeric rule produces a BLOCK
        regardless of whether action_on_fail is 'BLOCK', 'ASK', 'WARN', or
        omitted entirely.

        If a future change wires action_on_fail through to the disposition,
        this test will fail — update INVARIANTS_SPEC.md accordingly and
        rewrite this test to assert the new routing instead of deleting it.
        """
        rules_without = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
            """
        )
        rules_with_ask = textwrap.dedent(
            """\
            rules:
              - concept: transaction_value
                op: lte
                value: 50000
                action_on_fail: ASK
            """
        )
        ast = {"nodes": [{"concept": "transaction_value", "value": 75000}]}

        code_a, stdout_a, _ = run_lemma(rules_without, ast)
        code_b, stdout_b, _ = run_lemma(rules_with_ask, ast)

        self.assertEqual(
            code_a,
            1,
            f"Rule missing action_on_fail should still BLOCK today; "
            f"exit={code_a} stdout={stdout_a!r}",
        )
        self.assertEqual(
            code_b,
            1,
            f"action_on_fail=ASK is currently ignored and the rule still "
            f"BLOCKs; exit={code_b} stdout={stdout_b!r}",
        )


if __name__ == "__main__":
    unittest.main()
