import json, os, re, datetime

SCRATCH = r"C:\Users\Gabri\.gemini\antigravity\brain\de05f81c-1390-494e-9dda-d5d7c96d6fe5\scratch\2.73"
ROOT = r"C:\Users\Gabri\Documents\blueslab\src\BluesLab\wwwroot"

with open(os.path.join(SCRATCH, "Trainer.txt"), "r", encoding="utf-8") as f:
    trainer_txt = f.read()

with open(os.path.join(SCRATCH, "Grid.txt"), "r", encoding="utf-8") as f:
    grid_txt = f.read()

with open(os.path.join(ROOT, "locales", "en.json"), "r", encoding="utf-8") as f:
    en_locale = json.load(f)

with open(os.path.join(ROOT, "locales", "es.json"), "r", encoding="utf-8") as f:
    es_locale = json.load(f)

# Clean up any accidental nested dicts from previous run if present
for k in ["moves", "move_descriptions", "passives", "passive_descriptions", "grid_skills", "trainers", "pokemon"]:
    en_locale.pop(k, None)
    es_locale.pop(k, None)

with open(os.path.join(ROOT, "data", "pairs_manifest.json"), "r", encoding="utf-8") as f:
    manifest = json.load(f)

with open(os.path.join(ROOT, "data", "themes_database.json"), "r", encoding="utf-8") as f:
    themes_db = json.load(f)

theme_name_to_id = {d["name"].lower(): d["id"] for d in themes_db.get("definitions", [])}

# Build lookup tables for existing moves, passives, and grid tiles
move_name_to_id = {}
passive_name_to_id = {}
tile_title_to_ability_id = {}
max_custom_move_id = 927300
max_custom_passive_id = 92730000
max_custom_ability_id = 9273000000

NEW_273_FILES = {
    "10196110000.json", "10195100000.json", "10192400000.json",
    "10193400000.json", "10221000000.json", "10224000000.json",
    "10223000000.json", "10012000002.json", "10002410001.json"
}

pairs_dir = os.path.join(ROOT, "data", "pairs")
for fn in os.listdir(pairs_dir):
    if not fn.endswith(".json") or fn in NEW_273_FILES:
        continue
    with open(os.path.join(pairs_dir, fn), "r", encoding="utf-8") as f:
        pdata = json.load(f)
    for m in pdata.get("moves", []):
        name_clean = m.get("name", "").replace("\n", " ").strip()
        if name_clean and m.get("id") and name_clean not in move_name_to_id:
            move_name_to_id[name_clean] = (m["id"], m.get("description", ""))
    for p in pdata.get("passives", []):
        name_clean = p.get("name", "").replace("\n", " ").strip()
        if name_clean and p.get("id") and name_clean not in passive_name_to_id:
            passive_name_to_id[name_clean] = (p["id"], p.get("description", ""))
    for c in pdata.get("grid", []):
        t_clean = c.get("title", "").replace("\n", " ").strip()
        if t_clean and c.get("abilityId") and t_clean not in tile_title_to_ability_id:
            tile_title_to_ability_id[t_clean] = str(c["abilityId"])

def get_or_create_move_id(name, desc, is_trainer=False, is_sync=False):
    global max_custom_move_id
    name_clean = name.replace("\n", " ").strip()
    if not is_sync and name_clean in move_name_to_id:
        mid, ex_desc = move_name_to_id[name_clean]
        # Standard Pokemon moves or shared Trainer item moves (Potion, X Evasion, X Attack, Hoenn Solidarity/Analysis)
        if (
            not is_trainer
            and (ex_desc.replace("\n", " ").strip() == desc.replace("\n", " ").strip() or mid < 1000)
        ) or name_clean in ("Potion", "X Attack", "X Evasion", "Hoenn Solidarity", "Hoenn Analysis"):
            return mid
    max_custom_move_id += 1
    mid = max_custom_move_id
    en_locale[f"move_name_{mid}"] = name_clean
    es_locale[f"move_name_{mid}"] = name_clean
    en_locale[f"move_desc_{mid}"] = desc
    es_locale[f"move_desc_{mid}"] = desc
    move_name_to_id[name_clean] = (mid, desc)
    return mid

