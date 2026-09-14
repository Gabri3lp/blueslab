import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp = rules.get('damagePassives', [])

weather_types = ['sunny', 'rain', 'rainy', 'sandstorm', 'hail']
terrain_types = ['electric_terrain', 'grassy_terrain', 'psychic_terrain']
zones = ['normal_zone', 'fire_zone', 'water_zone', 'electric_zone', 'grass_zone', 'ice_zone', 'fighting_zone', 'poison_zone', 'ground_zone', 'flying_zone', 'psychic_zone', 'bug_zone', 'rock_zone', 'ghost_zone', 'dragon_zone', 'dark_zone', 'steel_zone', 'fairy_zone']

print(f"Total damage passives: {len(dp)}")

mismatches = []

def check_mismatch(p, parent_name=None):
    name = p.get('name', '')
    conds = p.get('conditions', [])
    flat_conds = [c.lower() for g in conds for c in g]
    
    # Check weather
    for w in ['sun', 'rain', 'sandstorm', 'hail']:
        if w in name.lower() and not any(other in name.lower() for other in ['brain', 'drain', 'rainbow']):
            # check if expected weather matches condition
            exp = 'sunny' if w == 'sun' else ('rain' if w == 'rain' else w)
            # if has weather condition that contradicts
            for c in flat_conds:
                if c in weather_types and not c.startswith(exp):
                    mismatches.append((parent_name or name, name, flat_conds, f"Expected {exp}, found {c}"))
                    
    # Check zone
    for z in zones:
        z_short = z.replace('_zone', '')
        if f"{z_short} zone" in name.lower():
            for c in flat_conds:
                if c.endswith('_zone') and c != z:
                    mismatches.append((parent_name or name, name, flat_conds, f"Expected {z}, found {c}"))

    # Check terrain
    for t in terrain_types:
        t_short = t.replace('_terrain', '')
        if f"{t_short} terrain" in name.lower():
            for c in flat_conds:
                if c.endswith('_terrain') and c != t:
                    mismatches.append((parent_name or name, name, flat_conds, f"Expected {t}, found {c}"))

for p in dp:
    check_mismatch(p)
    for sp in p.get('sub_passives', []):
        check_mismatch(sp, parent_name=p.get('name'))

print(f"Total condition mismatches detected: {len(mismatches)}")
for parent, name, conds, reason in mismatches:
    print(f" * [{parent}] {name} -> {conds} : {reason}")
