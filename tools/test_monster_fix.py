import urllib.request, json

req_headers = {"User-Agent": "Mozilla/5.0"}
m_names = json.loads(urllib.request.urlopen(urllib.request.Request("https://pokemon.brybry.ch/masters/data/lsd/monster_name_en.json", headers=req_headers)).read().decode("utf-8"))
monsters = json.loads(urllib.request.urlopen(urllib.request.Request("https://pokemon.brybry.ch/masters/data/proto/Monster.json", headers=req_headers)).read().decode("utf-8"))

def get_pokemon_name(base_id_str):
    if base_id_str in m_names:
        return m_names[base_id_str]
    # Try normalizing shiny / variant prefix e.g. 21028200 -> 20028200
    if len(base_id_str) >= 8 and base_id_str.startswith("210"):
        norm_id = "200" + base_id_str[3:]
        if norm_id in m_names:
            return m_names[norm_id]
    if len(base_id_str) >= 8 and base_id_str.startswith("200") and base_id_str[6:8] != "00":
        norm_id = base_id_str[:6] + "00"
        if norm_id in m_names:
            return m_names[norm_id]
    # Try last 6 digits with 200 prefix
    if len(base_id_str) >= 6:
        dex_part = base_id_str[-5:-2] if len(base_id_str) >= 8 else base_id_str[-4:-2]
        # scan m_names for matching
    return None

manifest = json.loads(open("src/BluesLab/wwwroot/data/pairs_manifest.json", encoding="utf-8").read())
fixed = 0
for p in manifest:
    if "monster #" in p["displayName"].lower():
        # find monsterBaseId
        tid = p["trainerId"]
        detail = json.loads(open(f"src/BluesLab/wwwroot/data/pairs/{tid}.json", encoding="utf-8").read())
        # extract number from Monster #XXXX
        import re
        m_num = re.search(r'Monster #(\d+)', p["displayName"])
        if m_num:
            raw_id = m_num.group(1)
            name = get_pokemon_name(raw_id)
            if name:
                fixed += 1
                if fixed <= 10:
                    print(f"{p['displayName']} -> {name}")

print(f"Total resolved: {fixed} / 162")