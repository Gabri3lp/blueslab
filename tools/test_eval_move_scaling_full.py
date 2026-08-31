import json

rules = json.loads(open("src/BluesLab/wwwroot/data/damage_rules.json", encoding="utf-8").read())
move_scalings = rules.get("moveScaling", [])

def eval_move_scaling_mock(rule, is_physical, move_type, ally_stages, enemy_stages, field_weather, field_terrain, field_zone, enemy_status, enemy_volatiles, enemy_rebuffs, ally_pmun, ally_smun, ally_syun, is_se):
    who = rule.get("who", "user")
    stages = ally_stages if who == "user" else enemy_stages
    direction = rule.get("direction", "raised")
    is_raised = direction == "raised"
    stat = rule.get("stat", "")
    step = rule.get("stepPer1000", 0) / 1000.0
    cap = rule.get("capPer1000", 0) / 1000.0 if rule.get("capPer1000") else 0

    count = 0
    if stat == "all_stats":
        for k in ["atk", "def", "spa", "spd", "spe", "acc", "eva"]:
            s = stages.get(k, 0)
            count += max(0, min(s, 6)) if is_raised else max(0, min(-s, 6))
    elif stat == "def_spd":
        s1 = stages.get("def", 0)
        s2 = stages.get("spd", 0)
        count += (max(0, s1) if is_raised else max(0, -s1)) + (max(0, s2) if is_raised else max(0, -s2))
    elif stat == "rebuff":
        reb = enemy_rebuffs.get(move_type, 0)
        count = max(0, -reb) if not is_raised else max(0, reb)
    elif stat == "boost_rank_pmun":
        count = ally_pmun
    elif stat == "boost_rank_smun":
        count = ally_smun
    elif stat == "boost_rank_syun":
        count = ally_syun
    elif stat.startswith("cond:"):
        cond = stat[5:]
        matched = False
        if cond == "sunny": matched = field_weather == "Sunny"
        elif cond == "rain": matched = field_weather == "Rainy"
        elif cond == "sandstorm": matched = field_weather == "Sandstorm"
        elif cond == "hail": matched = field_weather == "Hail"
        elif cond == "any_weather": matched = bool(field_weather)
        elif cond == "electric_terrain": matched = field_terrain == "Electric Terrain"
        elif cond == "grassy_terrain": matched = field_terrain == "Grassy Terrain"
        elif cond == "any_terrain": matched = bool(field_terrain)
        elif cond == "burned": matched = enemy_status == "burned"
        elif cond == "paralyzed": matched = enemy_status == "paralyzed"
        elif cond == "poisoned": matched = enemy_status in ["poisoned", "badly poisoned"]
        elif cond == "asleep": matched = enemy_status == "asleep"
        elif cond == "frozen": matched = enemy_status == "frozen"
        elif cond == "any_status": matched = bool(enemy_status)
        elif cond == "confused": matched = enemy_volatiles.get("confused", False)
        elif cond == "trapped": matched = enemy_volatiles.get("trapped", False)
        elif cond == "flinching": matched = enemy_volatiles.get("flinching", False)
        elif cond == "flinch_confuse_trap": matched = enemy_volatiles.get("confused", False) or enemy_volatiles.get("trapped", False) or enemy_volatiles.get("flinching", False)
        elif cond == "target_rebuff_lowered": matched = enemy_rebuffs.get(move_type, 0) < 0
        elif cond == "super_effective": matched = is_se
        elif "zone" in cond:
            zname = cond.replace("_zone", "").capitalize() + " Zone"
            matched = field_zone == zname
        
        count = 1 if matched else 0
    else:
        s = stages.get(stat, 0)
        count = max(0, min(s, 6)) if is_raised else max(0, min(-s, 6))

    mult = 1.0 + count * step
    if cap > 0:
        mult = min(mult, cap)
    return mult

print("Testing Arc Suit N (Almighty Obsidian Night Daze) with 42 debuffs:")
arc_n_rule = {"who": "target", "stat": "all_stats", "direction": "lowered", "stepPer1000": 100, "capPer1000": 5200}
enemy_all_minus_6 = {k: -6 for k in ["atk", "def", "spa", "spd", "spe", "acc", "eva"]}
mult = eval_move_scaling_mock(arc_n_rule, False, "Dark", {}, enemy_all_minus_6, "", "", "", "", {}, {}, 0, 0, 0, False)
print(f"  Arc Suit N max scaling: x{mult:.2f} (Expected: x5.20)")

print("\nTesting Florian & Ogerpon (Lush Ivy Cudgel with Rebuff -3):")
florian_rule = {"who": "user", "stat": "rebuff", "direction": "raised", "stepPer1000": 500}
mult_f = eval_move_scaling_mock(florian_rule, True, "Grass", {}, {}, "", "", "", "", {}, {"Grass": -3}, 0, 0, 0, False)
print(f"  Florian with Rebuff -3: x{mult_f:.2f} (Expected: x2.50)")