import json

with open('src/BluesLab/wwwroot/locales/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)

for k, v in es.items():
    if k.startswith("pokemon_name_") and any(n in str(v).lower() for n in ["gardevoir", "sylveon", "groudon", "greninja"]):
        print(f"{k} => {v}")
