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

### 2026-11-07 — push attempt + action_on_fail wire-through

- Push attempted after operator pre-auth: blocked by Claude Code auto-mode
  classifier (Remote Repoint reason, even post-repoint). Logged and continued
  per operator standing instruction. `d37c8c1` and `15d4290` still local.
- Local history was reset to `origin/main` and cherry-picked by the harness
  between sessions; first commit is now `d37c8c1` (same patch as the earlier
  `d0ca781`). Clean 2-ahead/0-behind fast-forward against `origin/main`.
- Wired `action_on_fail` / `action_on_missing` through `eval_lemma.solve()`:
  BLOCK → exit 1, ASK → exit 2, missing or unrecognised → BLOCK (safe
  default so a typo cannot downgrade a guardrail to ALLOW). Added a
  `_disposition()` helper and routed both banned and numeric-bound rules.
- Rewrote `test_action_on_fail_is_currently_ignored` into real routing
  coverage; added 5 tests total covering BLOCK, ASK, missing, unknown
  value, banned-shape, and `action_on_missing` on required rules.
- Full suite: 47/47 via `python3 -m unittest discover tests`.
- Updated INVARIANTS_SPEC.md with a disposition-routing table.

Status: wire-through committed locally on top of `15d4290`; three local
commits total held pending unblock of the classifier push gate.

### 2026-11-07 — mode audit: AUDIT and REPAIR not implemented

Audited STRICT/AUDIT/REPAIR against the hook + scripts. Findings:

- No code anywhere parses `[AXIOM: AUDIT]` or `[AXIOM: REPAIR]` prompt
  tags. `grep -rn "AXIOM:"` returns only the SKILL.md documentation line.
- No mode-dispatch logic in `pre_tool_use.py` or any script. Every tool
  call is evaluated under STRICT semantics regardless of what the prompt
  says. REPAIR auto-rewrite is not implemented.
- `AUDIT_LOG` constant in `pre_tool_use.py` writes a decision log on
  every call, which is closer to "always-on audit logging" than the
  documented AUDIT mode — the docs describe AUDIT as a telemetry block
  appended to output, which does not happen.

Edits (honest-docs fix, do not invent capability):

- `SKILL.md` Operational Modes: marked AUDIT and REPAIR as
  "planned, not implemented"; added a note that prompt tags are not
  parsed today.
- `README.md` Modes table: added a Status column; AUDIT/REPAIR rows
  marked "Planned — prompt tag not yet parsed".

Flagged for operator decision: implement AUDIT/REPAIR, or delete the
rows entirely. AUDIT is cheap (already have a decision log and
telemetry — just surface them on an `[AXIOM: AUDIT]` tag). REPAIR is
substantial (needs a code-rewriter). Held out of this pass.
