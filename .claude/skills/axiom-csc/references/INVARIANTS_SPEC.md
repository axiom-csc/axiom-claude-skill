# Axiom Invariants — 3-State Epistemic Specification

## Tri-State Logic

Every Base Entity evaluation resolves to exactly one state:

| State   | Meaning                                          | Action           |
|---------|--------------------------------------------------|------------------|
| TRUE    | Value extracted, rule satisfied                  | Continue         |
| FALSE   | Value extracted, rule violated                   | BLOCK            |
| UNKNOWN | Required value absent from context               | ASK (STRICT: halt) |

## Standard Invariants

### Financial Bounds
- `transaction_value` must satisfy `lte 10000` (configurable via `.axiom/invariants.yaml`)
- Applies to: invoice totals, payment amounts, transfer values

### Fail-Closed Guarantee
In STRICT mode, any UNKNOWN state halts execution immediately.
Claude must issue a single targeted micro-query naming the exact missing variable.

## Configuring Custom Rules

Create `.axiom/invariants.yaml` in your project root:

```yaml
rules:
  - concept: transaction_value
    op: lte
    value: 50000
    action_on_fail: BLOCK
  - concept: percentage_value
    op: lte
    value: 100
    action_on_fail: BLOCK
```

Supported operators: `lte`, `gte`, `lt`, `gt`, `eq`

### Rule shapes

| Shape | Fields | Meaning |
|-------|--------|---------|
| Numeric bound | `concept`, `op`, `value`, `action_on_fail` | Fail if extracted value violates `op value` |
| Banned entity | `concept`, `banned: true`, `action_on_fail` | Fail if any matching entity is found |
| Required entity | `concept`, `required: true`, `action_on_missing` | ASK if the entity is not found in context |
