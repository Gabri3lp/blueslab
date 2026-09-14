import glob, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp_names = {p['name'].strip().lower(): p for p in rules.get('damagePassives', []) if p.get('name')}
mp_names = {p['passiveName'].strip().lower(): p for p in rules.get('masterPassives', []) if p.get('passiveName')}

files = glob.glob('src/BluesLab/wwwroot/data/pairs/*.json')

damage_keywords = [
    r'powers up the (user’s|user\'s)?\s*(moves|physical attack moves|special attack moves|sync move|max move|moves and sync move)',
    r'increases the power of the (user’s|user\'s)?\s*(moves|attack moves|sync move|max move)',
    r'the more the (user’s|target’s|target\'s|user\'s)?\s*\w+\s*is (raised|lowered), the more it powers up',
    r'powers up the moves of all allied sync pairs',
    r'powers up the sync moves of all allied sync pairs'
]

unhandled_damage_passives = {}

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        p = json.load(f)
    pname = p.get('displayName', '')
    
    def test_p(name, desc, src, pid=None):
        if not name or not desc: return
        nl = name.strip().lower()
        if nl in dp_names or nl in mp_names: return
        
        # Test if it actually powers up moves
        for pat in damage_keywords:
            if re.search(pat, desc, re.IGNORECASE):
                rec = unhandled_damage_passives.setdefault(name.strip(), {'sources': set(), 'descs': set(), 'id': pid})
                rec['sources'].add(f"{pname} ({src})")
                rec['descs'].add(desc.strip())
                break

    for ps in p.get('passives', []):
        test_p(ps.get('name'), ps.get('description'), 'base', ps.get('id'))
        for cp in ps.get('childPassives', []):
            test_p(cp.get('name'), cp.get('description'), 'child', cp.get('id'))
    for v in p.get('variations', []):
        for ps in v.get('passives', []):
            test_p(ps.get('name'), ps.get('description'), 'var', ps.get('id'))
            for cp in ps.get('childPassives', []):
                test_p(cp.get('name'), cp.get('description'), 'var child', cp.get('id'))
    sa = p.get('superAwakeningPassive')
    if sa:
        test_p(sa.get('name'), sa.get('description'), 'SA', sa.get('id'))
    for cell in p.get('grid', []):
        title = cell.get('title', '')
        desc = cell.get('description', '')
        clean = title.split(':')[-1].strip() if ':' in title else title.strip()
        test_p(clean, desc, 'grid')

print(f"Total unhandled genuine damage passives: {len(unhandled_damage_passives)}")
for name, data in sorted(unhandled_damage_passives.items()):
    desc = list(data['descs'])[0]
    src = list(data['sources'])[0]
    print(f" * {name} (ID: {data['id']}) | Src: {src}")
    print(f"   Desc: {desc[:100]}")
