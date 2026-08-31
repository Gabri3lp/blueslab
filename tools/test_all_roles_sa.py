import math

def calc_poma_move_power(raw_power, move_level, role_name, is_sync, is_tech_ex=False):
    # Role bitmasks in PoMaTools:
    # Strike: 1, Support: 2, Tech: 4, Sprint: 8, Field: 16
    r = role_name.lower()
    if "strike" in r: role_bit = 1
    elif "support" in r: role_bit = 2
    elif "tech" in r: role_bit = 4
    elif "sprint" in r: role_bit = 8
    elif "field" in r: role_bit = 16
    else: role_bit = 0

    base_mult = 100 + 5 * (min(move_level, 5) - 1)
    e = [base_mult, base_mult] # [regular, sync]

    if move_level > 5:
        if (9 & role_bit): # Strike (1) or Sprint (8)
            if move_level > 6: e[0] += 10
            if move_level > 7: e[1] += 20
            if move_level > 8: e[0] += 30
        elif (20 & role_bit): # Tech (4) or Field (16)
            if move_level > 6: e[1] += 10
            if move_level > 7: e[0] += 20
            if move_level > 8: e[1] += 30

    mult = e[1] if is_sync else e[0]
    power = math.floor(raw_power * mult / 100)
    if is_sync and is_tech_ex:
        power = math.floor(power * 1.5)
    return power, mult

print("=== Strike Move Power (Base 100) across Move Levels 1..10 ===")
for ml in range(1, 11):
    reg_pwr, reg_m = calc_poma_move_power(100, ml, "Strike", False)
    sync_pwr, sync_m = calc_poma_move_power(300, ml, "Strike", True)
    print(f"  Level {ml:2d}/5: Regular = {reg_pwr} ({reg_m}%), Sync = {sync_pwr} ({sync_m}%)")

print("\n=== Tech Move Power (Base 100) across Move Levels 1..10 ===")
for ml in range(1, 11):
    reg_pwr, reg_m = calc_poma_move_power(100, ml, "Tech", False)
    sync_pwr, sync_m = calc_poma_move_power(300, ml, "Tech", True)
    print(f"  Level {ml:2d}/5: Regular = {reg_pwr} ({reg_m}%), Sync = {sync_pwr} ({sync_m}%)")