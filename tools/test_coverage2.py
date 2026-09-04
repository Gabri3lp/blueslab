import json
import urllib.request

with open('src/BluesLab/wwwroot/locales/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)

with open('src/BluesLab/wwwroot/data/pairs_manifest.json', 'r', encoding='utf-8-sig') as f:
    manifest = json.load(f)

url = "https://pokemon.brybry.ch/masters/data/proto/TrainerBase.json"
tb_data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8'))
tb_map = {e['id']: e for e in tb_data.get('entries', [])}

pairs_dir = "src/BluesLab/wwwroot/data/pairs"

def get_pokemon_name(mb_id):
    for candidate in [
        f"pokemon_name_{mb_id}",
        f"pokemon_name_200{mb_id[3:]}" if mb_id.startswith("210") else None,
        f"pokemon_name_{mb_id[:6]}00" if len(mb_id) >= 8 else None,
        f"pokemon_name_200{mb_id[3:8]}" if len(mb_id) >= 10 else None
    ]:
        if candidate and candidate in es:
            return es[candidate]
    return None

def get_trainer_name(tid, t_base_id):
    # 1. Direct trainer_name_{tid}
    if f"trainer_name_{tid}" in es:
        return es[f"trainer_name_{tid}"]
    # 2. Via TrainerBase
    tb = tb_map.get(t_base_id)
    if tb:
        alt_id = tb.get('altTrainerNameId')
        if alt_id and f"trainer_name_{alt_id}" in es:
            return es[f"trainer_name_{alt_id}"]
        tname_id = tb.get('trainerNameId')
        if tname_id and f"trainer_name_{tname_id}" in es:
            return es[f"trainer_name_{tname_id}"]
        actor_id = tb.get('actorId', '')
        if actor_id.startswith("ch"):
            ch = actor_id.split("_")[0]
            if f"trainer_name_{ch}" in es:
                return es[f"trainer_name_{ch}"]
    return None

matched_trainers = 0
unmatched_trainers = []
matched_pokemon = 0
unmatched_pokemon = []

for p in manifest:
    tid = p['trainerId']
    mb_id = p.get('monsterBaseId', '')
    try:
        with open(f"{pairs_dir}/{tid}.json", 'r', encoding='utf-8-sig') as df:
            detail = json.load(df)
            t_base_id = detail.get('trainerBaseId', '')
    except Exception:
        t_base_id = ''

    tr = get_trainer_name(tid, t_base_id)
    if tr:
        matched_trainers += 1
    else:
        unmatched_trainers.append((tid, p.get('trainerName'), t_base_id))

    pk = get_pokemon_name(mb_id)
    if pk:
        matched_pokemon += 1
    else:
        unmatched_pokemon.append((mb_id, p.get('monsterName')))

print(f"Total pairs: {len(manifest)}")
print(f"Matched trainers: {matched_trainers} / {len(manifest)}")
if unmatched_trainers:
    print("Unmatched trainers:", unmatched_trainers[:10])

print(f"Matched pokemon: {matched_pokemon} / {len(manifest)}")
if unmatched_pokemon:
    print("Unmatched pokemon:", unmatched_pokemon[:10])
