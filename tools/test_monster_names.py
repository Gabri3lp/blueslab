import urllib.request, json

req_headers = {"User-Agent": "Mozilla/5.0"}
m_names = json.loads(urllib.request.urlopen(urllib.request.Request("https://pokemon.brybry.ch/masters/data/lsd/monster_name_en.json", headers=req_headers)).read().decode("utf-8"))
monsters = json.loads(urllib.request.urlopen(urllib.request.Request("https://pokemon.brybry.ch/masters/data/proto/Monster.json", headers=req_headers)).read().decode("utf-8"))

print(f"Total monster names: {len(m_names)}")
print("Sample keys:", list(m_names.items())[:10])

# Check Wally's monster ID
wally_mid = "21028200"
for m in monsters.get("entries", []):
    mid = str(m.get("monsterId", ""))
    if "282" in mid:
        base_id = str(m.get("monsterBaseId", ""))
        print(f"Monster {mid} -> baseId {base_id} -> name in dict: {m_names.get(base_id, m_names.get(mid))}")