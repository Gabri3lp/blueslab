import json, glob, os, urllib.request

req_headers = {"User-Agent": "Mozilla/5.0"}
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers=req_headers)).read().decode("utf-8"))

# Build mapping from trainerId / gridId / id
poma_by_tid = {}
for p in poma_pairs:
    tid = p.get("trainerId", "")
    pkm = p.get("pokemon", [{}])[0].get("id", "")
    if tid and pkm:
        poma_by_tid[tid] = pkm
        # also full 11-digit format e.g. 10128100000 -> "1" + tid + "0000"
        full_tid = "10" + tid + "000"
        poma_by_tid[full_tid] = pkm

manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest = json.loads(open(manifest_path, encoding="utf-8").read())

updated = 0
for p in manifest:
    tid = str(p.get("trainerId", ""))
    # tid in BluesLab is like 10128100000 or 10000000000
    # short tid is tid[2:8] e.g. 10000000000 -> 000000, 10128100000 -> 012810
    short_tid = tid[2:8] if len(tid) >= 8 else tid
    pkm_id = poma_by_tid.get(short_tid) or poma_by_tid.get(tid)
    
    if not pkm_id:
        # Fallback from monsterBaseId if available
        mb_id = str(p.get("monsterBaseId", ""))
        if len(mb_id) >= 8:
            pkm_id = mb_id[2:8]

    if pkm_id:
        pkm_icon_url = f"img/pokemon/{pkm_id}_128.png"
        p["pokemonIconUrl"] = pkm_icon_url
        updated += 1

        detail_path = os.path.join(pairs_dir, f"{tid}.json")
        if os.path.exists(detail_path):
            detail = json.loads(open(detail_path, encoding="utf-8").read())
            detail["pokemonIconUrl"] = pkm_icon_url
            open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))

open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"Added pokemonIconUrl to {updated} / {len(manifest)} sync pairs.")