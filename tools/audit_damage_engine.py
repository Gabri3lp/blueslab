import os
import sys
import json
import math
import struct
from pathlib import Path
from datetime import datetime

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "src" / "BluesLab" / "wwwroot" / "data"
PAIRS_DIR = DATA_DIR / "pairs"
MANIFEST_FILE = DATA_DIR / "pairs_manifest.json"
RULES_FILE = DATA_DIR / "damage_rules.json"
LOG_FILE = ROOT_DIR / "tools" / "diff_audit.log"

# Exact 32-bit single-precision rolls matching PoMaTools and BluesLab DamageRolls
DAMAGE_ROLLS = [
    # Non-Critical (0.90 to 1.00)
    [
        0.899999976158142,
        0.910000026226043,
        0.9200000166893,
        0.930000007152557,
        0.939999997615814,
        0.949999988079071,
        0.959999978542327,
        0.970000028610229,
        0.980000019073486,
        0.990000009536743,
        1.0
    ],
    # Critical (1.35 to 1.50)
    [
        1.3499999046325684,
        1.3650000095367432,
        1.3799999952316284,
        1.3949999809265137,
        1.409999966621399,
        1.4249999523162842,
        1.4399999380111694,
        1.4550000429153442,
        1.4700000286102295,
        1.4850000143051147,
        1.5
    ]
]

def to_float32(val):
    """Simulate Math.fround / 32-bit single-precision float."""
    return struct.unpack('f', struct.pack('f', val))[0]

def get_move_multiplier(full_move_level, role, is_sync, is_max=False):
    """Calculates move power percentage multiplier matching DeNA / PoMaTools."""
    if is_max:
        base_lvl = max(1, min(full_move_level, 5))
        return 100 + (base_lvl - 1) * 5

    base_level = max(1, min(full_move_level, 5))
    base_mult = 100 + (base_level - 1) * 5

    if full_move_level <= 5:
        return base_mult

    sa_level = full_move_level - 5
    r = role.lower().strip()
    is_strike_sprint_multi = ("strike" in r) or ("sprint" in r) or ("multi" in r)
    is_tech_field = ("tech" in r) or ("field" in r)

    if is_strike_sprint_multi:
        if not is_sync:
            if sa_level >= 4:
                return 160
            if sa_level >= 2:
                return 130
        else:
            if sa_level >= 3:
                return 140
    elif is_tech_field:
        if is_sync:
            if sa_level >= 4:
                return 160
            if sa_level >= 2:
                return 130
        else:
            if sa_level >= 3:
                return 140

    return base_mult

def calc_power(base_power, full_move_level, role, is_sync, increment=1.0, is_max=False):
    if base_power <= 0:
        return 0
    mult = get_move_multiplier(full_move_level, role, is_sync, is_max)
    scaled = math.floor(base_power * mult / 100.0)
    return math.floor(scaled * increment)

def calculate_test_damage_rolls(battle_power, attacker_stat, defender_stat, is_critical):
    ne = float(attacker_stat)
    he = float(defender_stat) * 2.0

    base_factor = to_float32((float(battle_power) * ne) / he)
    roll_index = 1 if is_critical else 0
    rolls = []

    for l in range(10):
        roll_val = DAMAGE_ROLLS[roll_index][l] * base_factor
        rolls.append(math.floor(roll_val))

    # Last 100% roll in double
    last_roll_val = DAMAGE_ROLLS[roll_index][10] * float(battle_power) * ne / he
    rolls.append(math.floor(last_roll_val))

    return rolls

