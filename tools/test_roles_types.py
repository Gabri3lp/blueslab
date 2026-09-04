import json

with open('src/BluesLab/wwwroot/locales/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)

with open('src/BluesLab/wwwroot/locales/common_es.json', 'r', encoding='utf-8') as f:
    ces = json.load(f)

for k, v in es.items():
    if k.startswith("type_") or k.startswith("role_"):
        print(f"es: {k} => {v}")

for k, v in ces.items():
    if any(term in k.lower() for term in ["type", "role", "strike", "support", "tech", "sprint", "field", "multi"]):
        print(f"common_es: {k} => {v}")
