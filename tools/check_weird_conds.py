import json, sys
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp = rules.get('damagePassives', [])

weird_conds = {'370', '506', '58', '629', '63', '89', 'cate_004', 'move_slot_move_004', 'move_slot_move_032', 'move_slot_move_16', 'tags_recoil', 'fighting_zone'}

for p in dp:
    found = []
    for cg in p.get('conditions', []):
        for c in cg:
            if c.strip().lower() in weird_conds:
                found.append(c)
    if found:
        print(f"{p.get('name')}: conds={p.get('conditions')} | mech={p.get('mechanism')} | type={p.get('type')}")
    for sp in p.get('sub_passives', []):
        sfound = []
        for cg in sp.get('conditions', []):
            for c in cg:
                if c.strip().lower() in weird_conds:
                    sfound.append(c)
        if sfound:
            print(f"  [SUB] {sp.get('name')} of {p.get('name')}: conds={sp.get('conditions')} | mech={sp.get('mechanism')}")
