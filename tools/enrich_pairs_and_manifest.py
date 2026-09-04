import os
import glob
import json
import urllib.request
import re

print("=== 1. Fetching AbilityPanel.json & TrainerBase.json ===")
panel_url = "https://pokemon.brybry.ch/masters/data/proto/AbilityPanel.json"
panel_data = json.loads(urllib.request.urlopen(urllib.request.Request(panel_url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8'))
panel_map = {p['cellId']: p['abilityId'] for p in panel_data.get('entries', []) if 'cellId' in p and 'abilityId' in p}
print(f"Loaded {len(panel_map)} AbilityPanel entries.")

tb_url = "https://pokemon.brybry.ch/masters/data/proto/TrainerBase.json"
tb_data = json.loads(urllib.request.urlopen(urllib.request.Request(tb_url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8'))
tb_map = {str(e['id']): e for e in tb_data.get('entries', [])}
print(f"Loaded {len(tb_map)} TrainerBase entries.")

with open('src/BluesLab/wwwroot/locales/en.json', 'r', encoding='utf-8') as f:
    en_dict = json.load(f)

pairs_dir = "src/BluesLab/wwwroot/data/pairs"
manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"

print("=== 2. Enriching pairs/*.json with abilityId ===")
pair_files = glob.glob(f"{pairs_dir}/*.json")
cells_updated = 0
files_updated = 0

for pf in pair_files:
    with open(pf, 'r', encoding='utf-8-sig') as inf:
        pair_data = json.load(inf)
    
    changed = False
    for cell in pair_data.get('grid', []):
        cid = cell.get('cellId')
        if cid in panel_map:
            ab_id = panel_map[cid]
            if cell.get('abilityId') != ab_id:
                cell['abilityId'] = ab_id
                changed = True
                cells_updated += 1
    
    if changed:
        with open(pf, 'w', encoding='utf-8') as outf:
            json.dump(pair_data, outf, indent=2, ensure_ascii=False)
        files_updated += 1

print(f"Enriched {cells_updated} cells across {files_updated} pair files.")

print("=== 3. Enriching pairs_manifest.json with trainerBaseId, trainerKey, pokemonKey ===")
with open(manifest_path, 'r', encoding='utf-8-sig') as f:
    manifest = json.load(f)

def get_trainer_key(tid, t_base_id):
    if f"trainer_name_{tid}" in en_dict:
        return str(tid)
    tb = tb_map.get(str(t_base_id))
    if tb:
        alt_id = tb.get('altTrainerNameId')
        if alt_id and f"trainer_name_{alt_id}" in en_dict:
            return str(alt_id)
        tname_id = tb.get('trainerNameId')
        if tname_id and f"trainer_name_{tname_id}" in en_dict:
            return str(tname_id)
        actor_id = tb.get('actorId', '')
        if actor_id.startswith("ch"):
            ch = actor_id.split("_")[0]
            if f"trainer_name_{ch}" in en_dict:
                return str(ch)
    return str(tid)

def get_pokemon_key(mb_id):
    raw = str(mb_id)
    candidates = [
        raw,
        f"200{raw[3:]}" if raw.startswith("210") else None,
        f"{raw[:6]}00" if len(raw) >= 8 else None,
        f"200{raw[3:8]}" if len(raw) >= 10 else None
    ]
    for c in candidates:
        if c and f"pokemon_name_{c}" in en_dict:
            return c
    return raw

for p in manifest:
    tid = str(p.get('trainerId', ''))
    mb_id = str(p.get('monsterBaseId', ''))
    
    # Read detail to get trainerBaseId
    pf = os.path.join(pairs_dir, f"{tid}.json")
    t_base_id = ""
    if os.path.exists(pf):
        with open(pf, 'r', encoding='utf-8-sig') as df:
            detail = json.load(df)
            t_base_id = str(detail.get('trainerBaseId', ''))
    
    tr_key = get_trainer_key(tid, t_base_id)
    pk_key = get_pokemon_key(mb_id)
    
    p['trainerBaseId'] = t_base_id
    p['trainerKey'] = tr_key
    p['pokemonKey'] = pk_key

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"Manifest enriched for {len(manifest)} pairs.")
print("Sample manifest entry:", json.dumps(manifest[0], indent=2, ensure_ascii=False))