def get_or_create_passive_id(name, desc):
    global max_custom_passive_id
    name_clean = name.replace("\n", " ").strip()
    if name_clean in passive_name_to_id:
        pid, _ = passive_name_to_id[name_clean]
        return pid
    max_custom_passive_id += 1
    pid = max_custom_passive_id
    en_locale[f"passive_name_{pid}"] = name_clean
    es_locale[f"passive_name_{pid}"] = name_clean
    en_locale[f"passive_desc_{pid}"] = desc
    es_locale[f"passive_desc_{pid}"] = desc
    passive_name_to_id[name_clean] = (pid, desc)
    return pid

def get_or_create_ability_id(title, desc):
    global max_custom_ability_id
    t_clean = title.replace("\n", " ").strip()
    if t_clean in tile_title_to_ability_id:
        return tile_title_to_ability_id[t_clean]
    max_custom_ability_id += 1
    aid = str(max_custom_ability_id)
    en_locale[f"tile_name_{aid}"] = t_clean
    es_locale[f"tile_name_{aid}"] = t_clean
    en_locale[f"tile_desc_{aid}"] = desc
    es_locale[f"tile_desc_{aid}"] = desc
    tile_title_to_ability_id[t_clean] = aid
    return aid

PAIR_META = {
    "Sygna Suit Lysandre (Alt.) & Chi-Yu": {
        "trainerId": "10196110000",
        "trainerBaseId": "10019611",
        "trainerKey": "10196110000",
        "monsterId": "20196110000",
        "monsterBaseId": "2010040000",
        "pokemonKey": "2010040000",
        "trainerActorId": "ch0196_11_fleurdelis",
        "pokemonActorId": "pm1004_00_00_yiyui",
        "iconUrl": "img/trainers/0196_11-1004_00.png",
        "pokemonIconUrl": "img/pokemon/100400_128.png",
        "trainerNameEn": "Sygna Suit Lysandre (Alt.)",
        "trainerNameEs": "Lysson (Traje S) (Alt.)",
        "pokemonNameEn": "Chi-Yu",
        "pokemonNameEs": "Chi-Yu",
        "displayName": "Sygna Suit Lysandre (Alt.) & Chi-Yu",
        "releaseDate": "2026-10-02"
    },
    "Sygna Suit Ghetsis & Chien-Pao": {
        "trainerId": "10195100000",
        "trainerBaseId": "10019510",
        "trainerKey": "10195100000",
        "monsterId": "20195100000",
        "monsterBaseId": "2010020000",
        "pokemonKey": "2010020000",
        "trainerActorId": "ch0195_10_ghetsis",
        "pokemonActorId": "pm1002_00_00_paojian",
        "iconUrl": "img/trainers/0195_10-1002_00.png",
        "pokemonIconUrl": "img/pokemon/100200_128.png",
        "trainerNameEn": "Sygna Suit Ghetsis",
        "trainerNameEs": "Ghechis (Traje S)",
        "pokemonNameEn": "Chien-Pao",
        "pokemonNameEs": "Chien-Pao",
        "displayName": "Sygna Suit Ghetsis & Chien-Pao",
        "releaseDate": "2026-09-30"
    },
    "Maxie (Fall 2026) & Ting-Lu": {
        "trainerId": "10192400000",
        "trainerBaseId": "10019240",
        "trainerKey": "10192400000",
        "monsterId": "20192400000",
        "monsterBaseId": "2010030000",
        "pokemonKey": "2010030000",
        "trainerActorId": "ch0192_40_matsubusa",
        "pokemonActorId": "pm1003_00_00_dinglu",
        "iconUrl": "img/trainers/0192_40-1003_00.png",
        "pokemonIconUrl": "img/pokemon/100300_128.png",
        "trainerNameEn": "Maxie (Fall 2026)",
        "trainerNameEs": "Magno (Otoño 2026)",
        "pokemonNameEn": "Ting-Lu",
        "pokemonNameEs": "Ting-Lu",
        "displayName": "Maxie (Fall 2026) & Ting-Lu",
        "releaseDate": "2026-10-16"
    },
    "Archie (Fall 2026) & Wo-Chien": {
        "trainerId": "10193400000",
        "trainerBaseId": "10019340",
        "trainerKey": "10193400000",
        "monsterId": "20193400000",
        "monsterBaseId": "2010010000",
        "pokemonKey": "2010010000",
        "trainerActorId": "ch0193_40_aogiri",
        "pokemonActorId": "pm1001_00_00_chongjian",
        "iconUrl": "img/trainers/0193_40-1001_00.png",
        "pokemonIconUrl": "img/pokemon/100100_128.png",
        "trainerNameEn": "Archie (Fall 2026)",
        "trainerNameEs": "Aquiles (Otoño 2026)",
        "pokemonNameEn": "Wo-Chien",
        "pokemonNameEs": "Wo-Chien",
        "displayName": "Archie (Fall 2026) & Wo-Chien",
        "releaseDate": "2026-10-14"
    },
    "Tabitha & Camerupt": {
        "trainerId": "10221000000",
        "trainerBaseId": "10022100",
        "trainerKey": "ch0221",
        "monsterId": "20221000000",
        "monsterBaseId": "20032300",
        "pokemonKey": "20032300",
        "trainerActorId": "ch0221_00_homura",
        "pokemonActorId": "pm0323_00_bakuuda",
        "iconUrl": "img/trainers/0221_00-0323_00.png",
        "pokemonIconUrl": "img/pokemon/032300_128.png",
        "trainerNameEn": "Tabitha",
        "trainerNameEs": "Tatiano",
        "pokemonNameEn": "Camerupt",
        "pokemonNameEs": "Camerupt",
        "displayName": "Tabitha & Camerupt",
        "releaseDate": "2026-10-21"
    },
    "Shelly & Sharpedo": {
        "trainerId": "10224000000",
        "trainerBaseId": "10022400",
        "trainerKey": "ch0224",
        "monsterId": "20224000000",
        "monsterBaseId": "20031900",
        "pokemonKey": "20031900",
        "trainerActorId": "ch0224_00_izumi",
        "pokemonActorId": "pm0319_00_samehader",
        "iconUrl": "img/trainers/0224_00-0319_00.png",
        "pokemonIconUrl": "img/pokemon/031900_128.png",
        "trainerNameEn": "Shelly",
        "trainerNameEs": "Silvina",
        "pokemonNameEn": "Sharpedo",
        "pokemonNameEs": "Sharpedo",
        "displayName": "Shelly & Sharpedo",
        "releaseDate": "2026-10-21"
    },
    "Matt & Sharpedo": {
        "trainerId": "10223000000",
        "trainerBaseId": "10022300",
        "trainerKey": "ch0223",
        "monsterId": "20223000000",
        "monsterBaseId": "20031900",
        "pokemonKey": "20031900",
        "trainerActorId": "ch0223_00_ushio",
        "pokemonActorId": "pm0319_00_samehader",
        "iconUrl": "img/trainers/0223_00-0319_00.png",
        "pokemonIconUrl": "img/pokemon/031900_128.png",
        "trainerNameEn": "Matt",
        "trainerNameEs": "Matías",
        "pokemonNameEn": "Sharpedo",
        "pokemonNameEs": "Sharpedo",
        "displayName": "Matt & Sharpedo",
        "releaseDate": "2026-10-21"
    },
    "Korrina & Machoke": {
        "trainerId": "10012000002",
        "trainerBaseId": "10001200",
        "trainerKey": "ch0012",
        "monsterId": "20012000002",
        "monsterBaseId": "20006700",
        "pokemonKey": "20006700",
        "trainerActorId": "ch0012_00_corni",
        "pokemonActorId": "pm0067_00_goriky",
        "iconUrl": "img/trainers/0012_00-0067_00.png",
        "pokemonIconUrl": "img/pokemon/006700_128.png",
        "trainerNameEn": "Korrina",
        "trainerNameEs": "Corelia",
        "pokemonNameEn": "Machoke",
        "pokemonNameEs": "Machoke",
        "displayName": "Korrina & Machoke",
        "releaseDate": "2026-10-01"
    },
    "Lyra (Special Costume) & Marill": {
        "trainerId": "10002410001",
        "trainerBaseId": "10000241",
        "trainerKey": "10002410001",
        "monsterId": "20002410001",
        "monsterBaseId": "20018300",
        "pokemonKey": "20018300",
        "trainerActorId": "ch0002_41_kotone",
        "pokemonActorId": "pm0183_00_maril",
        "iconUrl": "img/trainers/0002_41-0183_00.png",
        "pokemonIconUrl": "img/pokemon/018300_128.png",
        "trainerNameEn": "Lyra (Special Costume)",
        "trainerNameEs": "Lira (Traje Especial)",
        "pokemonNameEn": "Marill",
        "pokemonNameEs": "Marill",
        "displayName": "Lyra (Special Costume) & Marill",
        "releaseDate": "2026-09-27"
    }
}

