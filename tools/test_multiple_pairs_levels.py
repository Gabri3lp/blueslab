import json, math

bp = [1, 30, 45, 100, 120, 140, 200]

def get_stat_at_level(values, level):
    level = max(1, min(200, level))
    for i in range(len(bp)):
        if level == bp[i]:
            return values[i]
        if level < bp[i]:
            if i == 0: return values[0]
            prev_lvl = bp[i-1]
            next_lvl = bp[i]
            prev_val = values[i-1]
            next_val = values[i]
            factor = (level - prev_lvl) / (next_lvl - prev_lvl)
            return math.floor(prev_val + (next_val - prev_val) * factor)
    return values[-1]

# Test Red & Charizard at Lv 140, 150, 200
red = json.loads(open("src/BluesLab/wwwroot/data/pairs/10000000000.json", encoding="utf-8").read())
print("Red & Charizard HP:")
for l in [120, 130, 140, 150, 200]:
    print(f"  Lv. {l}: {get_stat_at_level(red['stats']['hp'], l)}")