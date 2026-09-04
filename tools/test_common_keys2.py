import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/BluesLab/wwwroot/locales/common_es.json', 'r', encoding='utf-8') as f:
    ces = json.load(f)

for k, v in ces.items():
    if any(term in k for term in ["search", "filter", "stat", "move", "passive", "sync", "overview", "damage", "grid", "hp", "atk", "def", "speed", "energy", "level"]):
        print(f"  {k} => {v}")
