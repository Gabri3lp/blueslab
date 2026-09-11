import urllib.request
import csv
import io
import json
import re
import os

stage_tabs = [
    ("1650345894", "AnabelFF", "Anabel's Flickering Flames", "Entei", "Fire", "Water"),
    ("1741304576", "ThortonFF", "Thorton's Freezing Frost", "Articuno", "Ice", "Fire"),
    ("1924026928", "DarachDW", "Darach's Daring Wings", "Staraptor", "Flying", "Rock"),
    ("925429129",  "ArgentaGC", "Argenta's Glistening Crystals", "Skarmory", "Steel", "Grass"),
    ("421291009",  "PalmerRM", "Palmer's Rumbling Might", "Regigigas", "Normal", "Fighting"),
    ("1842600990", "LucyEV", "Lucy's Entangling Vipers", "Seviper", "Poison", "Ground"),
    ("1728091004", "LeonUB", "Leon's Unbeatable Bonds", "Charizard", "Fire", "Electric"),
    ("438037569",  "NitaBL", "Nita's Breezy Land", "Landorus", "Ground", "Ice"),
    ("853536673",  "NolandPP", "Noland's Piercing Pins", "Pinsir", "Bug", "Flying"),
    ("1446835045", "GiovanniDP", "Giovanni's Destructive Power", "Mewtwo", "Psychic", "Bug"),
    ("1652235416", "EvelynHS", "Evelyn's Heated Spirit", "Entei", "Fire", "Fairy"),
    ("1633964033", "MaskedRoyalEC", "Masked Royal's Entertaining Clash", "Incineroar", "Fire", "Poison"),
    ("1848852370", "NemonaLS", "Nemona's Lightning Spirit", "Pawmot", "Electric", "Psychic"),
    ("1348266858", "MorganTL", "Morgan's Tranquil Lake", "Cobalion", "Steel", "Dragon"),
    ("1619997153", "DanaIP", "Dana's Icy Peaks", "Regice", "Ice", "Steel"),
    ("328690724",  "WallySS", "Wally's Spirited Strike", "Gallade", "Fighting", "Ghost"),
    ("203549936",  "DahliaLD", "Dahlia's Lively Dance", "Ludicolo", "Water", "Bug"),
    ("1358150860", "ArceusDG", "Arceus' Divine Gauntlet", "Arceus", "Normal", "Fighting"),
]

# Trainer / Boss name mappings
LEADER_MAP = {
    "AnabelFF": "Anabel",
    "ThortonFF": "Thorton",
    "DarachDW": "Darach",
    "ArgentaGC": "Argenta",
    "PalmerRM": "Palmer",
    "LucyEV": "Lucy",
    "LeonUB": "Leon",
    "NitaBL": "Nita",
    "NolandPP": "Noland",
    "GiovanniDP": "Giovanni",
    "EvelynHS": "Evelyn",
    "MaskedRoyalEC": "The Masked Royal",
    "NemonaLS": "Nemona",
    "MorganTL": "Morgan",
    "DanaIP": "Dana",
    "WallySS": "Wally",
    "DahliaLD": "Dahlia",
    "ArceusDG": "Arceus"
}

