import json, glob, urllib.request

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))

poma_map = {}
for p in poma_pairs:
    tid = p.get("trainerId")
    pkm = p.get("pokemon", [{}])[0].get("id")
    if tid and pkm:
        poma_map[tid] = pkm

print("Total PoMaTools pairs:", len(poma_pairs))
print("Sample mappings (trainerId -> pokemonId):")
for tid, pkm in list(poma_map.items())[:10]:
    print(f"  {tid} -> {pkm}")