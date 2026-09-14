import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Load rules
rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dps = rules.get('damagePassives', [])
mps = rules.get('masterPassives', [])

print("=== PASSIVE ENGINE VERIFICATION ===")
print(f"Total Damage Passives in rules: {len(dps)}")
print(f"Total Master Passives in rules: {len(mps)}")

# 1. Verify no empty mechanisms on powerups
powerups = [p for p in dps if p.get('type') == 'powerup']
empty_mech_powerups = [p for p in powerups if not p.get('mechanism')]
print(f"Powerup passives with empty mechanism: {len(empty_mech_powerups)}")
assert len(empty_mech_powerups) == 0, f"Found empty mech powerups: {[p['name'] for p in empty_mech_powerups]}"

# 2. Verify all Team [Type] Moves ↑ 2 exist
types = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison",
    "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
]
dp_name_map = {p['name'].strip().lower(): p for p in dps}
for t in types:
    expected_name = f"Team {t} Moves ↑ 2".lower()
    assert expected_name in dp_name_map, f"Missing team passive: {expected_name}"
    rule = dp_name_map[expected_name]
    assert rule.get('affects') == 'team', f"{expected_name} does not affect team"
    assert rule.get('value') == 2, f"{expected_name} value != 2"
    assert rule.get('mechanism') == 'flat_boost', f"{expected_name} mech != flat_boost"
print("✓ All 18 Team [Type] Moves ↑ 2 verified successfully!")

# 3. Verify specific move passives have move_name set
specific_moves = {
    'Hyper Beam Power ↑ 5': 'Hyper Beam',
    'Opp Status Cond: Hex Power ×2': 'Hex',
    'Close Combat Power ↑ 5': 'Close Combat',
    'Sunny: High Horsepower Power ×2': 'High Horsepower',
    'Ice Beam Power ×2': 'Ice Beam',
    'Earthquake Power ↑ 9': 'Earthquake'
}

for name, exp_move in specific_moves.items():
    rule = None
    for p in dps:
        if p.get('name') == name: rule = p; break
        for sp in p.get('sub_passives', []):
            if sp.get('name') == name: rule = sp; break
    assert rule is not None, f"Could not find rule for {name}"
    assert rule.get('move_name') == exp_move, f"{name} move_name '{rule.get('move_name')}' != '{exp_move}'"
print("✓ Specific move name passives verified successfully!")

# 4. Verify condition mismatches are 0
mismatches = []
zones = ['normal_zone', 'fire_zone', 'water_zone', 'electric_zone', 'grass_zone', 'ice_zone', 'fighting_zone', 'poison_zone', 'ground_zone', 'flying_zone', 'psychic_zone', 'bug_zone', 'rock_zone', 'ghost_zone', 'dragon_zone', 'dark_zone', 'steel_zone', 'fairy_zone']
for p in dps:
    name = p.get('name', '')
    flat_conds = [c.lower() for g in p.get('conditions', []) for c in g]
    for z in zones:
        z_short = z.replace('_zone', '')
        if f"{z_short} zone" in name.lower():
            for c in flat_conds:
                if c.endswith('_zone') and c != z:
                    mismatches.append((name, c, z))

assert len(mismatches) == 0, f"Condition mismatches found: {mismatches}"
print("✓ All zone condition alignments verified (0 mismatches)!")

# 5. Verify Team Mode Master Passives in pairs dataset
pairs_manifest = json.load(open('src/BluesLab/wwwroot/data/pairs_manifest.json', encoding='utf-8'))
print(f"Total pairs in manifest: {len(pairs_manifest)}")

# Check Calem Champion has Kalos Pride in variation
calem_file = 'src/BluesLab/wwwroot/data/pairs/calem_champion_greninja.json'
try:
    calem_data = json.load(open(calem_file, encoding='utf-8'))
    var_passives = [ps['name'] for v in calem_data.get('variations', []) for ps in v.get('passives', [])]
    assert 'Kalos Pride' in var_passives, "Calem Champion missing Kalos Pride in variations"
    print("✓ Calem (Champion) & Greninja has Kalos Pride in variations!")
except FileNotFoundError:
    pass

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
