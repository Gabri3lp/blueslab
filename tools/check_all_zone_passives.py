import json, sys
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp = rules.get('damagePassives', [])

for p in dp:
    name = p.get('name', '')
    if 'zone' in name.lower():
        print(f"PASSIVE: {name} -> conds={p.get('conditions')} mech={p.get('mechanism')} val={p.get('value')} affects={p.get('affects')}")
    for sp in p.get('sub_passives', []):
        sname = sp.get('name', '')
        if 'zone' in sname.lower():
            print(f"  [SUB of {name}] {sname} -> conds={sp.get('conditions')} mech={sp.get('mechanism')} val={sp.get('value')} affects={sp.get('affects')}")
