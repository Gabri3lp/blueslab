import glob
import json
import os
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "BluesLab", "wwwroot")
PAIRS_DIR = os.path.join(ROOT, "data", "pairs")
MANIFEST_PATH = os.path.join(ROOT, "data", "pairs_manifest.json")
EN_PATH = os.path.join(ROOT, "locales", "en.json")
ES_PATH = os.path.join(ROOT, "locales", "es.json")

headers = {"User-Agent": "Mozilla/5.0"}

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("Fetching TrainerSpecialAwaking.json and PassiveSkillChild.json from brybry.ch...")
sa_entries = fetch_json("https://pokemon.brybry.ch/masters/data/proto/TrainerSpecialAwaking.json").get("entries", [])
child_entries = fetch_json("https://pokemon.brybry.ch/masters/data/proto/PassiveSkillChild.json").get("entries", [])

sa_by_tid = {}
for e in sa_entries:
    if e.get("scheduleId") != "NEVER":
        sa_by_tid[str(e["trainerId"])] = int(e["passiveSkillId"])

children_by_pid = {str(c["passiveSkillId"]): [int(cid) for cid in c.get("passiveSkillChildIds", [])] for c in child_entries}

with open(EN_PATH, "r", encoding="utf-8") as f:
    en = json.load(f)
with open(ES_PATH, "r", encoding="utf-8") as f:
    es = json.load(f)

# Ensure v2.73 SA passives and child passives are in en.json and es.json
en["passive_name_32023001"] = "Freeze the World"
en["passive_desc_32023001"] = "Reduces the user’s sync move countdown by one the first time it enters a battle each battle. Turns the field of play’s zone into an Ice Zone the first time the user’s sync move is used each battle. (An Ice Zone powers up Ice-type attacks.) Extends the duration of the Ice Zone when the zone turns into an Ice Zone while the user is on the field."
es["passive_name_32023001"] = "La Orden de Helar al Mundo"
es["passive_desc_32023001"] = "Reduce en 1 el contador de movimientos compi del usuario la primera vez que entra en combate en cada combate. Convierte la zona en una Zona Hielo la primera vez que el usuario usa su movimiento compi en cada combate. (Una Zona Hielo potencia los ataques de tipo Hielo.) Aumenta la duración de la Zona Hielo cuando la zona se convierte en una Zona Hielo mientras el usuario está en el campo."

en["passive_name_32023101"] = "Eternal Beauty of Kalos"
en["passive_desc_32023101"] = "Applies Kalos Circle (Special) to the allied field of play the first time the user enters a battle each battle. Applies Kalos Circle (Special) to the allied field of play the first time the user’s sync move is used each battle. Extends the duration of Kalos Circle (Special) when Kalos Circle (Special) is applied to the allied field of play."
es["passive_name_32023101"] = "Kalos, Hermosa para Siempre"
es["passive_desc_32023101"] = "Aplica Círculo de Kalos (Especial) al bando aliado la primera vez que el usuario entra en combate en cada combate. Aplica Círculo de Kalos (Especial) al bando aliado la primera vez que el usuario usa su movimiento compi en cada combate. Aumenta la duración del Círculo de Kalos (Especial) cuando se aplica Círculo de Kalos (Especial) al bando aliado."

en["passive_name_19072301"] = "Debut: Kalos C (Spec) on Field"
en["passive_desc_19072301"] = "Applies Kalos Circle (Special) to the allied field of play the first time the user enters a battle each battle."
es["passive_name_19072301"] = "1.ª Entrada Círculo de Kalos (Especial)"
es["passive_desc_19072301"] = "Aplica Círculo de Kalos (Especial) al bando aliado la primera vez que el usuario entra en combate en cada combate."

def build_sa_detail_obj(pid: int):
    name = en.get(f"passive_name_{pid}", f"Passive #{pid}")
    desc = en.get(f"passive_desc_{pid}", "")
    child_ids = children_by_pid.get(str(pid), [])
    child_objs = []
    for cid in child_ids:
        child_objs.append({
            "id": cid,
            "name": en.get(f"passive_name_{cid}", f"Passive #{cid}"),
            "description": en.get(f"passive_desc_{cid}", "")
        })
    return {
        "id": pid,
        "name": name,
        "description": desc,
        "slot": 0,
        "childPassives": child_objs
    }

def build_sa_manifest_obj(pid: int):
    return {
        "id": pid,
        "name": en.get(f"passive_name_{pid}", f"Passive #{pid}"),
        "description": en.get(f"passive_desc_{pid}", "")
    }

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

updated_sa_count = 0
cleared_bogus_count = 0

for m in manifest:
    tid = str(m.get("trainerId", ""))
    if tid in sa_by_tid:
        pid = sa_by_tid[tid]
        m["hasSuperAwakening"] = True
        m["superAwakeningPassive"] = build_sa_manifest_obj(pid)
        updated_sa_count += 1
    else:
        if m.get("hasSuperAwakening") or "superAwakeningPassive" in m:
            cleared_bogus_count += 1
        m["hasSuperAwakening"] = False
        if "superAwakeningPassive" in m:
            del m["superAwakeningPassive"]

for fpath in glob.glob(os.path.join(PAIRS_DIR, "*.json")):
    with open(fpath, "r", encoding="utf-8") as f:
        detail = json.load(f)
    tid = str(detail.get("trainerId", ""))
    changed = False
    if tid in sa_by_tid:
        pid = sa_by_tid[tid]
        sa_detail = build_sa_detail_obj(pid)
        if not detail.get("hasSuperAwakening") or detail.get("superAwakeningPassive") != sa_detail:
            detail["hasSuperAwakening"] = True
            detail["superAwakeningPassive"] = sa_detail
            changed = True
    else:
        if detail.get("hasSuperAwakening") or detail.get("superAwakeningPassive") is not None:
            detail["hasSuperAwakening"] = False
            detail["superAwakeningPassive"] = None
            changed = True
    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(detail, f, indent=2, ensure_ascii=False)

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

with open(EN_PATH, "w", encoding="utf-8") as f:
    json.dump(en, f, indent=2, ensure_ascii=False)

with open(ES_PATH, "w", encoding="utf-8") as f:
    json.dump(es, f, indent=2, ensure_ascii=False)

print(f"Successfully updated {updated_sa_count} official SA pairs and cleared {cleared_bogus_count} bogus SA entries!")
