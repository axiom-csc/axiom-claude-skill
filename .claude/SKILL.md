---
name: axiom-csc
description: Continuous Structural Compiler for deterministic AI state execution. Enforces Tri-State logic invariants on Claude Code outputs.
---

# Axiom Core: Continuous Structural Compiler (CSC)

When executing tasks or generating code, enforce the three-pillar Axiom Core evaluation framework:

## 1. Noema (Perception & AST Lowering)
- Lower all incoming natural language requirements, schemas, or agent responses into a typed `AxiomGraph` consisting of tuples: `(id, concept, value, type)`.
- Never evaluate rules against unstructured text strings; always isolate concrete Base Entities first.

## 2. Lemma (Deterministic Logic Solver)
- Evaluate extracted Base Entities against declarative rulesets using deterministic relational logic.
- Do not use statistical likelihood or guesswork for hard numeric bounds, financial limits, or access constraints.
- If a value violates a rule, output an explicit `AxiomConstraintViolation` with the failing parameters.

## 3. Manam (Tri-State Epistemic Controller)
- Enforce strict 3-State Epistemic Logic: `TRUE | FALSE | UNKNOWN`.
- If a required Base Entity node cannot be extracted from the context, mark the state as `UNKNOWN`.
- On `UNKNOWN`, fail-closed immediately and generate a targeted clarifying micro-query to isolate the exact missing variable.
