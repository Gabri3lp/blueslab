import json, sys
sys.stdout.reconfigure(encoding='utf-8')
rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp_names = {p.get('name'): p for p in rules.get('damagePassives', [])}
mp_names = {p.get('passiveName'): p for p in rules.get('masterPassives', [])}

check_list = [
    'The Shining Beauty', 'The Verdant Virtuoso', 'The Will to Protect',
    'Vigorous Splashing', 'Traveler with a Thing for Photography',
    'Unova’s Gentle Hero', 'Unova’s Hotblooded Girl', 'Team Poison Moves ↑ 2',
    'Team Water Moves ↑ 2', 'Team Dragon Moves ↑ 2'
]

for name in check_list:
    p = dp_names.get(name)
    m = mp_names.get(name)
    if p:
        print(f"FOUND DP: {name} -> type={p.get('type')}, affects={p.get('affects')}, mech={p.get('mechanism')}, subs={len(p.get('sub_passives', []))}")
        for sp in p.get('sub_passives', []):
            print(f"   sub: {sp.get('name')} -> affects={sp.get('affects')}, mech={sp.get('mechanism')}, val={sp.get('value')}, conds={sp.get('conditions')}")
    elif m:
        print(f"FOUND MP: {name} -> theme={m.get('theme')}, cat={m.get('category')}, base={m.get('basePowerUpPct')}, max={m.get('maxPowerUpPct')}")
    else:
        print(f"MISSING: {name}")
