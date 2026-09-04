import urllib.request
import json
import re
import os
import glob
from pathlib import Path

BASE_DATA_URL = "https://pokemon.brybry.ch/masters/data"
PAIRS_DIR = Path(r"C:\Users\Gabri\Documents\blueslab\src\BluesLab\wwwroot\data\pairs")

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

print("1. Fetching proto and lsd tables from brybry...")
mv_entries = fetch_json(f"{BASE_DATA_URL}/proto/MonsterVariation.json")["entries"]
t_entries = fetch_json(f"{BASE_DATA_URL}/proto/Trainer.json")["entries"]
psc_entries = fetch_json(f"{BASE_DATA_URL}/proto/PassiveSkillChild.json")["entries"]

p_name_en = fetch_json(f"{BASE_DATA_URL}/lsd/passive_skill_name_en.json")
p_name_parts_en = fetch_json(f"{BASE_DATA_URL}/lsd/passive_skill_name_parts_en.json")
p_desc_en = fetch_json(f"{BASE_DATA_URL}/lsd/passive_skill_description_en.json")
p_desc_parts_en = fetch_json(f"{BASE_DATA_URL}/lsd/passive_skill_description_parts_en.json")

ps_children = {str(psc.get("passiveSkillId", "")): psc for psc in psc_entries}

def get_passive_name(passive_id):
    name = p_name_en.get(str(passive_id), f"Passive #{passive_id}")
    parts_re = re.compile(r'\[Name:PassiveSkillNameParts Idx="(\w+)" \]', re.I)
    m = parts_re.search(name)
    while m:
        idx = m.group(1)
        repl = p_name_parts_en.get(idx, "")
        digit = str(safe_int(passive_id) - safe_int(idx))
        name = name.replace(m.group(0), repl).replace('[Name:PassiveSkillNameDigit ]', digit)
        m = parts_re.search(name)
    return name

def get_passive_desc(passive_id):
    desc = p_desc_en.get(str(passive_id), "")
    parts_re = re.compile(r'\[Name:PassiveSkillDescriptionPartsIdTag Idx="(\w+)" \]', re.I)
    m = parts_re.search(desc)
    while m:
        idx = m.group(1)
        repl = p_desc_parts_en.get(idx, "")
        desc = desc.replace(m.group(0), repl)
        m = parts_re.search(desc)
    return desc

def build_passive_item(pid, slot):
    p_name = get_passive_name(pid)
    p_desc = get_passive_desc(pid)
    child_passives = []
    psc = ps_children.get(str(pid))
    if psc:
        for cid in psc.get("passiveSkillChildIds", []):
            cid_int = safe_int(cid)
            if cid_int > 0:
                child_passives.append({
                    "id": cid_int,
                    "name": get_passive_name(cid_int),
                    "description": get_passive_desc(cid_int)
                })
    return {
        "id": pid,
        "name": p_name,
        "description": p_desc,
        "slot": slot,
        "childPassives": child_passives
    }

trainers_by_id = {str(t.get("trainerId")): t for t in t_entries}
mv_by_mid = {}
for mv in mv_entries:
    mid = str(mv.get("monsterId"))
    mv_by_mid.setdefault(mid, []).append(mv)

print("2. Processing all pair JSON files in BluesLab...")
pair_files = glob.glob(str(PAIRS_DIR / "*.json"))
print(f"   Found {len(pair_files)} pair files.")

updated_pairs = 0
updated_variations_total = 0

for pf in pair_files:
    tid = Path(pf).stem
    with open(pf, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    t = trainers_by_id.get(tid)
    file_changed = False
    
    # 1. Update base passives to have slot
    if t:
        base_passives = []
        for slot in range(1, 6):
            pid = safe_int(t.get(f"passive{slot}Id", 0))
            if pid > 0:
                base_passives.append(build_passive_item(pid, slot))
        if base_passives:
            data["passives"] = base_passives
            file_changed = True
    else:
        for idx, p in enumerate(data.get("passives", [])):
            if "slot" not in p:
                p["slot"] = idx + 1
                file_changed = True

    # 2. Update variations passives
    vars_list = data.get("variations", [])
    if vars_list and t:
        mid = str(t.get("monsterId"))
        proto_vars = mv_by_mid.get(mid, [])
        
        for v_idx, v in enumerate(vars_list):
            form_num = v.get("formId", 0)
            matching_pv = None
            for pv in proto_vars:
                if pv.get("form") == form_num or pv.get("formId") == form_num:
                    matching_pv = pv
                    break
            if not matching_pv and v_idx < len(proto_vars):
                matching_pv = proto_vars[v_idx]
            
            if matching_pv:
                resolved_var_passives = []
                has_diff = False
                for slot in range(1, 6):
                    var_pid = safe_int(matching_pv.get(f"passive{slot}Id", 0))
                    base_pid = safe_int(t.get(f"passive{slot}Id", 0))
                    effective_pid = var_pid if var_pid > 0 else base_pid
                    if effective_pid > 0:
                        resolved_var_passives.append(build_passive_item(effective_pid, slot))
                    if var_pid > 0 and var_pid != base_pid:
                        has_diff = True
                
                v["passives"] = resolved_var_passives
                file_changed = True
                updated_variations_total += 1
                if has_diff:
                    updated_pairs += 1

    if file_changed:
        with open(pf, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done! Updated variations across {updated_variations_total} variation objects in pairs.")
print(f"Total pairs with distinct substituted passives in forms: {updated_pairs}.")