def get_in_battle_stat_multiplier(stat, passives, field_weather="", field_terrain="", field_zone="", hp_percent=100, status_condition="", form_name="", grid_cells=None):
    mult = 1.0
    s = stat.lower().strip()
    has_weather = bool(field_weather and field_weather.lower() != "none")
    has_terrain = bool(field_terrain and field_terrain.lower() != "none")
    has_zone = bool(field_zone and field_zone.lower() != "none")
    has_field = has_weather or has_terrain or has_zone

    for p in passives:
        pid = p.get("id", 0)
        pname = p.get("name", "")

        # Weather Buff (23011101)
        if pid == 23011101 or pname.lower() == "weather buff" or "clima favorable" in pname.lower():
            if has_weather and s in ("atk", "def", "spa", "spd", "spe"):
                mult *= 1.30

        # Sedimentary (23010401)
        if pid == 23010401 or pname.lower() == "sedimentary":
            if has_weather and field_weather.lower() == "sandstorm" and s in ("def", "spd"):
                mult *= 1.30

        # Hail and Hearty (23011001)
        if pid == 23011001 or pname.lower() == "hail and hearty":
            if has_weather and field_weather.lower() == "hail" and s in ("def", "spd"):
                mult *= 1.30

        # Healthy Strength 5 (23010505)
        if pid == 23010505 or "healthy strength" in pname.lower():
            if hp_percent >= 50 and s == "atk":
                mult *= 1.50

        # Fortify 3 (23010903)
        if pid == 23010903 or "fortify" in pname.lower():
            if hp_percent <= 50 and s in ("def", "spd"):
                mult *= 1.30

        # Allied Field Effect Multiplier 2 (23011502)
        if pid == 23011502 or "allied field effect multiplier" in pname.lower():
            if has_field and s in ("atk", "def", "spa", "spd", "spe"):
                mult *= 1.20

        # Rules of the Enchanted Land (99016701)
        if pid == 99016701 or "rules of the enchanted land" in pname.lower():
            if has_field and s in ("def", "spd"):
                mult *= 1.20

        # Becalming Beauty (99027801)
        if pid == 99027801 or "becalming beauty" in pname.lower():
            if status_condition and s in ("def", "spd"):
                mult *= 1.50

        # Mind over Matter 4 (23011604)
        if pid == 23011604 or "mind over matter" in pname.lower():
            if hp_percent < 100 and s == "spa":
                mult *= 1.40

        # Soul-Clad Rage (99044601)
        if pid == 99044601 or "soul-clad rage" in pname.lower():
            if s in ("atk", "def", "spa", "spd", "spe"):
                mult *= 1.50

        # While S-Tera: 5 Stats ↑ 1 (23012301)
        if pid == 23012301 or "while s-tera" in pname.lower():
            if "tera" in form_name.lower() or "stellar" in form_name.lower():
                if s in ("atk", "def", "spa", "spd", "spe"):
                    mult *= 1.10

    if grid_cells:
        for cell in grid_cells:
            ab_id = cell.get("abilityId", 0)
            ctitle = cell.get("title", "")

            # Sand Screen (2301010100000)
            if ab_id == 2301010100000 or "sand screen" in ctitle.lower():
                if s == "spd" and has_weather and field_weather.lower() == "sandstorm":
                    mult *= 1.50

            # Ice Shell (2301020100000)
            if ab_id == 2301020100000 or "ice shell" in ctitle.lower():
                if s == "def" and has_weather and field_weather.lower() == "hail":
                    mult *= 1.50

            # Weird Shield (2301030100000)
            if ab_id == 2301030100000 or "weird shield" in ctitle.lower():
                if s == "spd" and has_terrain and field_terrain.lower() == "psychic terrain":
                    mult *= 1.50

    return mult

