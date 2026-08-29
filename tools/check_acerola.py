import json, glob

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
for p in manifest:
    if "mimikyu" in p["displayName"].lower() or "acerola" in p["displayName"].lower():
        tid = p["trainerId"]
        print(f"=== {p['displayName']} (ID: {tid}) ===")
        print("Manifest exRole:", p.get("exRole"))
        print("Manifest role:", p.get("role"))
        detail = json.loads(open(f"src/BluesLab/wwwroot/data/pairs/{tid}.json", encoding="utf-8").read())
        print("Detail exRole:", detail.get("exRole"))
        print("Detail role:", detail.get("role"))
        print("HasEX:", detail.get("hasEx"))