# Pokémon ID and icon mapping
POKEMON_META = {
    "Entei": {"id": "024400", "icon": "img/pokemon/024400_128.png"},
    "Arcanine": {"id": "005900", "icon": "img/pokemon/005900_128.png"},
    "Ninetales": {"id": "003800", "icon": "img/pokemon/003800_128.png"},
    "Articuno": {"id": "014400", "icon": "img/pokemon/014400_128.png"},
    "Machamp": {"id": "006800", "icon": "img/pokemon/006800_128.png"},
    "Magneton": {"id": "008200", "icon": "img/pokemon/008200_128.png"},
    "Staraptor": {"id": "039800", "icon": "img/pokemon/039800_128.png"},
    "Pidgeot": {"id": "001800", "icon": "img/pokemon/001800_128.png"},
    "Honchkrow": {"id": "043000", "icon": "img/pokemon/043000_128.png"},
    "Skarmory": {"id": "022700", "icon": "img/pokemon/022700_128.png"},
    "Bronzong": {"id": "043700", "icon": "img/pokemon/043700_128.png"},
    "Regigigas": {"id": "048600", "icon": "img/pokemon/048600_128.png"},
    "Snorlax": {"id": "014300", "icon": "img/pokemon/014300_128.png"},
    "Empoleon": {"id": "039500", "icon": "img/pokemon/039500_128.png"},
    "Seviper": {"id": "033600", "icon": "img/pokemon/033600_128.png"},
    "Nidoking": {"id": "003400", "icon": "img/pokemon/003400_128.png"},
    "Nidoqueen": {"id": "003100", "icon": "img/pokemon/003100_128.png"},
    "Charizard": {"id": "000600", "icon": "img/pokemon/000600_128.png"},
    "Butterfree": {"id": "001200", "icon": "img/pokemon/001200_128.png"},
    "Lapras": {"id": "013100", "icon": "img/pokemon/013100_128.png"},
    "Landorus": {"id": "064500", "icon": "img/pokemon/064500_128.png"},
    "Hippowdon": {"id": "045000", "icon": "img/pokemon/045000_128.png"},
    "Garchomp": {"id": "044500", "icon": "img/pokemon/044500_128.png"},
    "Pinsir": {"id": "012700", "icon": "img/pokemon/012700_128.png"},
    "Poliwrath": {"id": "006200", "icon": "img/pokemon/006200_128.png"},
    "Mewtwo": {"id": "015000", "icon": "img/pokemon/015000_128.png"},
    "Hypno": {"id": "009700", "icon": "img/pokemon/009700_128.png"},
    "Hydreigon": {"id": "063500", "icon": "img/pokemon/063500_128.png"},
    "Dragapult": {"id": "088700", "icon": "img/pokemon/088700_128.png"},
    "Incineroar": {"id": "072700", "icon": "img/pokemon/072700_128.png"},
    "Primarina": {"id": "073000", "icon": "img/pokemon/073000_128.png"},
    "Meganium": {"id": "015400", "icon": "img/pokemon/015400_128.png"},
    "Pawmot": {"id": "092300", "icon": "img/pokemon/092300_128.png"},
    "Toxtricity": {"id": "084900", "icon": "img/pokemon/084900_128.png"},
    "Cobalion": {"id": "063800", "icon": "img/pokemon/063800_128.png"},
    "Haxorus": {"id": "061200", "icon": "img/pokemon/061200_128.png"},
    "Regice": {"id": "037800", "icon": "img/pokemon/037800_128.png"},
    "Aurorus": {"id": "069900", "icon": "img/pokemon/069900_128.png"},
    "Abomasnow": {"id": "046000", "icon": "img/pokemon/046000_128.png"},
    "Gallade": {"id": "047500", "icon": "img/pokemon/047500_128.png"},
    "Gardevoir": {"id": "028200", "icon": "img/pokemon/028200_128.png"},
    "Slowbro": {"id": "008000", "icon": "img/pokemon/008000_128.png"},
    "Ludicolo": {"id": "027200", "icon": "img/pokemon/027200_128.png"},
    "Weavile": {"id": "046100", "icon": "img/pokemon/046100_128.png"},
    "Tsareena": {"id": "076300", "icon": "img/pokemon/076300_128.png"},
    "Arceus": {"id": "049300", "icon": "img/pokemon/049300_128.png"},
    "Dialga": {"id": "048300", "icon": "img/pokemon/048300_128.png"},
    "Palkia": {"id": "048400", "icon": "img/pokemon/048400_128.png"}
}

