import json, os, urllib.request, glob

headers = {"User-Agent": "Mozilla/5.0"}
en = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/i18n/en.json", headers=headers)).read().decode("utf-8"))
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers=headers)).read().decode("utf-8"))

poma_sa_map = {}
for p in poma_pairs:
    askill = p.get("awakeningSkill", 0)
    tid = p.get("trainerId", "")
    if askill > 0 and tid:
        skill_info = en["DATA"]["SKILLS"].get(str(askill), {})
        if skill_info:
            poma_sa_map[tid] = {
                "name": skill_info.get("NAME", ""),
                "description": skill_info.get("DESC", "")
            }
            # Also full 11-digit
            poma_sa_map["10" + tid + "000"] = poma_sa_map[tid]

pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
manifest = json.loads(open(manifest_path, encoding="utf-8").read())

enriched = 0
for p in manifest:
    tid = str(p.get("trainerId", ""))
    short_tid = tid[2:8] if len(tid) >= 8 else tid
    sa_info = poma_sa_map.get(short_tid) or poma_sa_map.get(tid)
    if sa_info:
        p["superAwakeningPassive"] = sa_info
        enriched += 1

        detail_path = os.path.join(pairs_dir, f"{tid}.json")
        if os.path.exists(detail_path):
            detail = json.loads(open(detail_path, encoding="utf-8").read())
            detail["superAwakeningPassive"] = sa_info
            open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))

open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"Enriched {enriched} sync pairs with superAwakeningPassive.")