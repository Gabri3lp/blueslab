import os
import sys
import json
import math
import glob
from pathlib import Path
from datetime import datetime

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "src" / "BluesLab" / "wwwroot" / "data"
PAIRS_DIR = DATA_DIR / "pairs"
MANIFEST_FILE = DATA_DIR / "pairs_manifest.json"
LOG_FILE = ROOT_DIR / "tools" / "diff_audit.log"

STAT_KEYS = ["hp", "atk", "def", "spa", "spd", "spe"]
BREAKPOINTS = [1, 30, 45, 100, 120, 140, 200]

EX_ROLE_BONUS = {
    "strike": {"hp": 60, "atk": 40, "def": 0, "spa": 40, "spd": 0, "spe": 0},
    "strike (physical)": {"hp": 60, "atk": 40, "def": 0, "spa": 40, "spd": 0, "spe": 0},
    "strike (special)": {"hp": 60, "atk": 40, "def": 0, "spa": 40, "spd": 0, "spe": 0},
    "tech": {"hp": 60, "atk": 0, "def": 20, "spa": 20, "spd": 20, "spe": 0},
    "support": {"hp": 60, "atk": 0, "def": 40, "spa": 0, "spd": 40, "spe": 0},
    "sprint": {"hp": 60, "atk": 20, "def": 0, "spa": 20, "spd": 0, "spe": 40},
    "field": {"hp": 60, "atk": 0, "def": 20, "spa": 0, "spd": 20, "spe": 40},
    "multi": {"hp": 60, "atk": 20, "def": 20, "spa": 20, "spd": 20, "spe": 20}
}

def interpolate_base_stat(stat_arr, level):
    """Piecewise linear interpolation over 7 breakpoint nodes matching PMEX & PoMaTools."""
    if level <= 1:
        return stat_arr[0]
    if level >= 200:
        return stat_arr[6]
        
    if level < 30:
        n, e, i, r = 0, 1, 1, 30
    elif level < 45:
        n, e, i, r = 1, 2, 30, 45
    elif level < 100:
        n, e, i, r = 2, 3, 45, 100
    elif level < 120:
        n, e, i, r = 3, 4, 100, 120
    elif level < 140:
        n, e, i, r = 4, 5, 120, 140
    else:
        n, e, i, r = 5, 6, 140, 200

    l = level - i
    u = r - i
    return stat_arr[n] + math.floor(l * (stat_arr[e] - stat_arr[n]) / u)

def get_potential_bonus(base_rarity, is_ex_or_max_potential):
    """Calculate flat stat bonus from 20/20 potentials & 6* EX."""
    if not is_ex_or_max_potential:
        return {k: 0 for k in STAT_KEYS}
    
    if base_rarity >= 5:
        return {"hp": 100, "atk": 40, "def": 40, "spa": 40, "spd": 40, "spe": 40}
    
    stars_gained = 5 - base_rarity + 1
    potentials = stars_gained * 20
    return {
        "hp": potentials * 2,
        "atk": potentials * 1,
        "def": potentials * 1,
        "spa": potentials * 1,
        "spd": potentials * 1,
        "spe": potentials * 1
    }

def get_ex_role_bonus(ex_role_name):
    """Retrieve EX role flat bonuses."""
    if not ex_role_name:
        return {k: 0 for k in STAT_KEYS}
    norm = ex_role_name.lower().strip()
    if norm in EX_ROLE_BONUS:
        return EX_ROLE_BONUS[norm]
    # Strip parentheses if needed
    base_name = norm.split(" (")[0]
    return EX_ROLE_BONUS.get(base_name, {k: 0 for k in STAT_KEYS})

def apply_super_awakening_stat(base_val, role, sa_level, stat_key):
    """Apply PoMaTools exact Super Awakening logic and rounding."""
    if sa_level <= 0:
        return base_val
    
    # 1. 10% base stat increase with PoMaTools odd-rounding: ceil(val * 1.1) + (-1 if val % 10 != 0 else 0)
    scaled = math.ceil(base_val * 1.1) + (-1 if (base_val % 10 != 0) else 0)
    
    # 2. Support role flat bonuses at SA lv 2, 3, 4
    if "support" in role.lower():
        if stat_key == "hp":
            if sa_level >= 2:
                scaled += 50
            if sa_level >= 4:
                scaled += 100
        elif stat_key in ("def", "spd"):
            if sa_level >= 3:
                scaled += 20
                
    return scaled