def get_pokemon_meta(name):
    clean = name.split("(")[0].strip()
    if clean in POKEMON_META:
        return POKEMON_META[clean]
    for k, v in POKEMON_META.items():
        if k.lower() in name.lower():
            return v
    return {"id": "000000", "icon": "img/pokemon/NONE.png"}

def fetch_csv(gid):
    url = f"https://docs.google.com/spreadsheets/d/1J_Wf9t4ZIOMwdlYEsIzgENDdYCut-AEX0pJiwbcIrVY/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")

def parse_stat_table(rows, start_r, start_c):
    stats = {}
    mitigations = {}
    status_mitigations = {}
    weakness = "Normal"
    for offset in range(1, 11):
        if start_r + offset >= len(rows): break
        r = rows[start_r + offset]
        if start_c >= len(r): continue
        s_name = r[start_c].strip().lower()
        if not s_name: continue
        
        # Stat Val
        if start_c + 1 < len(r):
            val_clean = re.sub(r'[^0-9]', '', r[start_c + 1])
            if val_clean:
                s_key = "spa" if "sp. atk" in s_name or "sp. attack" in s_name else ("spd" if "sp. def" in s_name or "sp. defense" in s_name else ("atk" if "att" in s_name or "attack" in s_name else s_name[:3]))
                stats[s_key] = int(val_clean)
        
        # Mitigation
        if start_c + 2 < len(r):
            m_str = r[start_c + 2].strip()
            s_key = "spa" if "sp. atk" in s_name or "sp. attack" in s_name else ("spd" if "sp. def" in s_name or "sp. defense" in s_name else ("atk" if "att" in s_name or "attack" in s_name else ("crit" if "cri" in s_name else s_name[:3])))
            if m_str.isdigit():
                mitigations[s_key] = int(m_str)
            elif m_str.lower() == "immune":
                mitigations[s_key] = 10
                
        # Status Mitigation & Weakness (c+3, c+4)
        if start_c + 3 < len(r) and start_c + 4 < len(r):
            st_name = r[start_c + 3].strip().lower()
            st_val = r[start_c + 4].strip()
            if "weakness" in st_name:
                weakness = st_val.strip()
            elif st_val.isdigit():
                status_mitigations[st_name] = int(st_val)
                
    return stats, mitigations, status_mitigations, weakness

