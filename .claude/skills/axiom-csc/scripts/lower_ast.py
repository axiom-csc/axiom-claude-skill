#!/usr/bin/env python3
import json, re, argparse, pathlib, sys

PATTERNS = [
    ("transaction_value", r'\$([0-9,]+(?:\.[0-9]{2})?)', "currency_usd", float),
    ("rate_limit_rpm",    r'(\d+)\s*(?:req|requests|calls)\s*/\s*min', "rate_rpm", float),
    ("rate_limit_rps",    r'(\d+)\s*(?:req|requests|calls)\s*/\s*sec', "rate_rps", float),
    ("rate_limit_rpd",    r'(\d+)\s*(?:req|requests|calls)\s*/\s*day', "rate_rpd", float),
    ("file_size_mb",      r'(\d+(?:\.\d+)?)\s*MB', "size_mb", float),
    ("file_size_gb",      r'(\d+(?:\.\d+)?)\s*GB', "size_gb", float),
    ("query_row_limit",   r'LIMIT\s+(\d+)', "db_rows", int),
    ("timeout_seconds",   r'timeout[=:\s]+(\d+)\s*s', "seconds", int),
    ("role_assignment",   r'(?:role|permission|scope)\s*[:=]\s*["\']?(\w+)["\']?', "role_string", str),
    ("api_quota_daily",   r'(\d+)\s*(?:calls?|requests?)\s*(?:per|/)\s*day', "api_calls_day", int),
    ("percentage_value",  r'(\d+(?:\.\d+)?)\s*%', "percentage", float),
    ("retry_count",       r'(?:retries?|retry)\s*[:=]?\s*(\d+)', "count", int),
]

def extract(text):
    entities, seen = [], set()
    for concept, pattern, type_label, cast in PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            raw = m.group(1).replace(',', '')
            try: val = cast(raw)
            except ValueError: val = raw
            key = (concept, str(val))
            if key in seen: continue
            seen.add(key)
            entities.append({"id": f"ent_{concept}_{len(entities)}", "concept": concept, "value": val, "type": type_label, "source": m.group(0).strip()})
    return entities

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", default="ast.json")
    args = p.parse_args()
    nodes = extract(args.input)
    pathlib.Path(args.out).write_text(json.dumps({"nodes": nodes}, indent=2))
    for n in nodes: print(f"[Noema]  {n['concept']} = {n['value']} ({n['type']})")
    print(f"[Noema]  {len(nodes)} Base Entities -> {args.out}")
