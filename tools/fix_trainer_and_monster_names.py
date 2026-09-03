import json
import os
import urllib.request
import re

req_headers = {"User-Agent": "Mozilla/5.0"}
url_tb = "https://pokemon.brybry.ch/masters/data/proto/TrainerBase.json"
url_mb = "https://pokemon.brybry.ch/masters/data/proto/MonsterBase.json"
url_tn = "https://pokemon.brybry.ch/masters/data/lsd/trainer_name_en.json"
url_tv = "https://pokemon.brybry.ch/masters/data/lsd/trainer_verbose_name_en.json"
url_mn = "https://pokemon.brybry.ch/masters/data/lsd/monster_name_en.json"

print("Downloading reference tables...")
req = urllib.request.Request(url_tb, headers=req_headers)
with urllib.request.urlopen(req) as resp:
    tb_entries = {str(x["id"]): x for x in json.loads(resp.read().decode("utf-8"))["entries"]}

req = urllib.request.Request(url_mb, headers=req_headers)
with urllib.request.urlopen(req) as resp:
    mb_entries = {str(x["monsterBaseId"]): x for x in json.loads(resp.read().decode("utf-8"))["entries"]}

req = urllib.request.Request(url_tn, headers=req_headers)
with urllib.request.urlopen(req) as resp:
    trainer_names = json.loads(resp.read().decode("utf-8"))

req = urllib.request.Request(url_tv, headers=req_headers)
with urllib.request.urlopen(req) as resp:
    verbose_names = json.loads(resp.read().decode("utf-8"))

req = urllib.request.Request(url_mn, headers=req_headers)
with urllib.request.urlopen(req) as resp:
    monster_names = json.loads(resp.read().decode("utf-8"))

manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest = json.loads(open(manifest_path, encoding="utf-8").read())

fixed_trainers_count = 0
fixed_monsters_count = 0
fixed_display_count = 0
unresolved = []

for p in manifest:
    tid = str(p.get("trainerId", ""))
    old_tname = p.get("trainerName", "")
    old_mname = p.get("monsterName", "")
    old_dname = p.get("displayName", "")
    
    # Read detail if available to get trainerBaseId
    detail_path = os.path.join(pairs_dir, f"{tid}.json")
    t_base_id = ""
    if os.path.exists(detail_path):
        d_json = json.loads(open(detail_path, encoding="utf-8").read())
        t_base_id = str(d_json.get("trainerBaseId", ""))
    
    # Resolve Trainer Name
    vname = verbose_names.get(tid, "").strip()
    tb = tb_entries.get(t_base_id, {})
    alt_tid = tb.get("altTrainerNameId", "")
    tname_id = tb.get("trainerNameId", "")
    actor_id = tb.get("actorId", "")
    
    new_tname = None
    if vname:
        new_tname = re.sub(r'\s+', ' ', vname).strip()
    elif alt_tid and alt_tid in trainer_names:
        new_tname = trainer_names[alt_tid]
    elif tname_id and tname_id in trainer_names:
        new_tname = trainer_names[tname_id]
    elif actor_id and actor_id.startswith("ch"):
        ch_key = actor_id.split("_")[0]
        new_tname = trainer_names.get(ch_key)
    elif actor_id == "hero" or t_base_id.startswith("107") or t_base_id.startswith("108") or tname_id == "ch8000":
        new_tname = "Main Character"
    else:
        new_tname = old_tname
    
    # Resolve Monster Name
    mbid = str(p.get("monsterBaseId", ""))
    mb = mb_entries.get(mbid, {})
    mname_id = str(mb.get("monsterNameId", ""))
    
    new_mname = None
    if mname_id and mname_id in monster_names:
        new_mname = monster_names[mname_id]
    elif mbid in monster_names:
        new_mname = monster_names[mbid]
    elif p.get("pokemonName") and not p.get("pokemonName").startswith("Monster #"):
        new_mname = p.get("pokemonName")
    else:
        new_mname = old_mname

    new_dname = f"{new_tname} & {new_mname}"
    
    if "#" in new_tname or "#" in new_mname:
        unresolved.append((tid, new_tname, new_mname))
    
    if new_tname != old_tname:
        fixed_trainers_count += 1
        p["trainerName"] = new_tname
    if new_mname != old_mname:
        fixed_monsters_count += 1
        p["monsterName"] = new_mname
    if "pokemonName" in p or p.get("monsterName") != p.get("pokemonName"):
        p["pokemonName"] = new_mname
    if new_dname != old_dname:
        fixed_display_count += 1
        p["displayName"] = new_dname

    # Also update pair detail file
    if os.path.exists(detail_path):
        detail = json.loads(open(detail_path, encoding="utf-8").read())
        detail["trainerName"] = new_tname
        detail["monsterName"] = new_mname
        detail["displayName"] = new_dname
        if "pokemonName" in detail:
            detail["pokemonName"] = new_mname
        open(detail_path, "w", encoding="utf-8").write(json.dumps(detail, indent=2, ensure_ascii=False))

# Save updated manifest
open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))

print(f"DONE! Results:")
print(f"  Fixed trainer names: {fixed_trainers_count}")
print(f"  Fixed monster names: {fixed_monsters_count}")
print(f"  Fixed display names: {fixed_display_count}")
print(f"  Unresolved count: {len(unresolved)}")
