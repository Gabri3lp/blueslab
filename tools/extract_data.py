import os
import sys
import json
import urllib.request
import concurrent.futures
from pathlib import Path

BASE_DATA_URL = "https://pokemon.brybry.ch/masters/data"
OUTPUT_DIR = Path(__file__).parent.parent / "src" / "BluesLab" / "wwwroot"
DATA_DIR = OUTPUT_DIR / "data"
PAIRS_DIR = DATA_DIR / "pairs"
IMG_TRAINERS_DIR = OUTPUT_DIR / "img" / "trainers"

TYPE_MAP = {
    1: "Normal", 2: "Fire", 3: "Water", 4: "Electric", 5: "Grass",
    6: "Ice", 7: "Fighting", 8: "Poison", 9: "Ground", 10: "Flying",
    11: "Psychic", 12: "Bug", 13: "Rock", 14: "Ghost", 15: "Dragon",
    16: "Dark", 17: "Steel", 18: "Fairy", 99: "Stellar"
}

ROLE_MAP = {
    0: "Strike (Physical)",
    1: "Strike (Special)",
    2: "Support",
    3: "Tech",
    4: "Sprint",
    5: "Field",
    6: "Multi"
}

EX_ROLE_MAP = {
    0: "Strike (Physical)",
    1: "Strike (Special)",
    2: "Support",
    3: "Tech",
    4: "Sprint",
    5: "Field",
    6: "Multi"
}

