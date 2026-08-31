import math

def get_move_multiplier(full_move_level, role, is_sync):
    base_level = max(1, min(full_move_level, 5))
    base_mult = 100 + (base_level - 1) * 5
    if full_move_level <= 5:
        return base_mult

    sa_level = full_move_level - 5
    r = role.lower()
    is_strike_sprint = ("strike" in r) or ("sprint" in r)
    is_tech_field = ("tech" in r) or ("field" in r)

    if is_strike_sprint:
        if not is_sync:
            if sa_level >= 4: return 160
            if sa_level >= 2: return 130
        else:
            if sa_level >= 3: return 140
    elif is_tech_field:
        if is_sync:
            if sa_level >= 4: return 160
            if sa_level >= 2: return 130
        else:
            if sa_level >= 3: return 140

    return base_mult

print("Wally (Tech) Move Power Scaling:")
for lvl in range(1, 11):
    reg = get_move_multiplier(lvl, "Tech", False)
    sync = get_move_multiplier(lvl, "Tech", True)
    print(f"  Lv {lvl:2d}/5: Regular Multiplier = {reg}%, Sync Multiplier = {sync}%")

print("\nRed (Strike) Move Power Scaling:")
for lvl in range(1, 11):
    reg = get_move_multiplier(lvl, "Strike (Special)", False)
    sync = get_move_multiplier(lvl, "Strike (Special)", True)
    print(f"  Lv {lvl:2d}/5: Regular Multiplier = {reg}%, Sync Multiplier = {sync}%")

print("\nBlue (Support) Move Power Scaling:")
for lvl in range(1, 11):
    reg = get_move_multiplier(lvl, "Support", False)
    sync = get_move_multiplier(lvl, "Support", True)
    print(f"  Lv {lvl:2d}/5: Regular Multiplier = {reg}%, Sync Multiplier = {sync}%")