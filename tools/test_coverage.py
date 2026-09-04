import json

with open('src/BluesLab/wwwroot/locales/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)

with open('src/BluesLab/wwwroot/data/pairs_manifest.json', 'r', encoding='utf-8-sig') as f:
    manifest = json.load(f)

pairs_dir = "src/BluesLab/wwwroot/data/pairs"

matched_trainers = 0
unmatched_trainers = []
matched_pokemon = 0
unmatched_pokemon = []

for p in manifest:
    tid = p['trainerId']
    mb_id = p.get('monsterBaseId', '')
    
    # Check detail for trainerBaseId
    try:
        with open(f"{pairs_dir}/{tid}.json", 'r', encoding='utf-8-sig') as df:
            detail = json.load(df)
            t_base_id = detail.get('trainerBaseId', '')
    except Exception:
        t_base_id = ''

    # Test trainer lookup
    tr_name = es.get(f"trainer_name_{tid}")
    if not tr_name and t_base_id:
        try:
            ch_key = f"trainer_name_ch{int(t_base_id):04d}"
            tr_name = es.get(ch_key)
        except Exception:
            pass
    if tr_name:
        matched_trainers += 1
    else:
        unmatched_trainers.append((tid, p.get('trainerName'), t_base_id))

    # Test pokemon lookup
    pk_name = es.get(f"pokemon_name_{mb_id}")
    if pk_name:
        matched_pokemon += 1
    else:
        unmatched_pokemon.append((mb_id, p.get('monsterName')))

print(f"Total pairs: {len(manifest)}")
print(f"Matched trainers: {matched_trainers} / {len(manifest)}")
if unmatched_trainers:
    print(f"Unmatched trainers sample ({len(unmatched_trainers)}):", unmatched_trainers[:10])

print(f"Matched pokemon: {matched_pokemon} / {len(manifest)}")
if unmatched_pokemon:
    print(f"Unmatched pokemon sample ({len(unmatched_pokemon)}):", unmatched_pokemon[:10])
