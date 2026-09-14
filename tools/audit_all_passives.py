import glob, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
rule_dp = {p['name'].strip().lower(): p for p in rules.get('damagePassives', []) if p.get('name')}
rule_mp = {p['passiveName'].strip().lower(): p for p in rules.get('masterPassives', []) if p.get('passiveName')}
rule_ls = {p['name'].strip().lower(): p for p in rules.get('luckySkills', []) if p.get('name')}

files = glob.glob('src/BluesLab/wwwroot/data/pairs/*.json')

damage_keywords = [
    'powers up', 'increases the power', 'more power', 'damage is increased', 
    'damage from attacks is increased', 'boosts the power', 'power of moves', 
    'power of sync move', 'power of max moves', 'reduces damage', 'damage is reduced',
    'power is doubled', 'doubles the power', 'reduces the damage', 'damage reduction'
]

damage_passives_found = {} # name -> {ids, descriptions, sources, in_rules, rule}

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        p = json.load(f)
    pname = p.get('displayName', '')
    
    def check_p(name, desc, src, pid=None):
        if not name or not desc: return
        n_low = name.strip().lower()
        d_low = desc.strip().lower()
        is_dmg = any(k in d_low for k in damage_keywords) or any(k in n_low for k in ['pride', 'spirit', 'flag bearer', 'teamwork', ' myth', 'strike', 'power reserves', 'super powered', 'haymaker', 'inertia', 'cakewalk', 'smart cookie'])
        if is_dmg:
            rec = damage_passives_found.setdefault(name.strip(), {'ids': set(), 'descriptions': set(), 'sources': set(), 'in_rules': False, 'rule': None})
            if pid: rec['ids'].add(pid)
            rec['descriptions'].add(desc.strip())
            rec['sources'].add(src)
            if n_low in rule_dp:
                rec['in_rules'] = True
                rec['rule'] = rule_dp[n_low]
            elif n_low in rule_mp:
                rec['in_rules'] = True
                rec['rule'] = rule_mp[n_low]

    for ps in p.get('passives', []):
        check_p(ps.get('name'), ps.get('description'), f'{pname} (base)', ps.get('id'))
        for cp in ps.get('childPassives', []):
            check_p(cp.get('name'), cp.get('description'), f'{pname} (child of {ps.get("name")})', cp.get('id'))

    for v in p.get('variations', []):
        for ps in v.get('passives', []):
            check_p(ps.get('name'), ps.get('description'), f'{pname} (variation)', ps.get('id'))
            for cp in ps.get('childPassives', []):
                check_p(cp.get('name'), cp.get('description'), f'{pname} (variation child)', cp.get('id'))

    sa = p.get('superAwakeningPassive')
    if sa and sa.get('name'):
        check_p(sa.get('name'), sa.get('description'), f'{pname} (SA)', sa.get('id'))

    for cell in p.get('grid', []):
        title = cell.get('title', '')
        desc = cell.get('description', '')
        clean = title.split(':')[-1].strip() if ':' in title else title.strip()
        check_p(clean, desc, f'{pname} (grid)')

print(f'Total damage-related passives found: {len(damage_passives_found)}')
in_rules = [p for name, p in damage_passives_found.items() if p['in_rules']]
not_in_rules = [name for name, p in damage_passives_found.items() if not p['in_rules']]
print(f'In rules: {len(in_rules)}')
print(f'NOT in rules: {len(not_in_rules)}')

# Print samples of NOT in rules
print('\n--- Sample NOT in rules (first 40) ---')
for name in not_in_rules[:40]:
    descs = list(damage_passives_found[name]['descriptions'])
    d = descs[0] if descs else ''
    if len(d) > 80: d = d[:77] + '...'
    print(f'* {name}: {d}')
