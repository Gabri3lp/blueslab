import json, glob

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
for p in manifest:
    if "wally" in p["displayName"].lower():
        print(p["displayName"], p["trainerId"])
        detail = json.loads(open(f"src/BluesLab/wwwroot/data/pairs/{p['trainerId']}.json", encoding="utf-8").read())
        print("  Base stats:", detail["stats"])
        print("  Variations:", detail.get("variations"))