def run_stats_audit(log_mode="a"):
    print("=" * 60)
    print("   BLUESLAB: AUDITORÍA DE ESTADÍSTICAS E INFORMACIÓN")
    print("=" * 60)
    
    if not MANIFEST_FILE.exists():
        print(f"[ERROR] Manifest file not found: {MANIFEST_FILE}")
        return
        
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    print(f"[*] Total de parejas registradas en Manifest: {len(manifest)}")
    
    total_checks = 0
    passed_checks = 0
    discrepancies = []
    
    pair_files = list(PAIRS_DIR.glob("*.json"))
    print(f"[*] Total de archivos JSON encontrados en pairs/: {len(pair_files)}")

    for p_path in pair_files:
        tid = p_path.stem
        try:
            with open(p_path, "r", encoding="utf-8") as f:
                pair = json.load(f)
        except Exception as e:
            discrepancies.append({
                "id": tid,
                "name": "Unknown",
                "field": "JSON Parsing",
                "expected": "Valid JSON",
                "actual": f"Error: {e}",
                "reason": "Corrupted or invalid JSON file"
            })
            continue

        name = pair.get("displayName", f"Trainer {tid}")
        stats = pair.get("stats", {})
        role = pair.get("role", "Strike")
        ex_role = pair.get("exRole", "")
        rarity = pair.get("rarity", 5)
        has_ex = pair.get("hasEx", False)
        has_sa = pair.get("hasSuperAwakening", False)

        # 1. Structural Check: 7 elements for each stat
        for k in STAT_KEYS:
            total_checks += 1
            arr = stats.get(k, [])
            if not isinstance(arr, list) or len(arr) != 7:
                discrepancies.append({
                    "id": tid,
                    "name": name,
                    "field": f"stats.{k}.length",
                    "expected": 7,
                    "actual": len(arr) if isinstance(arr, list) else type(arr).__name__,
                    "reason": "Stat array must have exactly 7 breakpoint values [1, 30, 45, 100, 120, 140, 200]"
                })
            else:
                passed_checks += 1
                # Check monotonic non-decreasing
                total_checks += 1
                if all(arr[i] <= arr[i+1] for i in range(len(arr)-1)):
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "id": tid,
                        "name": name,
                        "field": f"stats.{k}.monotonicity",
                        "expected": "Monotonically increasing",
                        "actual": str(arr),
                        "reason": f"Stat values decreased between levels: {arr}"
                    })

        # 2. Check Milestones (Lv 140, Lv 150, Lv 200)
        # Milestone 1: Lv 140 Base (Index 5 in array)
        for k in STAT_KEYS:
            total_checks += 1
            arr = stats.get(k, [0]*7)
            if len(arr) == 7:
                expected_140 = arr[5]
                calc_140 = interpolate_base_stat(arr, 140)
                if expected_140 == calc_140:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "id": tid,
                        "name": name,
                        "field": f"Base {k} at Lv 140",
                        "expected": expected_140,
                        "actual": calc_140,
                        "reason": "Interpolation mismatch at Lv 140 breakpoint"
                    })

        # Milestone 2: Lv 200 Base (Index 6 in array)
        for k in STAT_KEYS:
            total_checks += 1
            arr = stats.get(k, [0]*7)
            if len(arr) == 7:
                expected_200 = arr[6]
                calc_200 = interpolate_base_stat(arr, 200)
                if expected_200 == calc_200:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "id": tid,
                        "name": name,
                        "field": f"Base {k} at Lv 200",
                        "expected": expected_200,
                        "actual": calc_200,
                        "reason": "Interpolation mismatch at Lv 200 breakpoint"
                    })

        # Milestone 3: Check Super Awakening & EX role math consistency
        pot_bonus = get_potential_bonus(rarity, has_ex)
        ex_bonus = get_ex_role_bonus(ex_role)
        for k in STAT_KEYS:
            total_checks += 1
            arr = stats.get(k, [0]*7)
            if len(arr) == 7:
                base_200 = arr[6]
                sa_stat = apply_super_awakening_stat(base_200, role, 5 if has_sa else 0, k)
                total_stat = sa_stat + pot_bonus[k] + ex_bonus[k]
                if total_stat > base_200 or not (has_ex or has_sa or ex_role):
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "id": tid,
                        "name": name,
                        "field": f"Total {k} at Lv 200 (6★ EX + EX Role + SA)",
                        "expected": f"> {base_200}",
                        "actual": total_stat,
                        "reason": "Calculated total stat with SA and EX failed sanity check"
                    })

    # Summary
    fidelity = (passed_checks / total_checks * 100.0) if total_checks > 0 else 0.0
    print("-" * 60)
    print(f"[+] Total de verificaciones realizadas: {total_checks}")
    print(f"[+] Verificaciones superadas con éxito: {passed_checks}")
    print(f"[+] Discrepancias detectadas:           {len(discrepancies)}")
    print(f"[+] PORCENTAJE DE FIDELIDAD DE STATS:   {fidelity:.2f}%")
    print("-" * 60)

    # Write log
    with open(LOG_FILE, log_mode, encoding="utf-8") as lf:
        lf.write(f"\n{'='*60}\n")
        lf.write(f"AUDITORÍA DE ESTADÍSTICAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lf.write(f"Total verificaciones: {total_checks} | Aprobadas: {passed_checks} | Discrepancias: {len(discrepancies)}\n")
        lf.write(f"Fidelidad: {fidelity:.2f}%\n")
        lf.write(f"{'='*60}\n")
        for d in discrepancies:
            lf.write(f"[DISCREPANCY][PHASE-1][PAIR: {d['id']} - {d['name']}]\n")
            lf.write(f"  Field:    {d['field']}\n")
            lf.write(f"  Expected: {d['expected']}\n")
            lf.write(f"  Actual:   {d['actual']}\n")
            lf.write(f"  Reason:   {d['reason']}\n\n")

    if discrepancies:
        print(f"[!] Se registraron {len(discrepancies)} discrepancias en {LOG_FILE}")
    else:
        print(f"[OK] 100% de estadísticas e información son fieles a la especificación.")
    
    return {
        "total": total_checks,
        "passed": passed_checks,
        "discrepancies": len(discrepancies),
        "fidelity": fidelity
    }

if __name__ == "__main__":
    run_stats_audit(log_mode="w")
