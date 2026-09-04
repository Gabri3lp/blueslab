import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/BluesLab/wwwroot/locales/common_es.json', 'r', encoding='utf-8') as f:
    ces = json.load(f)

print(f"Total keys in common_es.json: {len(ces)}")
for k, v in list(ces.items())[:50]:
    print(f"  {k} => {v}")
