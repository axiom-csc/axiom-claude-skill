#!/usr/bin/env python3
import json, re, argparse

def extract_base_entities(text):
    entities = []
    amounts = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)', text)
    for idx, amt in enumerate(amounts):
        clean_val = float(amt.replace(',', ''))
        entities.append({
            "id": f"ent_currency_{idx}",
            "concept": "transaction_value",
            "value": clean_val,
            "type": "currency_usd"
        })
    pct = re.findall(r'([0-9]+(?:\.[0-9]+)?)[%]', text)
    for idx, p in enumerate(pct):
        entities.append({
            "id": f"ent_pct_{idx}",
            "concept": "percentage_value",
            "value": float(p),
            "type": "percentage"
        })
    return entities

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    ast = {"nodes": extract_base_entities(args.input)}
    with open("ast.json", "w") as f:
        json.dump(ast, f, indent=2)
    print(f"[Noema] Lowered {len(ast['nodes'])} Base Entities to ast.json")
