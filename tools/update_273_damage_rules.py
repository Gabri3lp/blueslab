import json, os

ROOT = r"C:\Users\Gabri\Documents\blueslab\src\BluesLab\wwwroot"
dr_path = os.path.join(ROOT, "data", "damage_rules.json")

with open(dr_path, "r", encoding="utf-8") as f:
    dr = json.load(f)

# 1. masterPassives: Water Teamwork for Lyra (Special Costume) & Marill
mp_list = dr.setdefault("masterPassives", [])
if not any(x.get("syncPair") == "Lyra (Special Costume) & Marill" for x in mp_list):
    mp_list.append({
        "syncPair": "Lyra (Special Costume) & Marill",
        "passiveName": "Water Teamwork",
        "theme": "Water",
        "category": "any",
        "appliesToSync": False,
        "basePowerUpPct": 10,
        "perAdditionalAllyPct": 5,
        "maxPowerUpPct": 20
    })

# 2. moveScaling: Shelly & Sharpedo, Korrina & Machoke
ms_list = dr.setdefault("moveScaling", [])
new_scalings = [
    {
        "syncPair": "Shelly & Sharpedo",
        "moveName": "Brains of Team Aqua Water Impact",
        "stat": "cond:rainy",
        "who": "user",
        "direction": "lowered",
        "stepPer1000": 1000,
        "capPer1000": 2000
    },
    {
        "syncPair": "Korrina & Machoke",
        "moveName": "Always in the Zone Fighting Impact",
        "stat": "cond:paralyzed",
        "who": "target",
        "direction": "lowered",
        "stepPer1000": 1000,
        "capPer1000": 2000
    }
]
for ns in new_scalings:
    if not any(x.get("syncPair") == ns["syncPair"] and x.get("moveName") == ns["moveName"] for x in ms_list):
        ms_list.append(ns)

# 3. damagePassives
dp_list = dr.setdefault("damagePassives", [])
existing_dp_names = {dp["name"] for dp in dp_list}

sync_buff_sub = {
    "name": "Moves ↑ as Sync Buff ↑",
    "type": "powerup",
    "applies_to": "moves",
    "affects": "self",
    "mechanism": "sync_buff_scaling",
    "value": 1,
    "stat": "sync_buff",
    "stat_target": "self",
    "conditions": [],
    "move_name": "",
    "sub_passives": []
}
crit_strike_2_sub = {
    "name": "Critical Strike 2",
    "type": "powerup",
    "applies_to": "all",
    "affects": "self",
    "mechanism": "flat_boost",
    "value": 2,
    "stat": "",
    "stat_target": "",
    "conditions": [["critical"]],
    "move_name": "",
    "sub_passives": []
}