ABILITY_TYPE_MAP = {
    1: "stat",
    2: "passive",
    3: "move effect",
    4: "move boost",
    5: "sync",
    6: "learn move"
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def download_file(url, out_path):
    if out_path.exists():
        return
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            with open(out_path, 'wb') as f:
                f.write(content)
    except Exception as e:
        pass

def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

def main():
    print("=== Blues Lab: PMEX Data Extraction Pipeline ===")
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_TRAINERS_DIR.mkdir(parents=True, exist_ok=True)

    print("1. Fetching Proto tables...")
    proto_names = [
        "Trainer", "TrainerBase", "Monster", "MonsterBase", "MonsterVariation",
        "Ability", "AbilityPanel", "AbilityReleaseCondition", "ExRoleStatusUp",
        "SpecialAwakingEffect", "Move", "PassiveSkillChild", "Schedule", "TrainerSpecialAwaking"
    ]
    protos = {}
    for p in proto_names:
        print(f"   Fetching {p}.json...")
        res = fetch_json(f"{BASE_DATA_URL}/proto/{p}.json")
        protos[p] = res.get("entries", [])

    print("2. Fetching LSD dictionaries...")
    lsd_names = [
        "trainer_verbose_name_en", "trainer_name_en", "monster_name_en",
        "move_name_en", "move_description_en", "move_description_parts_en",
        "passive_skill_name_en", "passive_skill_name_parts_en",
        "passive_skill_description_en", "passive_skill_description_parts_en",
        "ability_name_en"
    ]
    lsd = {}
    for l in lsd_names:
        print(f"   Fetching {l}.json...")
        try:
            lsd[l] = fetch_json(f"{BASE_DATA_URL}/lsd/{l}.json")
        except Exception:
            lsd[l] = {}

    print("3. Loading existing damage engine rules...")
    flutter_data_dir = Path("C:/Users/Gabri/Desktop/blues_lab/assets/data")
    move_scaling = []
    damage_passives = []
    master_passives = []
    lucky_skills = []
    if (flutter_data_dir / "move_scaling.json").exists():
        with open(flutter_data_dir / "move_scaling.json", "r", encoding="utf-8") as f:
            move_scaling = json.load(f)
    if (flutter_data_dir / "damage_passives.json").exists():
        with open(flutter_data_dir / "damage_passives.json", "r", encoding="utf-8") as f:
            damage_passives = json.load(f)
    if (flutter_data_dir / "master_passives.json").exists():
        with open(flutter_data_dir / "master_passives.json", "r", encoding="utf-8") as f:
            master_passives = json.load(f)
    if (flutter_data_dir / "lucky_skills.json").exists():
        with open(flutter_data_dir / "lucky_skills.json", "r", encoding="utf-8") as f:
            lucky_skills = json.load(f)

    damage_rules = {
        "moveScaling": move_scaling,
        "damagePassives": damage_passives,
        "masterPassives": master_passives,
        "luckySkills": lucky_skills
    }
    with open(DATA_DIR / "damage_rules.json", "w", encoding="utf-8") as f:
        json.dump(damage_rules, f, indent=2, ensure_ascii=False)
    print("   Saved damage_rules.json")

    t_bases = {str(tb.get("id", "")): tb for tb in protos["TrainerBase"]}
    m_bases = {str(mb.get("monsterBaseId", "")): mb for mb in protos["MonsterBase"]}
    monsters = {str(m.get("monsterId", "")): m for m in protos["Monster"]}
    abilities = {str(a.get("abilityId", "")): a for a in protos["Ability"]}
    moves_dict = {str(mv.get("moveId", "")): mv for mv in protos["Move"]}
    rel_conditions = {str(rc.get("conditionId", "")): rc for rc in protos["AbilityReleaseCondition"]}
    ps_children = {str(psc.get("passiveSkillId", "")): psc for psc in protos["PassiveSkillChild"]}

    panels_by_trainer = {}
    for ap in protos["AbilityPanel"]:
        tid = str(ap.get("trainerId", ""))
        panels_by_trainer.setdefault(tid, []).append(ap)

    vars_by_monster = {}
    for mv in protos["MonsterVariation"]:
        mid = str(mv.get("monsterId", ""))
        vars_by_monster.setdefault(mid, []).append(mv)

    def get_move_name(move_id):
        return lsd["move_name_en"].get(str(move_id), f"Move #{move_id}")

    def get_move_desc(move_id):
        desc = lsd["move_description_en"].get(str(move_id), "")
        import re
        parts_re = re.compile(r'\[Name:MoveDescriptionPartsIdTag Idx="(\w+)" ]', re.I)
        m = parts_re.search(desc)
        while m:
            idx = m.group(1)
            repl = lsd["move_description_parts_en"].get(idx, "")
            desc = desc.replace(m.group(0), repl)
            m = parts_re.search(desc)
        return desc

    def get_passive_name(passive_id):
        name = lsd["passive_skill_name_en"].get(str(passive_id), f"Passive #{passive_id}")
        import re
        parts_re = re.compile(r'\[Name:PassiveSkillNameParts Idx="(\w+)" \]', re.I)
        m = parts_re.search(name)
        while m:
            idx = m.group(1)
            repl = lsd["passive_skill_name_parts_en"].get(idx, "")
            digit = str(safe_int(passive_id) - safe_int(idx))
            name = name.replace(m.group(0), repl).replace('[Name:PassiveSkillNameDigit ]', digit)
            m = parts_re.search(name)
        return name

    def get_passive_desc(passive_id):
        desc = lsd["passive_skill_description_en"].get(str(passive_id), "")
        import re
        parts_re = re.compile(r'\[Name:PassiveSkillDescriptionPartsIdTag Idx="(\w+)" \]', re.I)
        m = parts_re.search(desc)
        while m:
            idx = m.group(1)
            repl = lsd["passive_skill_description_parts_en"].get(idx, "")
            desc = desc.replace(m.group(0), repl)
            m = parts_re.search(desc)
        return desc

    print("4. Processing and building Sync Pairs...")
    manifest = []
    avatar_downloads = []

    trainers = protos["Trainer"]
    valid_trainers = [
        t for t in trainers
        if t.get("scheduleId") not in ["NEVER_CHECK_DICTIONARY", "NEVER"] and t.get("scoutMethod") != 3
    ]
    print(f"   Found {len(valid_trainers)} valid playable Sync Pairs.")

    for t in valid_trainers:
        trainer_id = str(t.get("trainerId", ""))
        trainer_base_id = str(t.get("trainerBaseId", ""))
        monster_id = str(t.get("monsterId", ""))

        tb = t_bases.get(trainer_base_id, {})
        mon = monsters.get(monster_id, {})
        monster_base_id = str(mon.get("monsterBaseId", ""))
        mb = m_bases.get(monster_base_id, {})

        t_actor = tb.get("actorId", "")
        t_uid = "8000_00" if t_actor == "hero" else (t_actor[2:9] if len(t_actor) >= 9 else t_actor)
        dex = str(mb.get("dexNumber", 0)).zfill(4)
        v = str(mb.get("actorVariant", 0)).zfill(2)
        shiny = "s" if mb.get("isShiny") else ""
        m_uid = f"{dex}_{v}{shiny}"
        uid = f"{t_uid}-{m_uid}"

        avatar_downloads.append((
            f"{BASE_DATA_URL}/icons/trainers/{uid}.png",
            IMG_TRAINERS_DIR / f"{uid}.png"
        ))

        import re
        t_verbose = lsd["trainer_verbose_name_en"].get(trainer_id, "").strip()
        if t_verbose:
            t_name = re.sub(r'\s+', ' ', t_verbose).strip()
        else:
            alt_tid = tb.get("altTrainerNameId", "")
            tname_id = tb.get("trainerNameId", "")
            if alt_tid and alt_tid in lsd["trainer_name_en"]:
                t_name = lsd["trainer_name_en"][alt_tid]
            elif tname_id and tname_id in lsd["trainer_name_en"]:
                t_name = lsd["trainer_name_en"][tname_id]
            elif t_actor.startswith("ch"):
                ch_key = t_actor.split("_")[0]
                t_name = lsd["trainer_name_en"].get(ch_key, f"Trainer #{trainer_base_id}")
            elif t_actor == "hero" or trainer_base_id.startswith("107") or trainer_base_id.startswith("108") or tname_id == "ch8000":
                t_name = "Main Character"
            else:
                t_name = lsd["trainer_name_en"].get(trainer_base_id, f"Trainer #{trainer_base_id}")

        mname_id = str(mb.get("monsterNameId", ""))
        if mname_id and mname_id in lsd["monster_name_en"]:
            m_name = lsd["monster_name_en"][mname_id]
        elif monster_base_id in lsd["monster_name_en"]:
            m_name = lsd["monster_name_en"][monster_base_id]
        else:
            m_name = f"Monster #{monster_base_id}"

        display_name = f"{t_name} & {m_name}"

        type_name = TYPE_MAP.get(t.get("type", 0), "Normal")
        weakness_name = TYPE_MAP.get(t.get("weakness", 0), "")
        role_id = t.get("role", 0)
        role_name = ROLE_MAP.get(role_id, "Strike (Physical)")
        rarity = t.get("rarity", 5)
        has_ex = t.get("exScheduleId") != "" and t.get("exScheduleId") != "NEVER"
        ex_role = ""
        for er in protos.get("TrainerExRole", []):
            if str(er.get("trainerId")) == trainer_id:
                er_id = er.get("role", -1)
                ex_role = EX_ROLE_MAP.get(er_id, "")
                break""

        has_sa = any(str(sa.get("trainerId")) == trainer_id for sa in protos["TrainerSpecialAwaking"])
        vars_list = vars_by_monster.get(monster_id, [])
        has_mega = any(v.get("form") == 1 for v in vars_list)
        has_tera = any(v.get("form") == 7 or v.get("terastalMoveId", 0) > 0 for v in vars_list)

        stats_obj = {
            "hp": mon.get("hpValues", [0]*7),
            "atk": mon.get("atkValues", [0]*7),
            "def": mon.get("defValues", [0]*7),
            "spa": mon.get("spaValues", [0]*7),
            "spd": mon.get("spdValues", [0]*7),
            "spe": mon.get("speValues", [0]*7),
        }

        moves = []
        for i in range(1, 5):
            mid = safe_int(t.get(f"move{i}Id", 0))
            if mid > 0:
                mv = moves_dict.get(str(mid), {})
                is_trainer = (mv.get("user") == "Trainer") or (mv.get("type") == 0) or (10000 <= mid < 20000)
                move_type = "Trainer" if is_trainer else TYPE_MAP.get(mv.get("type", t.get("type", 1)), type_name)
                uses = safe_int(mv.get("uses", 0))
                moves.append({
                    "id": mid,
                    "slot": i,
                    "name": get_move_name(mid),
                    "type": move_type,
                    "category": "Physical" if mv.get("category") == 1 else ("Special" if mv.get("category") == 2 else "Status"),
                    "power": str(mv.get("power", 0)),
                    "accuracy": "-" if is_trainer else str(mv.get("accuracy", 100)),
                    "gauge": "-" if is_trainer else str(mv.get("gaugeDrain", mv.get("gauge", 0))),
                    "target": "An opponent" if mv.get("target") == 1 else ("All opponents" if mv.get("target") == 2 else "Self"),
                    "description": get_move_desc(mid),
                    "isSync": False,
                    "maxUses": uses,
                    "isTrainer": is_trainer
                })

        sync_mid = safe_int(mon.get("syncMoveId", 0))
        if sync_mid > 0:
            smv = moves_dict.get(str(sync_mid), {})
            sync_move_name = get_move_name(sync_mid)
            moves.append({
                "id": sync_mid,
                "slot": 5,
                "name": sync_move_name,
                "type": type_name,
                "category": "Physical" if smv.get("category") == 1 else ("Special" if smv.get("category") == 2 else "Status"),
                "power": str(smv.get("power", 250)),
                "accuracy": "-",
                "gauge": "-",
                "target": "An opponent",
                "description": get_move_desc(sync_mid),
                "isSync": True
            })
        else:
            sync_move_name = f"{display_name} Sync"

        passives = []
        for i in range(1, 6):
            pid = safe_int(t.get(f"passive{i}Id", 0))
            if pid > 0:
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
                passives.append({
                    "id": pid,
                    "name": p_name,
                    "description": p_desc,
                    "childPassives": child_passives
                })

        variations = []
        for v_entry in vars_list:
            form_num = v_entry.get("form", 0)
            form_name = "Mega" if form_num == 1 else ("Tera" if form_num == 7 else f"Form {form_num}")
            stat_mult = {
                "atk": v_entry.get("atkScale", 100) / 100.0,
                "def": v_entry.get("defScale", 100) / 100.0,
                "spa": v_entry.get("spaScale", 100) / 100.0,
                "spd": v_entry.get("spdScale", 100) / 100.0,
                "spe": v_entry.get("speScale", 100) / 100.0,
            }
            var_passives = []
            for i in range(1, 6):
                pid = safe_int(v_entry.get(f"passive{i}Id", 0))
                if pid > 0:
                    var_passives.append({
                        "id": pid,
                        "name": get_passive_name(pid),
                        "description": get_passive_desc(pid)
                    })
            variations.append({
                "formId": form_num,
                "formName": form_name,
                "actorId": v_entry.get("actorId", ""),
                "statMultiplier": stat_mult,
                "passives": var_passives,
                "terastalMoveId": v_entry.get("terastalMoveId", 0)
            })

        raw_panels = panels_by_trainer.get(trainer_id, [])
        dedup_panels = {}
        for ap in raw_panels:
            cid = ap.get("cellId")
            if cid not in dedup_panels or dedup_panels[cid].get("version", 0) < ap.get("version", 0):
                dedup_panels[cid] = ap

        grid_cells = []
        for cid, ap in dedup_panels.items():
            ab_id = str(ap.get("abilityId", ""))
            ab = abilities.get(ab_id, {})
            ab_type_num = ab.get("type", 1)
            color_kind = ABILITY_TYPE_MAP.get(ab_type_num, "passive")

            req_level = 1
            for cond_id in ap.get("conditionIds", []):
                rc = rel_conditions.get(str(cond_id), {})
                if rc.get("type") in [6, 7]:
                    req_level = max(req_level, rc.get("parameter", 1))

            title = lsd["ability_name_en"].get(ab_id, "")
            desc = ""
            stat_bonus = {}
            power_bonus = {}

            if ab_type_num == 1:
                val = ab.get("value", 0)
                desc = f"Increases stat by {val}."
                t_low = title.lower()
                if "hp" in t_low: stat_bonus["hp"] = val
                elif "sp.atk" in t_low or "sp. attack" in t_low: stat_bonus["spa"] = val
                elif "attack" in t_low: stat_bonus["atk"] = val
                elif "defense" in t_low: stat_bonus["def"] = val
                elif "sp.def" in t_low or "sp. defense" in t_low: stat_bonus["spd"] = val
                elif "speed" in t_low: stat_bonus["spe"] = val
            elif ab_type_num == 2:
                pid = safe_int(ab.get("passiveId", 0))
                title = get_passive_name(pid)
                desc = get_passive_desc(pid)
            elif ab_type_num == 4:
                mid = safe_int(ab.get("moveId", 0))
                mname = get_move_name(mid) if mid else "Move"
                val = ab.get("value", 0)
                if not title:
                    title = f"{mname}: Power +{val}"
                if ": power" in title.lower():
                    power_bonus[mname] = val
                desc = f"Raises the power of {mname}."
            elif ab_type_num == 5:
                val = ab.get("value", 25)
                title = f"{sync_move_name}: Power +{val}"
                power_bonus[sync_move_name] = val
                desc = f"Raises the power of {sync_move_name}."

            grid_cells.append({
                "cellId": cid,
                "q": ap.get("x", 0),
                "r": ap.get("y", 0),
                "s": ap.get("z", 0),
                "energyCost": ap.get("energyCost", 0),
                "orbCost": ap.get("orbCost", 0),
                "moveLevel": req_level,
                "colorKind": color_kind,
                "title": title,
                "description": desc,
                "statBonus": stat_bonus,
                "powerBonus": power_bonus
            })

        pair_doc = {
            "trainerId": trainer_id,
            "trainerBaseId": trainer_base_id,
            "monsterId": monster_id,
            "monsterBaseId": monster_base_id,
            "displayName": display_name,
            "trainerName": t_name,
            "monsterName": m_name,
            "type": type_name,
            "weakness": weakness_name,
            "role": role_name,
            "exRole": ex_role,
            "rarity": rarity,
            "hasEx": has_ex,
            "hasMega": has_mega,
            "hasTera": has_tera,
            "hasSuperAwakening": has_sa,
            "syncMoveName": sync_move_name,
            "iconUrl": f"img/trainers/{uid}.png",
            "stats": stats_obj,
            "moves": moves,
            "passives": passives,
            "variations": variations,
            "grid": grid_cells
        }

        with open(PAIRS_DIR / f"{trainer_id}.json", "w", encoding="utf-8") as f:
            json.dump(pair_doc, f, indent=2, ensure_ascii=False)

        manifest.append({
            "trainerId": trainer_id,
            "monsterId": monster_id,
            "monsterBaseId": monster_base_id,
            "displayName": display_name,
            "trainerName": t_name,
            "monsterName": m_name,
            "type": type_name,
            "role": role_name,
            "exRole": ex_role,
            "rarity": rarity,
            "hasEx": has_ex,
            "hasMega": has_mega,
            "hasTera": has_tera,
            "hasSuperAwakening": has_sa,
            "iconUrl": f"img/trainers/{uid}.png",
            "gridTileCount": len(grid_cells)
        })

    manifest.sort(key=lambda x: x["displayName"])

    with open(DATA_DIR / "pairs_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"   Saved pairs_manifest.json ({len(manifest)} pairs)")

    print(f"5. Downloading {len(avatar_downloads)} trainer avatars in parallel...")
    def dl_task(item):
        url, path = item
        download_file(url, path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(dl_task, avatar_downloads))

    print("=== Extraction completed successfully! ===")

if __name__ == "__main__":
    main()