def compute_7_stats(v1, v140, v150, v200):
    step10 = v150 - v140
    v120 = v140 - 2 * step10
    v100 = v140 - 4 * step10
    v30 = round(v1 + (v100 - v1) * 0.1745)
    v45 = round(v1 + (v100 - v1) * 0.3360)
    return [v1, v30, v45, v100, v120, v140, v200]

# Parse Grid.txt
grid_sections = re.split(r'=+(?:END)?=+', grid_txt)
grids_by_pair = {}

STAT_BONUS_KEY = {
    "HP": ("hp", "11000000"),
    "Attack": ("atk", "12000000"),
    "Defense": ("def", "13000000"),
    "Sp. Atk": ("spa", "14000000"),
    "Sp. Def": ("spd", "15000000"),
    "Speed": ("spe", "16000000")
}

for sec in grid_sections:
    sec = sec.strip()
    if not sec or sec.startswith("1. No."):
        continue
    lines = [l.rstrip() for l in sec.splitlines() if l.strip()]
    header = lines[0]
    m_hdr = re.match(r"No\.\s*\d+\s+(.+?)\s*\((?:Genderless|Male♂️|Female♀️)\)", header)
    if not m_hdr:
        continue
    pair_name = m_hdr.group(1).strip()
    cells = re.findall(r'Cell (\d+) \| 🎯 Cord \(([^)]+)\) \| Cost: ⚡ (\d+) Energy \| 🔮 (\d+) Sync Orb\(s\)\n((?:\t.*\n?)+)', sec)
    parsed_cells = []
    for c_num, cord, energy, orbs, body in cells:
        q, r, s = [int(x.strip()) for x in cord.split(",")]
        b_lines = [bl.strip() for bl in body.strip().splitlines() if bl.strip()]
        move_lvl = 1
        for bl in b_lines:
            m_lvl = re.search(r"Move level must be (\d+) or higher", bl)
            if m_lvl:
                move_lvl = int(m_lvl.group(1))
        color_line = next((bl for bl in b_lines if bl.startswith("Color Grid:")), "")
        non_req = [
            bl for bl in b_lines
            if not bl.startswith("Requirements:")
            and not bl.startswith("Color Grid:")
            and not bl.startswith("Grid Expand Unlock:")
            and not bl.startswith("Move:")
        ]
        color_kind = "passive"
        title = non_req[0] if non_req else ""
        desc = "\n".join(non_req[1:]) if len(non_req) > 1 else title
        stat_bonus = {}
        power_bonus = {}
        ability_id = ""

        if "Blue (Stat)" in color_line:
            color_kind = "stat"
            m_st = re.match(r"^(HP|Attack|Defense|Sp\. Atk|Sp\. Def|Speed)\s+(\d+)$", title)
            if m_st:
                st_label, st_val = m_st.group(1), int(m_st.group(2))
                st_key, st_prefix = STAT_BONUS_KEY[st_label]
                title = f"{st_label} +{st_val}"
                desc = f"Raises {st_label} by {st_val}."
                stat_bonus = {st_key: st_val}
                ability_id = f"{st_prefix}{st_val:02d}"
        elif "Green (Move Boost)" in color_line or "Rainbow (Sync Move)" in color_line:
            color_kind = "move boost" if "Green" in color_line else "sync"
            line_arrow = non_req[1] if len(non_req) > 1 else title
            if ": Power ↑ " in line_arrow:
                m_part, v_part = line_arrow.split(": Power ↑ ", 1)
                val = int(v_part.strip())
                m_name = m_part.strip()
                title = f"{m_name}: Power +{val}"
                desc = f"Raises the power of {m_name}."
                power_bonus = {m_name: val}
            elif ": Accuracy ↑ " in line_arrow:
                m_part, v_part = line_arrow.split(": Accuracy ↑ ", 1)
                val = int(v_part.strip())
                m_name = m_part.strip()
                title = f"{m_name}: Accuracy +{val}"
                desc = f"Raises the accuracy of {m_name} by {val}."
            ability_id = get_or_create_ability_id(title, desc)
        elif "Red (Move Effect)" in color_line:
            color_kind = "move effect"
            ability_id = get_or_create_ability_id(title, desc)
        else:
            color_kind = "passive"
            ability_id = get_or_create_ability_id(title, desc)

        parsed_cells.append({
            "cellNum": int(c_num),
            "q": q,
            "r": r,
            "s": s,
            "energyCost": int(energy),
            "orbCost": int(orbs),
            "moveLevel": move_lvl,
            "colorKind": color_kind,
            "title": title,
            "description": desc,
            "statBonus": stat_bonus,
            "powerBonus": power_bonus,
            "abilityId": ability_id
        })
    grids_by_pair[pair_name] = parsed_cells