new_dps = [
    {
        "name": "Burning Flames of Conviction",
        "type": "powerup",
        "applies_to": "sync_move",
        "affects": "self",
        "mechanism": "SYUN",
        "value": 1,
        "stat": "",
        "stat_target": "self",
        "conditions": [],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Curved Beads of Fiery Envy",
        "type": "powerup",
        "applies_to": "all",
        "affects": "team",
        "mechanism": "flat_boost",
        "value": 2,
        "stat": "",
        "stat_target": "",
        "conditions": [["special"]],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Sword Clad in Hatred and Snow",
        "type": "powerup",
        "applies_to": "all",
        "affects": "team",
        "mechanism": "flat_boost",
        "value": 2,
        "stat": "",
        "stat_target": "",
        "conditions": [["physical"]],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Trap and Buff 3",
        "type": "powerup",
        "applies_to": "pokemon_moves",
        "affects": "self",
        "mechanism": "flat_boost",
        "value": 3,
        "stat": "",
        "stat_target": "",
        "conditions": [["trapped"]],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Evasive Sync-Up 9",
        "type": "powerup",
        "applies_to": "sync_move",
        "affects": "self",
        "mechanism": "stat_is_raised",
        "value": 9,
        "stat": "eva",
        "stat_target": "self",
        "conditions": [],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Opp Defense ↓: S-Moves ↑ 4",
        "type": "powerup",
        "applies_to": "sync_move",
        "affects": "self",
        "mechanism": "stat_is_lowered",
        "value": 4,
        "stat": "def",
        "stat_target": "target",
        "conditions": [],
        "move_name": "",
        "sub_passives": []
    },
    {
        "name": "Ace of Sparks",
        "type": "composite",
        "applies_to": "",
        "affects": "",
        "mechanism": "",
        "value": 0,
        "stat": "",
        "stat_target": "",
        "conditions": [],
        "move_name": "",
        "sub_passives": [sync_buff_sub, crit_strike_2_sub]
    },
    {
        "name": "Power of Space to Change the World",
        "type": "composite",
        "applies_to": "",
        "affects": "",
        "mechanism": "",
        "value": 0,
        "stat": "",
        "stat_target": "",
        "conditions": [],
        "move_name": "",
        "sub_passives": [
            {
                "name": "Superduper Effective 5",
                "type": "powerup",
                "applies_to": "pokemon_moves",
                "affects": "self",
                "mechanism": "flat_boost",
                "value": 5,
                "stat": "",
                "stat_target": "",
                "conditions": [["super_effective"]],
                "move_name": "",
                "sub_passives": []
            },
            sync_buff_sub,
            crit_strike_2_sub
        ]
    },
    {
        "name": "Infinite Bond of Resonant Spirits",
        "type": "composite",
        "applies_to": "",
        "affects": "",
        "mechanism": "",
        "value": 0,
        "stat": "",
        "stat_target": "",
        "conditions": [],
        "move_name": "",
        "sub_passives": [sync_buff_sub, crit_strike_2_sub]
    },
    {
        "name": "Soul-Purifying Flames",
        "type": "composite",
        "applies_to": "",
        "affects": "",
        "mechanism": "",
        "value": 0,
        "stat": "",
        "stat_target": "",
        "conditions": [],
        "move_name": "",
        "sub_passives": [sync_buff_sub, crit_strike_2_sub]
    },
    {
        "name": "Sandstorm-Slicing Sickles",
        "type": "composite",
        "applies_to": "",
        "affects": "",
        "mechanism": "",
        "value": 0,
        "stat": "",
        "stat_target": "",
        "conditions": [],
        "move_name": "",
        "sub_passives": [
            {
                "name": "Surging Sand 5",
                "type": "powerup",
                "applies_to": "sync_move",
                "affects": "self",
                "mechanism": "flat_boost",
                "value": 5,
                "stat": "",
                "stat_target": "",
                "conditions": [["sandstorm"]],
                "move_name": "",
                "sub_passives": []
            },
            sync_buff_sub,
            crit_strike_2_sub
        ]
    }
]

for ndp in new_dps:
    if ndp["name"] not in existing_dp_names:
        dp_list.append(ndp)

# 4. luckySkills
ls_list = dr.setdefault("luckySkills", [])
ls_by_name = {ls["name"]: ls for ls in ls_list}

def add_or_update_lucky_skill(name, pairs):
    if name in ls_by_name:
        cur_pairs = ls_by_name[name].get("restricted_to_pairs") or []
        for p in pairs:
            if p not in cur_pairs:
                cur_pairs.append(p)
        ls_by_name[name]["restricted_to_pairs"] = cur_pairs
    else:
        entry = {
            "name": name,
            "restricted_to_roles": None,
            "restricted_to_pairs": pairs
        }
        ls_list.append(entry)
        ls_by_name[name] = entry

add_or_update_lucky_skill("Opp Defense ↓: S-Moves ↑ 4", ["Sygna Suit Ghetsis & Chien-Pao"])
add_or_update_lucky_skill("Superduper Effective 3", ["Nemona & Pawmot"])
add_or_update_lucky_skill("Trap and Sync 4", ["Sygna Suit Lysandre (Alt.) & Chi-Yu"])
add_or_update_lucky_skill("Shower Power 4", ["Archie & Kyogre"])
add_or_update_lucky_skill("Solar Flare 4", ["Maxie & Groudon"])
add_or_update_lucky_skill("Ace of Sparks", ["Volkner & Luxray"])
add_or_update_lucky_skill("Power of Space to Change the World", ["Cyrus & Palkia"])
add_or_update_lucky_skill("Infinite Bond of Resonant Spirits", ["Palmer & Regigigas"])
add_or_update_lucky_skill("Soul-Purifying Flames", ["Irida (Anniversary 2025) & Typhlosion"])
add_or_update_lucky_skill("Sandstorm-Slicing Sickles", ["Arc Suit Cynthia & Garchomp"])

with open(dr_path, "w", encoding="utf-8") as f:
    json.dump(dr, f, indent=2, ensure_ascii=False)

print("Updated damage_rules.json successfully!")
