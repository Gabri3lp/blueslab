import json, re, urllib.request

# 1. Check move_scaling in damage_rules.json
rules = json.loads(open("src/BluesLab/wwwroot/data/damage_rules.json", encoding="utf-8").read())
move_scalings = rules.get("moveScaling", [])
print(f"Total moveScaling rules in damage_rules.json: {len(move_scalings)}")

unique_types = set()
for ms in move_scalings:
    stat = ms.get("stat")
    who = ms.get("who")
    direction = ms.get("direction")
    step = ms.get("step_per_1000")
    cap = ms.get("cap_per_1000")
    unique_types.add((who, stat, direction, step, cap))

print(f"Distinct move scaling formulas in damage_rules.json: {len(unique_types)}")
for ut in sorted(unique_types, key=lambda x: str(x)):
    print(" ", ut)

# 2. Inspect PoMaTools main JS for any custom move/sync scaling logic
url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'innateModifier|moveScaling|scaling|calculateMoveDamage|innateValue|uniqueScaling', js, re.I)]
print(f"\nOccurrences in PoMaTools JS: {len(matches)}")
for idx in matches[:10]:
    print("--- SNIPPET ---")
    print(js[max(0, idx-50):min(len(js), idx+300)])