# Update Bertha & Hippowdon (10154000000.json)
bertha_path = os.path.join(pairs_dir, "10154000000.json")
if os.path.exists(bertha_path) and "Bertha & Hippowdon" in grids_by_pair:
    with open(bertha_path, "r", encoding="utf-8") as f:
        bertha = json.load(f)
    existing_coords = {(c["q"], c["r"], c["s"]) for c in bertha.get("grid", [])}
    added_bertha = 0
    for nc in grids_by_pair["Bertha & Hippowdon"]:
        if (nc["q"], nc["r"], nc["s"]) not in existing_coords:
            cell_obj = {
                "cellId": int(f"1015400{nc['cellNum']-1:03d}"),
                "q": nc["q"],
                "r": nc["r"],
                "s": nc["s"],
                "energyCost": nc["energyCost"],
                "orbCost": nc["orbCost"],
                "moveLevel": nc["moveLevel"],
                "colorKind": nc["colorKind"],
                "title": nc["title"],
                "description": nc["description"],
                "statBonus": nc["statBonus"],
                "powerBonus": nc["powerBonus"],
                "abilityId": nc["abilityId"]
            }
            bertha["grid"].append(cell_obj)
            added_bertha += 1
    with open(bertha_path, "w", encoding="utf-8") as f:
        json.dump(bertha, f, indent=2, ensure_ascii=False)
    for mp in manifest:
        if mp["trainerId"] == "10154000000":
            mp["gridTileCount"] = len(bertha["grid"])
    print(f"Updated Bertha & Hippowdon with {added_bertha} new grid tiles (total {len(bertha['grid'])}).")

