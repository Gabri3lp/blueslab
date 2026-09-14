import glob, json, sys
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp_names = {p['name'].strip().lower(): p for p in rules.get('damagePassives', []) if p.get('name')}
mp_names = {p['passiveName'].strip().lower(): p for p in rules.get('masterPassives', []) if p.get('passiveName')}

files = glob.glob('src/BluesLab/wwwroot/data/pairs/*.json')

all_team_damage_skills = {} # name -> { 'sources': set(), 'descriptions': set(), 'in_dp': bool, 'in_mp': bool }

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        p = json.load(f)
    pname = p.get('displayName', '')
    
    def consider(name, desc, src):
        if not name or not desc: return
        nl = name.strip().lower()
        dl = desc.strip().lower()
        
        # Check if it's a team damage boost
        is_team = ('all allied sync pairs' in dl or 'all allies' in dl or 'team' in dl or 'team' in nl)
        is_dmg = any(k in dl for k in ['powers up', 'increases the power', 'more power', 'damage is increased', 'damage from attacks is increased']) or 'moves ↑' in nl or 's-moves ↑' in nl
        if is_team and is_dmg:
            rec = all_team_damage_skills.setdefault(name.strip(), {'sources': set(), 'descriptions': set(), 'in_dp': False, 'in_mp': False})
            rec['sources'].add(f"{pname} ({src})")
            rec['descriptions'].add(desc.strip())
            if nl in dp_names: rec['in_dp'] = True
            if nl in mp_names: rec['in_mp'] = True

    for ps in p.get('passives', []):
        consider(ps.get('name'), ps.get('description'), 'base')
        for cp in ps.get('childPassives', []):
            consider(cp.get('name'), cp.get('description'), 'child')
    for v in p.get('variations', []):
        for ps in v.get('passives', []):
            consider(ps.get('name'), ps.get('description'), 'var')
            for cp in ps.get('childPassives', []):
                consider(cp.get('name'), cp.get('description'), 'var child')
    sa = p.get('superAwakeningPassive')
    if sa:
        consider(sa.get('name'), sa.get('description'), 'SA')
    for cell in p.get('grid', []):
        title = cell.get('title', '')
        desc = cell.get('description', '')
        clean = title.split(':')[-1].strip() if ':' in title else title.strip()
        consider(clean, desc, 'grid')

print(f"Total team damage skills found: {len(all_team_damage_skills)}")
missing = [n for n, d in all_team_damage_skills.items() if not d['in_dp'] and not d['in_mp']]
print(f"Missing from rules completely: {len(missing)}")
for n in sorted(missing):
    sample_desc = list(all_team_damage_skills[n]['descriptions'])[0]
    sample_src = list(all_team_damage_skills[n]['sources'])[0]
    print(f"  * {n} | Src: {sample_src}")
    print(f"    Desc: {sample_desc[:90]}")
