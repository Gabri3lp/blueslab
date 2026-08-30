import json, math

wally = json.loads(open("src/BluesLab/wwwroot/data/pairs/10128100000.json", encoding="utf-8").read())
stats = wally["stats"] # {"hp": [92, 167, 239, 525, 585, 645, 825], ...}

# Breakpoint levels in datamine / PoMaTools:
# [1, 30, 45, 100, 120, 140, 200]
bp = [1, 30, 45, 100, 120, 140, 200]

def calc_base_stat(stat_array, level):
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
    return stat_array[n] + math.floor(l * (stat_array[e] - stat_array[n]) / u)

print("Wally Base HP across levels:")
for lvl in [1, 30, 45, 100, 120, 130, 140, 150, 200]:
    hp_val = calc_base_stat(stats["hp"], lvl)
    print(f"  Lv. {lvl}: HP = {hp_val}")