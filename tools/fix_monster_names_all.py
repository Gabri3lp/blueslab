import urllib.request, json, os, glob, re

req_headers = {"User-Agent": "Mozilla/5.0"}
m_names = json.loads(urllib.request.urlopen(urllib.request.Request("https://pokemon.brybry.ch/masters/data/lsd/monster_name_en.json", headers=req_headers)).read().decode("utf-8"))

def resolve_monster_name(raw_id):
    if raw_id in m_names:
        return m_names[raw_id]
    if len(raw_id) >= 8 and raw_id.startswith("210"):
        norm_id = "200" + raw_id[3:]
        if norm_id in m_names:
            return m_names[norm_id]
    if len(raw_id) >= 8 and raw_id.startswith("200") and raw_id[6:8] != "00":
        norm_id = raw_id[:6] + "00"
        if norm_id in m_names:
            return m_names[norm_id]
    if len(raw_id) >= 10:
        norm_id = "200" + raw_id[3:8]
        if norm_id in m_names:
            return m_names[norm_id]
    return None

manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
pairs_dir = "src/BluesLab/wwwroot/data/pairs"

manifest = json.loads(open(manifest_path, encoding="utf-8").read())
fixed_count = 0

for p in manifest:
    if "monster #" in p["displayName"].lower():
        m_num = re.search(r'Monster #(\d+)', p["displayName"])
        if m_num:
            raw_id = m_num.group(1)
            real_name = resolve_monster_name(raw_id)
            if real_name:
                old_name = p["displayName"]
                new_name = p["displayName"].replace(f"Monster #{raw_id}", real_name)
                p["displayName"] = new_name
                p["pokemonName"] = real_name
                fixed_count += 1

                tid = str(p["trainerId"])
                detail_path = os.path.join(pairs_dir, f"{tid}.json")
                if os.path.exists(detail_path):
                    detail = json.loads(open(detail_path, encoding="utf-8").read())
                    detail["displayName"] = new_name
                    detail["pokemonName"] = real_name
                    open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))

open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"Fixed {fixed_count} monster names in manifest and pair JSONs.")