def extract_stage_data(gid, code, default_title, default_boss, stage_type, default_weakness):
    csv_str = fetch_csv(gid)
    rows = list(csv.reader(io.StringIO(csv_str)))
    
    leader_name = LEADER_MAP.get(code, "Boss")
    fight_id = f"ultimate_{code.lower()}"
    title = f"vs. {leader_name} & {default_boss}"
    theme = default_title
    
    # Extract Center Boss Stats (row 3, col 3)
    c_stats, c_mits, c_status_mits, c_weak = parse_stat_table(rows, 3, 3)
    if not c_weak or c_weak == "Normal":
        c_weak = default_weakness
        
    # Default Center Opponent
    c_meta = get_pokemon_meta(default_boss)
    center_opp = {
        "slotIndex": 1, # Center
        "trainerName": leader_name,
        "pokemonName": default_boss,
        "pokemonId": c_meta["id"],
        "iconUrl": c_meta["icon"],
        "weakness": c_weak,
        "hp": c_stats.get("hp", 800000),
        "atk": c_stats.get("atk", 4000),
        "def": c_stats.get("def", 83),
        "spa": c_stats.get("spa", 4000),
        "spd": c_stats.get("spd", 83),
        "spe": c_stats.get("spe", 67),
        "mitigations": c_mits,
        "statusMitigations": c_status_mits,
        "passives": []
    }
    
    # Find Side Opponents Tables
    left_opp = None
    right_opp = None
    
    for r_idx in range(25, min(45, len(rows))):
        r = rows[r_idx]
        if len(r) > 5 and r[0].strip() == "Statistic" and r[5].strip() == "Statistic":
            # Left Opponent is in col 0, Right Opponent is in col 5
            # Header names in row r_idx - 1
            left_name = rows[r_idx - 1][0].strip() if r_idx > 0 and len(rows[r_idx - 1]) > 0 else "Left Side"
            right_name = rows[r_idx - 1][5].strip() if r_idx > 0 and len(rows[r_idx - 1]) > 5 else "Right Side"
            
            l_stats, l_mits, l_status_mits, l_weak = parse_stat_table(rows, r_idx, 0)
            r_stats, r_mits, r_status_mits, r_weak = parse_stat_table(rows, r_idx, 5)
            
            l_meta = get_pokemon_meta(left_name)
            r_meta = get_pokemon_meta(right_name)
            
            left_opp = {
                "slotIndex": 0, # Left
                "trainerName": "Teammate",
                "pokemonName": left_name,
                "pokemonId": l_meta["id"],
                "iconUrl": l_meta["icon"],
                "weakness": l_weak if l_weak != "Normal" else c_weak,
                "hp": l_stats.get("hp", 200000),
                "atk": l_stats.get("atk", 3000),
                "def": l_stats.get("def", 83),
                "spa": l_stats.get("spa", 3000),
                "spd": l_stats.get("spd", 83),
                "spe": l_stats.get("spe", 200),
                "mitigations": l_mits,
                "statusMitigations": l_status_mits,
                "passives": []
            }
            
            right_opp = {
                "slotIndex": 2, # Right
                "trainerName": "Teammate",
                "pokemonName": right_name,
                "pokemonId": r_meta["id"],
                "iconUrl": r_meta["icon"],
                "weakness": r_weak if r_weak != "Normal" else c_weak,
                "hp": r_stats.get("hp", 200000),
                "atk": r_stats.get("atk", 3000),
                "def": r_stats.get("def", 83),
                "spa": r_stats.get("spa", 3000),
                "spd": r_stats.get("spd", 83),
                "spe": r_stats.get("spe", 200),
                "mitigations": r_mits,
                "statusMitigations": r_status_mits,
                "passives": []
            }
            break
            
    # Stage Gimmicks & Passives Construction
    passives = []
    rules = []
    
    if "Anabel" in code or "Evelyn" in code or "Dahlia" in code:
        passives.append({
            "name": "Fluid Fortification",
            "description": "The net sum of stat ranks that the user has determines how much damage it will take from attack moves and sync moves (up to 100% reduction at >= +10, 0% at <= -10).",
            "mechanism": "damage_mitigation",
            "condition": "fluid_fortification",
            "multiplier": 1.0
        })
        rules.append("Fluid Fortification: The net sum of enemy stat ranks dictates damage mitigation. Piercing Blows bypasses this.")
        
    if "Thorton" in code or "Nemona" in code:
        passives.append({
            "name": "No Negative Status Change: Defense ×3 & Sp. Def ×3",
            "description": "The user's Defense and Sp. Def are multiplied by 3 when it is not affected by a negative status change.",
            "mechanism": "stat_multiplier",
            "condition": "no_negative_stat",
            "multiplier": 3.0
        })
        rules.append("No Negative Stat Change: Enemy Defense & Sp. Def are multiplied by 3 unless debuffed. Piercing Blows does NOT bypass stat multipliers.")
        
    if "Darach" in code or "Giovanni" in code:
        passives.append({
            "name": "Unaffected by Field Effect: Defense ×3 & Sp. Def ×3",
            "description": "The user's Defense and Sp. Def are multiplied by 3 when it is not affected by a field effect (Weather/Terrain/Zone/Damage Field).",
            "mechanism": "stat_multiplier",
            "condition": "no_field_effect",
            "multiplier": 3.0
        })
        rules.append("Unaffected by Field Effect: Enemy Defense & Sp. Def are multiplied by 3 unless a field effect (WTZ/Damage Field) is active.")
        
    if "Wally" in code:
        passives.append({
            "name": "Unaffected by Field Effect: Defense ×3 & Sp. Def ×3",
            "description": "The user's Defense and Sp. Def are multiplied by 3 when it is not affected by a field effect.",
            "mechanism": "stat_multiplier",
            "condition": "no_field_effect",
            "multiplier": 3.0
        })
        passives.append({
            "name": "Sp. Def ↑: Defense x3 & Sp. Def x3",
            "description": "The user's Defense and Sp. Def are multiplied by 3 when its Sp. Def is raised.",
            "mechanism": "stat_multiplier",
            "condition": "spdef_up",
            "multiplier": 3.0
        })
        rules.append("Unaffected by Field Effect: Def/SpD x3 without WTZ. Also Sp. Def ↑: Def/SpD x3 if Sp. Def buffed.")

    if "Nita" in code:
        passives.append({
            "name": "Speed ↑: Defense & Sp. Def x3",
            "description": "The user's Defense and Sp. Def are multiplied by 3 when its Speed is raised.",
            "mechanism": "stat_multiplier",
            "condition": "speed_up",
            "multiplier": 3.0
        })
        rules.append("Speed ↑: Enemy Defense & Sp. Def are multiplied by 3 when its Speed is raised.")
        
    if "Argenta" in code:
        passives.append({
            "name": "Rain Gear 5",
            "description": "Reduces damage by 50% when the user is hit by an attack move while the weather is rainy.",
            "mechanism": "damage_mitigation",
            "condition": "rain",
            "multiplier": 0.5
        })
        rules.append("Rain Gear 5: Reduces attack move damage by 50% under Rain. Piercing Blows bypasses this.")
        
    if "MaskedRoyal" in code:
        passives.append({
            "name": "Robust Physique",
            "description": "Protects the user against critical hits when it is not affected by a status condition.",
            "mechanism": "crit_immunity",
            "condition": "no_status_condition",
            "multiplier": 0.0
        })
        rules.append("Robust Physique: Immune to critical hits unless affected by a status condition. Piercing Blows bypasses this.")

    if "Dana" in code:
        rules.append("Dana's Icy Peaks: Moves and sync moves powered up heavily under Ice Zone / Hail.")
        
    if "Morgan" in code:
        rules.append("Morgan's Tranquil Lake: Opponent stats reduction powers up enemy moves.")
        
    if "Palmer" in code:
        rules.append("Palmer's Rumbling Might: Max Moves target all allies, massive defensive profile.")
        
    if "Lucy" in code:
        rules.append("Lucy's Entangling Vipers: Severe poison mechanics, cleanses debuffs at 40% HP.")
        
    if "Leon" in code:
        rules.append("Leon's Unbeatable Bonds: Moves/sync moves power x3 when unaffected by status.")

    if "Noland" in code:
        rules.append("Noland's Piercing Pins: Good Form scaling based on raised stats.")
        
    if "Arceus" in code:
        rules.append("Arceus' Divine Gauntlet: Maximum stats boss with multi-phase Judgement attacks.")

    # Attach passives to center
    center_opp["passives"] = passives
    
    # Assemble Opponents list: [Left (0), Center (1), Right (2)]
    opponents = []
    if left_opp: opponents.append(left_opp)
    opponents.append(center_opp)
    if right_opp: opponents.append(right_opp)
    
    return {
        "fightId": fight_id,
        "title": f"{theme} ({leader_name})",
        "leader": leader_name,
        "stageType": stage_type,
        "theme": theme,
        "rules": rules,
        "opponents": opponents
    }

all_stages = []
for gid, code, title, boss, stype, def_weak in stage_tabs:
    print(f"Extracting {code}...")
    stg = extract_stage_data(gid, code, title, boss, stype, def_weak)
    all_stages.append(stg)

out_path = "src/BluesLab/wwwroot/data/ultimate_stages.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_stages, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {out_path} with {len(all_stages)} Ultimate Battles!")
