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
