import glob, json, sys
sys.stdout.reconfigure(encoding='utf-8')

files = glob.glob('src/BluesLab/wwwroot/data/pairs/*.json')

team_passives = {}

team_keywords = [
    'all allied sync pairs', 'all allies', 'team', 'allies',
    'powers up the moves of all', 'powers up the sync move of all',
    'powers up the physical attack moves of all', 'powers up the special attack moves of all'
]

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        p = json.load(f)
    pname = p.get('displayName', '')
    
    def check(name, desc, src):
        if not name or not desc: return
        dl = desc.lower()
        if any(k in dl for k in ['powers up', 'increases the power', 'boosts the power', 'damage is increased', 'more damage']) and any(tk in dl for tk in ['allied sync pairs', 'allies', 'team']):
            rec = team_passives.setdefault(name, {'descs': set(), 'sources': set()})
            rec['descs'].add(desc)
            rec['sources'].add(f"{pname} ({src})")

    for ps in p.get('passives', []):
        check(ps.get('name'), ps.get('description'), 'base')
        for cp in ps.get('childPassives', []):
            check(cp.get('name'), cp.get('description'), f'child of {ps.get("name")}')

    for v in p.get('variations', []):
        for ps in v.get('passives', []):
            check(ps.get('name'), ps.get('description'), 'variation')
            for cp in ps.get('childPassives', []):
                check(cp.get('name'), cp.get('description'), 'variation child')

    sa = p.get('superAwakeningPassive')
    if sa:
        check(sa.get('name'), sa.get('description'), 'SA')

    for cell in p.get('grid', []):
        title = cell.get('title', '')
        desc = cell.get('description', '')
        clean = title.split(':')[-1].strip() if ':' in title else title.strip()
        check(clean, desc, 'grid')

print(f"Total distinct team damage passives found: {len(team_passives)}")
for name, info in sorted(team_passives.items()):
    descs = list(info['descs'])
    print(f"=== {name} ===")
    print(f"  Sources: {list(info['sources'])[:3]}")
    print(f"  Desc: {descs[0] if descs else ''}")
