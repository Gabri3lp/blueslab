import json, urllib.request

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))

print("Sample BluesLab trainerIds:")
for p in manifest[:5]:
    print(" ", p.get("trainerId"), p.get("trainerBaseId"), p.get("displayName"))

print("\nSample PoMaTools trainerIds with awakeningSkill > 0:")
for p in poma_pairs:
    if p.get("awakeningSkill", 0) > 0:
        print(" ", p.get("id"), p.get("trainerId"), p.get("gridId"))
        if p.get("trainerId") in ["000000", "000001", "000403", "012810"]:
            print("   -> Found key pair:", p.get("trainerId"))