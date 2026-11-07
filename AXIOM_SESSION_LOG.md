# Axiom Session Log

## Progress

### 2026-11-07 — skill-polish pass (teammate `skill-polish`)

Polish pass against the shipped distribution. Commit `d0ca781` (local, not pushed).

Edits (6 files):
- `install.sh` — `AXIOM_VERSION` 1.2.1 → 1.2.2 (matches README/run_demo.sh install URLs); dropped stale "protecting 5 failure domains" line (actual DEFAULT_RULES: 13 concepts).
- `.claude/skills/axiom-csc/hooks/pre_tool_use.py` — `SKILL_VERSION` 1.2.1 → 1.2.2.
- `.claude/skills/axiom-csc/SKILL.md` — frontmatter `version` 1.0.0 → 1.2.2.
- `.claude/skills/axiom-csc/scripts/axiom.py` — telemetry `axiom_version` 1.0.0 → 1.2.2.
- `.claude/skills/axiom-csc/references/INVARIANTS_SPEC.md` — YAML example key `field:` → `concept:` (code keys on `concept`; `field` silently no-ops); added missing `action_on_fail`; added rule-shapes table.
- `CONTRIBUTING.md` — "Python 3.10+" → "Python 3.8+" (matches installer and COMPATIBILITY.md); fixed three Extension-section paths to `.claude/skills/axiom-csc/scripts/...`.

Infra:
- Remote repointed: `origin` was `github.com/axiom-csc/axiom-skill.git` → now `github.com/axiom-csc/axiom-claude-skill.git` (canonical, confirmed by operator).

Status:
- Commit `d0ca781` on local `main`.
- Push to `origin/main` awaiting operator authorization (classifier denied automated push).
- Next task on deck: regression tests covering `concept` vs `field` key and required `action_on_fail` field — held until push lands.

Flagged, not changed:
- Untracked `hn_comment.txt` at repo root — out of polish scope.
- `PRIVACY.md` "This policy applies to Axiom CSC v1.0.0 and later" — historical statement, left alone.

### 2026-11-07 — regression tests for concept/field + action_on_fail

Added `tests/test_rule_keys.py` with 4 tests pinning the rule-key behaviour
behind commit `d0ca781`:

- `test_concept_key_raises_the_bound` — concept-keyed rule with higher
  value overrides the DEFAULT_RULES cap.
- `test_field_key_is_silently_dropped` — rule written with `field:` is
  dropped by `_parse_yaml_rules`, so the DEFAULT_RULES cap stays in
  force. This is the regression the INVARIANTS_SPEC.md fix prevents.
- `test_concept_key_blocks_when_exceeded` — sanity: concept-keyed rule
  still BLOCKs its own violations.
- `test_action_on_fail_is_currently_ignored` — documents that
  `eval_lemma.solve()` never reads `action_on_fail`; both a rule
  missing the field and a rule with `action_on_fail: ASK` still return
  exit 1 (BLOCK). Flagged below; fail-on-change is intentional so
  future wiring prompts a spec update.

Full suite: 42/42 pass via `python3 -m unittest discover tests`.

Flagged for operator decision:
- `action_on_fail` and `action_on_missing` are written by
  `axiom_init.py`, set in `DEFAULT_RULES`, and documented in
  INVARIANTS_SPEC.md / README, but never consulted by eval_lemma or
  the hook. The disposition (BLOCK vs ASK) is inferred from whether
  the rule is `op`-shaped or `required`-shaped, not from the field
  value. Two possible fixes: (a) wire `action_on_fail` through
  `solve()`, or (b) drop the field from docs and the init template.
  Staying out of scope for this polish pass — flagging for your call.

Status: new commit staged on top of `d0ca781`, awaiting operator push
authorization alongside the first commit.
