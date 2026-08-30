import math

# Wally at Level 200:
base_json = {"hp": 825, "atk": 388, "def": 259, "spa": 648, "spd": 262, "spe": 314}
pot = {"hp": 100, "atk": 40, "def": 40, "spa": 40, "spd": 40, "spe": 40} # 5* EX
ex_role = {"hp": 60, "atk": 20, "def": 0, "spa": 20, "spd": 0, "spe": 40} # Sprint
mega_mult = {"hp": 1.0, "atk": 1.0, "def": 1.0, "spa": 1.2, "spd": 1.2, "spe": 1.0}
grid = {"hp": 10, "atk": 0, "def": 5, "spa": 10, "spd": 5, "spe": 5}

stats_keys = ["hp", "atk", "def", "spa", "spd", "spe"]

def calc_total(s, json_stat, potential, ex_bonus, form_mult, has_sa, grid_stat):
    base_val = json_stat
    if has_sa:
        base_val = math.ceil(base_val * 1.1) + (-1 if (base_val % 10 != 0) else 0)
    
    raw_base = base_val + potential + ex_bonus
    if abs(form_mult - 1.0) < 0.0001:
        after_mult = raw_base
    else:
        after_mult = math.floor(raw_base * form_mult)
    
    return after_mult + grid_stat

print("Calculated with fixed SA formula:")
for s in stats_keys:
    t = calc_total(s, base_json[s], pot[s], ex_role[s], mega_mult[s], True, grid[s])
    print(f"  {s}: {t}")

print("\nPoMaTools expected:")
print("  hp: 1077, atk: 486, def: 329, spa: 936, spd: 398, spe: 430")