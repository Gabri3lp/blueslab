import json

rules = json.loads(open("src/BluesLab/wwwroot/data/damage_rules.json", encoding="utf-8").read())
move_scalings = rules.get("moveScaling", [])
stats = set(ms.get("stat") for ms in move_scalings)
print("All distinct stats used in moveScaling:")
for s in sorted(stats):
    print(" ", s)