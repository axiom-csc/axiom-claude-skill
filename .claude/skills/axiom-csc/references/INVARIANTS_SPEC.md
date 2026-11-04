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
  - field: transaction_value
    op: lte
    value: 50000
  - field: percentage_value
    op: lte
    value: 100
```

Supported operators: `lte`, `gte`, `lt`, `gt`, `eq`
