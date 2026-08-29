import urllib.request, json, os, glob

req_headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/data/proto/TrainerExRole.json"
req = urllib.request.Request(url, headers=req_headers)
data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
entries = data.get("entries", [])

EX_ROLE_NAMES = {
    0: "Strike (Physical)",
    1: "Strike (Special)",
    2: "Support",
    3: "Tech",
    4: "Sprint",
    5: "Field",
    6: "Multi"
}

trainer_ex_map = {}
for e in entries:
    tid = str(e.get("trainerId", ""))
    role_id = e.get("role", -1)
    if role_id in EX_ROLE_NAMES:
        trainer_ex_map[tid] = EX_ROLE_NAMES[role_id]

print(f"Loaded {len(trainer_ex_map)} EX Role mappings.")

pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"

manifest = json.loads(open(manifest_path, encoding="utf-8").read())

updated_count = 0
ex_counts = {}

for p in manifest:
    tid = str(p["trainerId"])
    real_ex = trainer_ex_map.get(tid, "")
    p["exRole"] = real_ex
    ex_counts[real_ex] = ex_counts.get(real_ex, 0) + 1

    detail_path = os.path.join(pairs_dir, f"{tid}.json")
    if os.path.exists(detail_path):
        detail = json.loads(open(detail_path, encoding="utf-8").read())
        detail["exRole"] = real_ex
        open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))
        updated_count += 1

open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))

print(f"Updated {updated_count} pairs and manifest.json.")
print("New EX Role distribution:")
for r, count in sorted(ex_counts.items(), key=lambda x: -x[1]):
    print(f"  '{r}': {count}")