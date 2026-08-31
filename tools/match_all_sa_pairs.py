import json, os, urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
en = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/i18n/en.json", headers=headers)).read().decode("utf-8"))
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers=headers)).read().decode("utf-8"))

manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest = json.loads(open(manifest_path, encoding="utf-8").read())

# Build mapping from poma
poma_by_tid = {}
poma_by_name = {}
for p in poma_pairs:
    askill = p.get("awakeningSkill", 0)
    if askill > 0:
        skill_info = en["DATA"]["SKILLS"].get(str(askill), {})
        t_id = p.get("trainerId", "")
        pkm_id = p.get("pokemon", [{}])[0].get("id", "")
        t_name = en["DATA"]["CHAR"].get(t_id, "")
        pkm_name = en["DATA"]["PKMN"].get(pkm_id, "")

        sa_obj = {
            "name": skill_info.get("NAME", ""),
            "description": skill_info.get("DESC", "")
        }

        b_tid = "1" + t_id.zfill(6) + "0000"
        poma_by_tid[b_tid] = sa_obj
        poma_by_tid[t_id] = sa_obj
        if t_name and pkm_name:
            norm_name = re.sub(r'[^a-zA-Z0-9]', '', f"{t_name}{pkm_name}".lower())
            poma_by_name[norm_name] = sa_obj

total_sa = 0
for p in manifest:
    tid = str(p.get("trainerId", ""))
    sa_info = poma_by_tid.get(tid)
    if not sa_info:
        norm_d = re.sub(r'[^a-zA-Z0-9]', '', p.get("displayName", "").lower())
        sa_info = poma_by_name.get(norm_d)

    if sa_info:
        total_sa += 1
        p["superAwakeningPassive"] = sa_info
        p["hasSuperAwakening"] = True
        detail_path = os.path.join(pairs_dir, f"{tid}.json")
        if os.path.exists(detail_path):
            detail = json.loads(open(detail_path, encoding="utf-8").read())
            detail["superAwakeningPassive"] = sa_info
            detail["hasSuperAwakening"] = True
            open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))

open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"Total SA pairs enriched: {total_sa} / {len(manifest)} pairs in BluesLab!")