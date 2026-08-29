import json, glob

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
role_counts = {}
for p in manifest:
    r = p.get("exRole", "")
    role_counts[r] = role_counts.get(r, 0) + 1

print("Current EX Role distribution in manifest:")
for r, count in sorted(role_counts.items(), key=lambda x: -x[1]):
    print(f"  '{r}': {count}")