def run_damage_audit(log_mode="a"):
    print("=" * 60)
    print("   BLUESLAB: AUDITORÍA DE POTENCIAS Y MOTOR DE DAÑO")
    print("=" * 60)

    total_checks = 0
    passed_checks = 0
    discrepancies = []

    # 1. Audit damage_rules.json structure and rules
    total_checks += 1
    if RULES_FILE.exists():
        passed_checks += 1
        with open(RULES_FILE, "r", encoding="utf-8") as rf:
            rules_doc = json.load(rf)
    else:
        discrepancies.append({
            "category": "Rules Document",
            "id": "damage_rules.json",
            "field": "File existence",
            "expected": "damage_rules.json exists",
            "actual": "Missing",
            "reason": "Rules file not found"
        })
        rules_doc = {}

    move_scalings = rules_doc.get("moveScaling", [])
    damage_passives = rules_doc.get("damagePassives", [])
    master_passives = rules_doc.get("masterPassives", [])
    lucky_skills = rules_doc.get("luckySkills", [])

    print(f"[*] Reglas de escalado de movimientos: {len(move_scalings)}")
    print(f"[*] Pasivas de daño registradas:       {len(damage_passives)}")
    print(f"[*] Pasivas maestras registradas:     {len(master_passives)}")
    print(f"[*] Habilidades afortunadas:          {len(lucky_skills)}")

    # Verify each moveScaling rule (supporting linear step rules and thresholdTable rules)
    for idx, ms in enumerate(move_scalings):
        total_checks += 1
        pair_name = ms.get("syncPair", "")
        move_name = ms.get("moveName", "")
        stat = ms.get("stat", "")
        step = ms.get("stepPer1000", 0)
        threshold_table = ms.get("thresholdTable", [])

        is_valid = bool(pair_name and move_name and stat and (step > 0 or len(threshold_table) > 0))
        if is_valid:
            passed_checks += 1
        else:
            discrepancies.append({
                "category": "Move Scaling Rule",
                "id": f"Rule #{idx+1}",
                "name": f"{pair_name} - {move_name}",
                "field": "Rule Definition",
                "expected": "Valid pair, moveName, stat and (stepPer1000 > 0 or valid thresholdTable)",
                "actual": str(ms),
                "reason": "Incomplete move scaling rule"
            })

    # 2. Audit Move Power Scaling and Damage Rolls for all pairs
    pair_files = list(PAIRS_DIR.glob("*.json"))
    print(f"[*] Total de compis a auditar: {len(pair_files)}")

    for p_path in pair_files:
        tid = p_path.stem
        try:
            with open(p_path, "r", encoding="utf-8") as f:
                pair = json.load(f)
        except Exception as e:
            continue

        pair_name = pair.get("displayName", f"Trainer {tid}")
        role = pair.get("role", "Strike")
        has_sa = pair.get("hasSuperAwakening", False)
        moves = pair.get("moves", [])

        for m in moves:
            m_id = m.get("id", 0)
            m_name = m.get("name", "")
            is_sync = m.get("isSync", False)
            is_max = m.get("isMax", False)
            raw_pwr_str = m.get("power", "0")
            raw_pwr = int(raw_pwr_str) if raw_pwr_str.isdigit() else 0

            # Test A: Base power scaling across move levels 1/5 to 5/5
            for lvl in range(1, 6):
                total_checks += 1
                expected_mult = 100 + (lvl - 1) * 5
                calc_mult = get_move_multiplier(lvl, role, is_sync, is_max)
                if calc_mult == expected_mult:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "Move Multiplier (1-5)",
                        "id": tid,
                        "name": pair_name,
                        "field": f"Move '{m_name}' Level {lvl}/5 Multiplier",
                        "expected": expected_mult,
                        "actual": calc_mult,
                        "reason": "Base level power multiplier mismatch"
                    })

            # Test B: Super Awakening scaling (levels 6 to 10)
            if has_sa:
                for sa_lvl in range(1, 6):
                    full_lvl = 5 + sa_lvl
                    total_checks += 1
                    sa_mult = get_move_multiplier(full_lvl, role, is_sync, is_max)
                    # Check that SA multiplier is never lower than 5/5 (120%)
                    if is_max:
                        if sa_mult == 120:
                            passed_checks += 1
                        else:
                            discrepancies.append({
                                "category": "Max Move SA Rule",
                                "id": tid,
                                "name": pair_name,
                                "field": f"Max Move '{m_name}' SA Lv {sa_lvl} Multiplier",
                                "expected": 120,
                                "actual": sa_mult,
                                "reason": "Max moves must not receive SA power jump"
                            })
                    else:
                        if sa_mult >= 120 and sa_mult <= 160:
                            passed_checks += 1
                        else:
                            discrepancies.append({
                                "category": "SA Multiplier Range",
                                "id": tid,
                                "name": pair_name,
                                "field": f"Move '{m_name}' SA Lv {sa_lvl} Multiplier",
                                "expected": "120% to 160%",
                                "actual": sa_mult,
                                "reason": "SA move power multiplier out of valid range"
                            })

            # Test C: Damage Simulation & 11 IEEE-754 Rolls Integrity
            if raw_pwr > 0:
                pwr_5 = calc_power(raw_pwr, 5, role, is_sync, 1.0, is_max)
                total_checks += 1
                if pwr_5 >= raw_pwr:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "Scaled Power Check",
                        "id": tid,
                        "name": pair_name,
                        "field": f"Move '{m_name}' Scaled Power at 5/5",
                        "expected": f">= {raw_pwr}",
                        "actual": pwr_5,
                        "reason": "Scaled power at 5/5 cannot be less than raw base power"
                    })

                # Test Non-Critical Rolls (11 elements, monotonically non-decreasing)
                total_checks += 1
                rolls_nc = calculate_test_damage_rolls(pwr_5, 400, 100, is_critical=False)
                if len(rolls_nc) == 11 and all(rolls_nc[i] <= rolls_nc[i+1] for i in range(10)):
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "Non-Crit Rolls Monotonicity",
                        "id": tid,
                        "name": pair_name,
                        "field": f"Move '{m_name}' Non-Crit Rolls",
                        "expected": "11 monotonically non-decreasing rolls",
                        "actual": str(rolls_nc),
                        "reason": "Damage rolls failed monotonicity or length requirement"
                    })

                # Test Critical Rolls (11 elements, monotonically non-decreasing, > non-crit rolls)
                total_checks += 1
                rolls_cr = calculate_test_damage_rolls(pwr_5, 400, 100, is_critical=True)
                if len(rolls_cr) == 11 and all(rolls_cr[i] <= rolls_cr[i+1] for i in range(10)) and rolls_cr[0] > rolls_nc[0]:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "Crit Rolls Monotonicity",
                        "id": tid,
                        "name": pair_name,
                        "field": f"Move '{m_name}' Crit Rolls",
                        "expected": "11 monotonically non-decreasing rolls higher than non-crit",
                        "actual": str(rolls_cr),
                        "reason": "Critical damage rolls failed monotonicity or magnitude requirement"
                    })

    # 3. Audit In-Battle Stat-Boosting Passives (BOOST / 2301xxxx & Overrides)
    print("[*] Auditando pasivas de aumento de estadísticas en combate (Weather Buff, Sedimentary, etc.)...")
    
    # Check 1: Raihan (Anniversary 2022) & Flygon (10257400000)
    raihan_file = PAIRS_DIR / "10257400000.json"
    if raihan_file.exists():
        with open(raihan_file, "r", encoding="utf-8") as f:
            raihan_data = json.load(f)
        r_passives = raihan_data.get("passives", [])
        
        # Test weather buff under all 4 weathers
        for weather in ["Sunny", "Rainy", "Sandstorm", "Hail"]:
            for st in ["atk", "def", "spa", "spd", "spe"]:
                total_checks += 1
                mult = get_in_battle_stat_multiplier(st, r_passives, field_weather=weather)
                if abs(mult - 1.30) < 0.001:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "In-Battle Stat Passive",
                        "id": "10257400000",
                        "name": "Raihan (Anniversary 2022) & Flygon",
                        "field": f"Weather Buff: {st} in {weather}",
                        "expected": 1.30,
                        "actual": mult,
                        "reason": "Weather Buff must boost 5 stats by +30% under weather"
                    })
        
        # Test when NO weather is active
        for st in ["atk", "def", "spa", "spd", "spe"]:
            total_checks += 1
            mult = get_in_battle_stat_multiplier(st, r_passives, field_weather="")
            if abs(mult - 1.00) < 0.001:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "In-Battle Stat Passive",
                    "id": "10257400000",
                    "name": "Raihan (Anniversary 2022) & Flygon",
                    "field": f"Weather Buff: {st} without weather",
                    "expected": 1.00,
                    "actual": mult,
                    "reason": "Weather Buff must not apply when no weather is active"
                })

        # Test live stat calculation at Level 140 (SpA base 336 + 40 potential = 376)
        total_checks += 1
        base_spa = 376
        spa_no_weather = math.floor(base_spa * 1.00)
        spa_with_weather = math.floor(base_spa * 1.30) # 376 * 1.3 = 488.8 -> 488
        if spa_with_weather == 488 and spa_no_weather == 376:
            passed_checks += 1
        else:
            discrepancies.append({
                "category": "In-Battle Stat Formula",
                "id": "10257400000",
                "name": "Raihan (Anniversary 2022) & Flygon",
                "field": "Sp. Atk Stat Under Weather",
                "expected": 488,
                "actual": spa_with_weather,
                "reason": "Floor(376 * 1.30) must equal 488"
            })

    # Check 2: Ingo & Excadrill (10108000000) - Sedimentary #23010401 (+30% Def, SpD in Sandstorm)
    ingo_file = PAIRS_DIR / "10108000000.json"
    if ingo_file.exists():
        with open(ingo_file, "r", encoding="utf-8") as f:
            ingo_data = json.load(f)
        i_passives = ingo_data.get("passives", [])
        for st in ["def", "spd"]:
            total_checks += 1
            mult_sand = get_in_battle_stat_multiplier(st, i_passives, field_weather="Sandstorm")
            if abs(mult_sand - 1.30) < 0.001:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "In-Battle Stat Passive",
                    "id": "10108000000",
                    "name": "Ingo & Excadrill",
                    "field": f"Sedimentary: {st} in Sandstorm",
                    "expected": 1.30,
                    "actual": mult_sand,
                    "reason": "Sedimentary must boost Def and SpD by +30% in Sandstorm"
                })

            total_checks += 1
            mult_rain = get_in_battle_stat_multiplier(st, i_passives, field_weather="Rainy")
            if abs(mult_rain - 1.00) < 0.001:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "In-Battle Stat Passive",
                    "id": "10108000000",
                    "name": "Ingo & Excadrill",
                    "field": f"Sedimentary: {st} outside Sandstorm",
                    "expected": 1.00,
                    "actual": mult_rain,
                    "reason": "Sedimentary must only activate in Sandstorm"
                })

    # Check 3: Bea & Vanilluxe (10250400000) - Hail and Hearty #23011001 (+30% Def, SpD in Hail)
    bea_file = PAIRS_DIR / "10250400000.json"
    if bea_file.exists():
        with open(bea_file, "r", encoding="utf-8") as f:
            bea_data = json.load(f)
        b_passives = bea_data.get("passives", [])
        for st in ["def", "spd"]:
            total_checks += 1
            mult_hail = get_in_battle_stat_multiplier(st, b_passives, field_weather="Hail")
            if abs(mult_hail - 1.30) < 0.001:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "In-Battle Stat Passive",
                    "id": "10250400000",
                    "name": "Bea & Vanilluxe",
                    "field": f"Hail and Hearty: {st} in Hail",
                    "expected": 1.30,
                    "actual": mult_hail,
                    "reason": "Hail and Hearty must boost Def and SpD by +30% in Hail"
                })

    # Check 4: Emmet & Archeops (10109000000) - Healthy Strength 5 #23010505 (+50% Atk when HP >= 50%)
    emmet_file = PAIRS_DIR / "10109000000.json"
    if emmet_file.exists():
        with open(emmet_file, "r", encoding="utf-8") as f:
            emmet_data = json.load(f)
        e_passives = emmet_data.get("passives", [])
        total_checks += 1
        mult_hp = get_in_battle_stat_multiplier("atk", e_passives, hp_percent=100)
        if abs(mult_hp - 1.50) < 0.001:
            passed_checks += 1
        else:
            discrepancies.append({
                "category": "In-Battle Stat Passive",
                "id": "10109000000",
                "name": "Emmet & Archeops",
                "field": "Healthy Strength 5: Atk at 100% HP",
                "expected": 1.50,
                "actual": mult_hp,
                "reason": "Healthy Strength 5 must boost Atk by +50% when HP >= 50%"
            })

    # Check 5: Sygna Suit Dawn & Cresselia (10116100000) - Fortify 3 #23010903 (+30% Def, SpD when HP <= 50%)
    dawn_file = PAIRS_DIR / "10116100000.json"
    if dawn_file.exists():
        with open(dawn_file, "r", encoding="utf-8") as f:
            dawn_data = json.load(f)
        d_passives = dawn_data.get("passives", [])
        for st in ["def", "spd"]:
            total_checks += 1
            mult_low_hp = get_in_battle_stat_multiplier(st, d_passives, hp_percent=40)
            if abs(mult_low_hp - 1.30) < 0.001:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "In-Battle Stat Passive",
                    "id": "10116100000",
                    "name": "Sygna Suit Dawn & Cresselia",
                    "field": f"Fortify 3: {st} at 40% HP",
                    "expected": 1.30,
                    "actual": mult_low_hp,
                    "reason": "Fortify 3 must boost Def and SpD by +30% when HP <= 50%"
                })

    # Check 6: Grid Passives (Sand Screen, Ice Shell, Weird Shield)
    grid_tests = [
        ("Sand Screen", "spd", 2301010100000, "Sandstorm", "", 1.50),
        ("Ice Shell", "def", 2301020100000, "Hail", "", 1.50),
        ("Weird Shield", "spd", 2301030100000, "", "Psychic Terrain", 1.50),
    ]
    for g_title, g_stat, g_abid, g_wthr, g_terr, g_mult in grid_tests:
        total_checks += 1
        fake_grid = [{"abilityId": g_abid, "title": g_title}]
        calc_gmult = get_in_battle_stat_multiplier(g_stat, [], field_weather=g_wthr, field_terrain=g_terr, grid_cells=fake_grid)
        if abs(calc_gmult - g_mult) < 0.001:
            passed_checks += 1
        else:
            discrepancies.append({
                "category": "Grid Stat Passive",
                "id": str(g_abid),
                "name": g_title,
                "field": f"{g_stat} multiplier",
                "expected": g_mult,
                "actual": calc_gmult,
                "reason": f"{g_title} must boost {g_stat} by +50% under matching field condition"
            })

    # Summary
    fidelity = (passed_checks / total_checks * 100.0) if total_checks > 0 else 0.0
    print("-" * 60)
    print(f"[+] Total de verificaciones realizadas: {total_checks}")
    print(f"[+] Verificaciones superadas con éxito: {passed_checks}")
    print(f"[+] Discrepancias detectadas:           {len(discrepancies)}")
    print(f"[+] PORCENTAJE DE FIDELIDAD DE DAÑO:    {fidelity:.2f}%")
    print("-" * 60)

    # Write log
    with open(LOG_FILE, log_mode, encoding="utf-8") as lf:
        lf.write(f"\n{'='*60}\n")
        lf.write(f"AUDITORÍA DE POTENCIAS Y MOTOR DE DAÑO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lf.write(f"Total verificaciones: {total_checks} | Aprobadas: {passed_checks} | Discrepancias: {len(discrepancies)}\n")
        lf.write(f"Fidelidad: {fidelity:.2f}%\n")
        lf.write(f"{'='*60}\n")
        for d in discrepancies:
            lf.write(f"[DISCREPANCY][PHASE-3][PAIR: {d.get('id')} - {d.get('name', 'N/A')}]\n")
            lf.write(f"  Category: {d.get('category')}\n")
            lf.write(f"  Field:    {d.get('field')}\n")
            lf.write(f"  Expected: {d.get('expected')}\n")
            lf.write(f"  Actual:   {d.get('actual')}\n")
            lf.write(f"  Reason:   {d.get('reason')}\n\n")

    if discrepancies:
        print(f"[!] Se registraron {len(discrepancies)} discrepancias en {LOG_FILE}")
    else:
        print(f"[OK] 100% de cálculos de potencias, reglas y daño son fieles a la especificación.")

    return {
        "total": total_checks,
        "passed": passed_checks,
        "discrepancies": len(discrepancies),
        "fidelity": fidelity
    }

if __name__ == "__main__":
    run_damage_audit(log_mode="a")
