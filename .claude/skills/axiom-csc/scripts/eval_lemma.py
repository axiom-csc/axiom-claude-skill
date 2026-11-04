#!/usr/bin/env python3
import json, sys, pathlib, argparse

OPS = {"lte": lambda a,b: a<=b, "gte": lambda a,b: a>=b, "lt": lambda a,b: a<b, "gt": lambda a,b: a>b, "eq": lambda a,b: a==b}

DEFAULT_RULES = {"rules": [
    {"concept": "transaction_value", "op": "lte", "value": 10000, "action_on_fail": "BLOCK"},
    {"concept": "rate_limit_rpm",    "op": "lte", "value": 1000,  "action_on_fail": "BLOCK"},
    {"concept": "file_size_mb",      "op": "lte", "value": 100,   "action_on_fail": "BLOCK"},
    {"concept": "query_row_limit",   "op": "lte", "value": 10000, "action_on_fail": "BLOCK"},
    {"concept": "percentage_value",  "op": "lte", "value": 100,   "action_on_fail": "BLOCK"},
    {"concept": "retry_count",       "op": "lte", "value": 10,    "action_on_fail": "BLOCK"},
    {"concept": "role_assignment",   "required": True,             "action_on_missing": "ASK"},
    {"concept": "api_quota_daily",   "required": True,             "action_on_missing": "ASK"},
]}

ASK_Q = {
    "role_assignment": "What explicit permissions should this role hold? (e.g., users:read, users:write)",
    "api_quota_daily": "What is the authorized daily API quota for this service?",
}

def load_rules(path):
    p = pathlib.Path(path)
    if not p.exists(): return DEFAULT_RULES
    try:
        import yaml; return yaml.safe_load(p.read_text())
    except ImportError:
        return json.loads(p.read_text())

def solve(ast_path, rules_path):
    try: ast = json.loads(pathlib.Path(ast_path).read_text())
    except FileNotFoundError:
        print("[Lemma]  ERROR: ast.json not found"); return 1
    rules = load_rules(rules_path).get("rules", [])
    nodes_by = {}
    for n in ast.get("nodes", []): nodes_by.setdefault(n["concept"], []).append(n)
    blocks, asks = [], []
    for rule in rules:
        concept = rule["concept"]
        nodes = nodes_by.get(concept, [])
        if rule.get("required") and not nodes:
            asks.append((concept, ASK_Q.get(concept, f"What is '{concept}'?")))
            continue
        if "op" in rule:
            op_fn = OPS.get(rule["op"])
            for n in nodes:
                if op_fn and not op_fn(n["value"], rule["value"]):
                    blocks.append((concept, n["value"], rule["op"], rule["value"]))
    for concept, actual, op, bound in blocks:
        print(f"\u274c [Lemma BLOCK] AxiomConstraintViolation: {concept} = {actual} violates {op} {bound}")
    for concept, q in asks:
        print(f"\u2753 [Lemma ASK] UNKNOWN: '{concept}' — {q}")
    if blocks: return 1
    if asks: return 2
    print(f"\u2705 [Lemma ALLOW] All {len(rules)} invariant checks passed.")
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ast", default="ast.json")
    p.add_argument("--rules", default=".axiom/invariants.yaml")
    args = p.parse_args()
    sys.exit(solve(args.ast, args.rules))