def parse_single_move(m_block, slot_num, is_sync=False):
    lines = [l.strip() for l in m_block.strip().splitlines() if l.strip()]
    header = lines[0]
    name = header.split(":", 1)[1].strip() if ":" in header else header
    m_type = "Trainer"
    cat = "Status"
    user = "Pokemon"
    desc = ""
    power = "0"
    acc = "-"
    gauge = "-"
    target = "Self"
    max_uses = 0
    for l in lines[1:]:
        if l.startswith("Type:"):
            m_type = l.split("Type:", 1)[1].strip()
        elif l.startswith("Category:"):
            cat = l.split("Category:", 1)[1].strip()
        elif l.startswith("User:"):
            user = l.split("User:", 1)[1].strip()
        elif l.startswith("Description:"):
            desc = l.split("Description:", 1)[1].strip().replace("\u00a0", " ")
        elif l.startswith("Power:"):
            parts = [p.strip() for p in l.split("|")]
            for p in parts:
                if p.startswith("Power:"):
                    pv = p.split("Power:", 1)[1].strip()
                    m_pv = re.match(r"(\d+)", pv)
                    power = m_pv.group(1) if m_pv else "0"
                elif p.startswith("Accuracy:"):
                    av = p.split("Accuracy:", 1)[1].strip()
                    acc = "-" if av == "--" else av
                elif p.startswith("Gauge:"):
                    gv = p.split("Gauge:", 1)[1].strip()
                    gauge = "0" if (gv == "--" and is_sync) else ("-" if gv == "--" else gv)
                elif p.startswith("Target:"):
                    target = p.split("Target:", 1)[1].strip()
                elif p.startswith("Max uses:"):
                    uv = p.split("Max uses:", 1)[1].strip()
                    max_uses = 0 if uv == "--" else int(uv)
    is_trainer = (user == "Trainer") or (m_type == "Trainer")
    mid = get_or_create_move_id(name, desc, is_trainer=is_trainer, is_sync=is_sync)
    return {
        "id": mid,
        "slot": slot_num,
        "name": name,
        "type": m_type,
        "category": cat,
        "power": power,
        "accuracy": acc,
        "gauge": gauge,
        "target": target,
        "description": desc,
        "isSync": is_sync,
        "maxUses": max_uses,
        "isTrainer": is_trainer
    }

# Split Trainer.txt into blocks
trainer_sections = trainer_txt.split("-------------------------------END-------------------------------")
new_manifest_entries = []

for tsec in trainer_sections:
    tsec = tsec.strip()
    if not tsec:
        continue
    # Remove table of contents if present in first block
    if "=========================================" in tsec:
        tsec = tsec.split("=========================================")[-1].strip()
    lines = [l.strip() for l in tsec.splitlines() if l.strip()]
    if not lines:
        continue
    m_hdr = re.match(r"No\.\s*\d+\s+(.+?)\s*\((?:Genderless|Male♂️|Female♀️)\)", lines[0])
    if not m_hdr:
        continue
    pair_name = m_hdr.group(1).strip()
    if pair_name not in PAIR_META:
        print("UNKNOWN PAIR:", pair_name)
        continue
    meta = PAIR_META[pair_name]

    role_m = re.search(r"Role:\s*([^\n|]+?)(?:\s*\|\s*EX Role 🌈:\s*([^\n]+))?$", tsec, re.M)
    role_str = role_m.group(1).strip() if role_m else "Support"
    ex_role_str = role_m.group(2).strip() if (role_m and role_m.group(2)) else ""

    type_m = re.search(r"Type:\s*(\w+)\s*\|\s*Weakness:\s*(\w+)", tsec)
    pkmn_type = type_m.group(1).strip() if type_m else "Normal"
    weakness = type_m.group(2).strip() if type_m else "Normal"

    rarity_m = re.search(r"Rarity:\s*(⭐+)", tsec)
    rarity = len(rarity_m.group(1)) if rarity_m else 5

    # Parse Team Skills -> Theme IDs
    skill_matches = re.findall(r"^\d+\.\s+(.+?)\s+(?:Field|Strike|Support|Tech|Sprint)$", tsec, re.M)
    theme_ids = []
    for sm in skill_matches:
        tid = theme_name_to_id.get(sm.strip().lower())
        if tid and tid not in theme_ids:
            theme_ids.append(tid)

    # Split main body from Tera/Mega details
    main_part = tsec
    tera_part = ""
    mega_part = ""
    if "📌 Tera Details 📌" in tsec:
        main_part, tera_part = tsec.split("📌 Tera Details 📌", 1)
    elif "📌 Mega Details 📌" in tsec:
        main_part, mega_part = tsec.split("📌 Mega Details 📌", 1)

    # Parse Moves (Move 1..4 and Sync Move)
    moves_list = []
    for m_idx in range(1, 5):
        m_pat = rf"(Move {m_idx}:.*?(?=(?:Move {m_idx+1}:|Sync Move:)))"
        m_match = re.search(m_pat, main_part, re.S)
        if m_match:
            moves_list.append(parse_single_move(m_match.group(1), m_idx, is_sync=False))

    sm_match = re.search(r"(Sync Move:.*?(?=🛡️ Passive Details 🌟))", main_part, re.S)
    sync_move_name = ""
    if sm_match:
        sm_obj = parse_single_move(sm_match.group(1), 5, is_sync=True)
        sync_move_name = sm_obj["name"]
        moves_list.append(sm_obj)

    # Parse Passives and Superawakening
    pass_sec_m = re.search(r"🛡️ Passive Details 🌟(.*?)📊 Base Stats 📊", main_part, re.S)
    pass_sec = pass_sec_m.group(1) if pass_sec_m else ""
    sa_passive = None
    sa_m = re.search(r"\(🌅🌟\) Superawakened Passive:\s*(.+)\n(.+)", pass_sec)
    if sa_m:
        sa_name = sa_m.group(1).strip()
        sa_desc = sa_m.group(2).strip().replace("\u00a0", " ")
        sa_id = get_or_create_passive_id(sa_name, sa_desc)
        sa_passive = {
            "id": sa_id,
            "name": sa_name,
            "description": sa_desc,
            "slot": 0,
            "childPassives": []
        }

    passives_list = []
    for pm in re.finditer(r"Passive (\d+)(?:\(🏅\))?:\s*(.+)\n(.+)", pass_sec):
        p_slot = int(pm.group(1))
        p_name = pm.group(2).strip()
        p_desc = pm.group(3).strip().replace("\u00a0", " ")
        p_id = get_or_create_passive_id(p_name, p_desc)
        passives_list.append({
            "id": p_id,
            "name": p_name,
            "description": p_desc,
            "slot": p_slot,
            "childPassives": []
        })

    # Parse Base Stats
    def parse_stat_levels(stat_block):
        vals_by_lvl = {}
        for lvl in [1, 140, 150, 200]:
            m_lv = re.search(rf"Lv\.\s*{lvl}\s*\nHP\s*:\s*(\d+)\s*\|\s*Attack\s*:\s*(\d+)\s*\|\s*Defense\s*:\s*(\d+)\s*\|\s*Sp\.\s*Atk\s*:\s*(\d+)\s*\|\s*Sp\.\s*Def\s*:\s*(\d+)\s*\|\s*Speed\s*:\s*(\d+)", stat_block)
            if m_lv:
                vals_by_lvl[lvl] = [int(m_lv.group(i)) for i in range(1, 7)]
        stats_out = {}
        for idx, key in enumerate(["hp", "atk", "def", "spa", "spd", "spe"]):
            stats_out[key] = compute_7_stats(
                vals_by_lvl[1][idx],
                vals_by_lvl[140][idx],
                vals_by_lvl[150][idx],
                vals_by_lvl[200][idx]
            )
        return stats_out

    stats_dict = parse_stat_levels(main_part)

    # Parse Tera / Mega variations
    variations_list = []
    has_tera = False
    has_mega = False
    if tera_part:
        has_tera = True
        tm_match = re.search(r"(💎 Tera Move:.*?(?=🛡️ Passives Details 🌟))", tera_part, re.S)
        tera_move_id = 0
        if tm_match:
            tm_obj = parse_single_move(tm_match.group(1), 6, is_sync=False)
            tera_move_id = tm_obj["id"]
            moves_list.append(tm_obj)
        var_passives = [dict(p) for p in passives_list]
        for pm in re.finditer(r"Passive (\d+):\s*(.+)\n(.+)", tera_part):
            p_slot = int(pm.group(1))
            p_name = pm.group(2).strip()
            p_desc = pm.group(3).strip().replace("\u00a0", " ")
            p_id = get_or_create_passive_id(p_name, p_desc)
            replaced = False
            for vp in var_passives:
                if vp["slot"] == p_slot:
                    vp["id"] = p_id
                    vp["name"] = p_name
                    vp["description"] = p_desc
                    replaced = True
            if not replaced:
                var_passives.append({
                    "id": p_id,
                    "name": p_name,
                    "description": p_desc,
                    "slot": p_slot,
                    "childPassives": []
                })
        variations_list.append({
            "formId": 7,
            "formName": "Tera",
            "type": pkmn_type,
            "actorId": meta["pokemonActorId"],
            "statMultiplier": {
                "atk": 1.0,
                "def": 1.0,
                "spa": 1.0,
                "spd": 1.0,
                "spe": 1.0
            },
            "passives": var_passives,
            "terastalMoveId": tera_move_id
        })
    elif mega_part:
        has_mega = True
        variations_list.append({
            "formId": 1,
            "formName": "Mega",
            "type": pkmn_type,
            "actorId": meta["pokemonActorId"],
            "statMultiplier": {
                "atk": 1.0,
                "def": 1.2,
                "spa": 1.0,
                "spd": 1.0,
                "spe": 1.2
            },
            "passives": [dict(p) for p in passives_list],
            "terastalMoveId": 0
        })

    # Build grid
    raw_grid = grids_by_pair.get(pair_name, [])
    grid_list = []
    prefix_7 = meta["trainerId"][:7]
    for c in raw_grid:
        grid_list.append({
            "cellId": int(f"{prefix_7}{c['cellNum']-1:03d}"),
            "q": c["q"],
            "r": c["r"],
            "s": c["s"],
            "energyCost": c["energyCost"],
            "orbCost": c["orbCost"],
            "moveLevel": c["moveLevel"],
            "colorKind": c["colorKind"],
            "title": c["title"],
            "description": c["description"],
            "statBonus": c["statBonus"],
            "powerBonus": c["powerBonus"],
            "abilityId": c["abilityId"]
        })

    dt = datetime.datetime.strptime(meta["releaseDate"], "%Y-%m-%d").replace(hour=6, tzinfo=datetime.timezone.utc)
    rel_ts = int(dt.timestamp())

    pair_detail = {
        "trainerId": meta["trainerId"],
        "trainerBaseId": meta["trainerBaseId"],
        "monsterId": meta["monsterId"],
        "monsterBaseId": meta["monsterBaseId"],
        "displayName": meta["displayName"],
        "trainerName": meta["trainerNameEn"],
        "monsterName": meta["pokemonNameEn"],
        "pokemonName": meta["pokemonNameEn"],
        "type": pkmn_type,
        "weakness": weakness,
        "role": role_str,
        "exRole": ex_role_str,
        "rarity": rarity,
        "hasEx": True,
        "hasMega": has_mega,
        "hasTera": has_tera,
        "hasDynamax": False,
        "hasSuperAwakening": sa_passive is not None,
        "superAwakeningPassive": sa_passive,
        "syncMoveName": sync_move_name,
        "iconUrl": meta["iconUrl"],
        "pokemonIconUrl": meta["pokemonIconUrl"],
        "releaseDate": meta["releaseDate"],
        "releaseTimestamp": rel_ts,
        "stats": stats_dict,
        "moves": moves_list,
        "passives": passives_list,
        "variations": variations_list,
        "grid": grid_list,
        "themes": theme_ids
    }

    with open(os.path.join(pairs_dir, f"{meta['trainerId']}.json"), "w", encoding="utf-8") as f:
        json.dump(pair_detail, f, indent=2, ensure_ascii=False)

    manifest_entry = {
        "trainerId": meta["trainerId"],
        "monsterId": meta["monsterId"],
        "monsterBaseId": meta["monsterBaseId"],
        "displayName": meta["displayName"],
        "trainerName": meta["trainerNameEn"],
        "monsterName": meta["pokemonNameEn"],
        "pokemonName": meta["pokemonNameEn"],
        "type": pkmn_type,
        "role": role_str,
        "exRole": ex_role_str,
        "rarity": rarity,
        "hasEx": True,
        "hasMega": has_mega,
        "hasTera": has_tera,
        "hasDynamax": False,
        "hasSuperAwakening": sa_passive is not None,
        "iconUrl": meta["iconUrl"],
        "pokemonIconUrl": meta["pokemonIconUrl"],
        "gridTileCount": len(grid_list),
        "trainerBaseId": meta["trainerBaseId"],
        "trainerKey": meta["trainerKey"],
        "pokemonKey": meta["pokemonKey"],
        "releaseTimestamp": rel_ts,
        "releaseDate": meta["releaseDate"],
        "themes": theme_ids
    }
    if sa_passive:
        manifest_entry["superAwakeningPassive"] = {
            "id": sa_passive["id"],
            "name": sa_passive["name"],
            "description": sa_passive["description"]
        }
    new_manifest_entries.append(manifest_entry)

    # Update themes_database.json
    themes_db["pairThemes"][meta["trainerId"]] = theme_ids

    # Update flat locales (en.json & es.json)
    en_locale[f"trainer_name_{meta['trainerId']}"] = meta["trainerNameEn"]
    es_locale[f"trainer_name_{meta['trainerId']}"] = meta["trainerNameEs"]
    en_locale[f"trainer_name_{meta['trainerKey']}"] = meta["trainerNameEn"]
    es_locale[f"trainer_name_{meta['trainerKey']}"] = meta["trainerNameEs"]
    en_locale[f"pokemon_name_{meta['monsterBaseId']}"] = meta["pokemonNameEn"]
    es_locale[f"pokemon_name_{meta['monsterBaseId']}"] = meta["pokemonNameEs"]

    print(f"Created {meta['trainerId']}.json ({pair_name}) -> {len(moves_list)} moves, {len(passives_list)} passives, {len(grid_list)} grid cells, themes={theme_ids}")

# Prepend new manifest entries sorted by releaseTimestamp descending
new_ids = {e["trainerId"] for e in new_manifest_entries}
manifest = [m for m in manifest if m["trainerId"] not in new_ids]
new_manifest_entries.sort(key=lambda x: (x["releaseTimestamp"], x["trainerId"]), reverse=True)
manifest = new_manifest_entries + manifest

with open(os.path.join(ROOT, "data", "pairs_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

with open(os.path.join(ROOT, "data", "themes_database.json"), "w", encoding="utf-8") as f:
    json.dump(themes_db, f, indent=2, ensure_ascii=False)

with open(os.path.join(ROOT, "locales", "en.json"), "w", encoding="utf-8") as f:
    json.dump(en_locale, f, indent=2, ensure_ascii=False)

with open(os.path.join(ROOT, "locales", "es.json"), "w", encoding="utf-8") as f:
    json.dump(es_locale, f, indent=2, ensure_ascii=False)

print("Completed v2.73 sync pairs import successfully!")
