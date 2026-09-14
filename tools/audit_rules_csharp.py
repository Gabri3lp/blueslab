import json, sys
sys.stdout.reconfigure(encoding='utf-8')

rules = json.load(open('src/BluesLab/wwwroot/data/damage_rules.json', encoding='utf-8'))
dp = rules.get('damagePassives', [])

supported_mechanisms = {
    'user_stat_raised', 'target_stat_lowered', 'stat_is_raised', 'stat_is_lowered',
    'stat_not_raised', 'stat_raised_30pct', 'gauge_cost_boost', 'mode_swing',
    'ice_plow', 'flat_boost', 'hp_scaling'
}

known_conds_in_csharp = {
    'sunny', 'rain', 'rainy', 'sandstorm', 'hail', 'no_weather', 'any_weather',
    'electric_terrain', 'grassy_terrain', 'psychic_terrain', 'any_terrain',
    'fairy_zone', 'dragon_zone', 'dark_zone', 'ghost_zone', 'flying_zone',
    'grass_zone', 'fire_zone', 'ground_zone', 'rock_zone', 'steel_zone',
    'electric_zone', 'poison_zone', 'normal_zone', 'fighting_zone', 'ice_zone', 'bug_zone', 'water_zone', 'psychic_zone',
    'any_weather_terrain_zone', 'burned', 'paralyzed', 'poisoned', 'frozen', 'asleep',
    'any_status', 'any_condition', 'confused', 'trapped', 'flinching', 'flinch_confuse_trap',
    'critical', 'super_effective', 'super_efective', 'has_rebuff', 'rebuff_lowered', 'target_rebuff',
    'user_rebuff', 'user_rebuff_raised', 'user_rebuff_lowered', 'hp_full', 'hp_low', 'hp_reduced',
    'hp_half_more', 'hp_above_half', 'hp_half_or_more', 'hp_half_less', 'target_hp_low', 'target_hp_half_less',
    'damage_field', 'any_damage_field', 'target_damage_field', 'user_damage_field',
    'field_fild_001', 'move_gauge_accel', 'theme_thm', 'theme_thmd_2', 'theme_thmp_2', 'theme_thms_2',
    'theme_thms_4', 'theme_thmd_5', 'theme_thmp_5', 'theme_thms_5', 'theme_thms_7', 'theme_thmd_9',
    'theme_thmp_9', 'theme_thmd_20', 'damage_field_dmfd_8', 'damage_field_dmfd_13',
    'damage_field_dmfd_16', 'damage_field_dmfd_17', 'circle_active', 'battle_circle',
    'battle_circle_active', 'any_circle', 'physical_circle', 'special_circle',
    'physical_damage_reduction', 'phys_dmg_red', 'physical_reduction',
    'special_damage_reduction', 'spec_dmg_red', 'special_reduction',
    'damage_reduction', 'any_damage_reduction', 'physical_break', 'phys_break',
    'special_break', 'spec_break', 'has_break', 'any_break', 'only_one_alive',
    'berry', 'berry_active', 'first_sync', 'all_stats_not_high', 'any_stat_in_low',
    'target_all_stats_not_high', 'target_any_stat_in_low'
}

# Also handle type_*
def is_known_cond(c):
    c = c.lower().strip()
    if c in known_conds_in_csharp: return True
    if c.startswith('type_'): return True
    if c.endswith('_zone'): return True
    if c.endswith('_circle'): return True
    if c.endswith('_damage_field'): return True
    return False

issues = []

for p in dp:
    name = p.get('name')
    subs = p.get('sub_passives', [])
    
    if subs:
        for sp in subs:
            m = sp.get('mechanism')
            if m not in supported_mechanisms:
                issues.append(f"Sub-passive '{sp.get('name')}' of '{name}' has unsupported mechanism '{m}' (val={sp.get('value')})")
            for cg in sp.get('conditions', []):
                for c in cg:
                    if not is_known_cond(c):
                        issues.append(f"Sub-passive '{sp.get('name')}' of '{name}' has unhandled condition '{c}'")
    else:
        m = p.get('mechanism')
        val = p.get('value', 0)
        ptype = p.get('type')
        if not m:
            if ptype == 'powerup' or val > 0:
                issues.append(f"Passive '{name}' (type={ptype}, val={val}) has no mechanism!")
            elif ptype == 'reducer':
                # DR passives
                pass
        elif m not in supported_mechanisms:
            issues.append(f"Passive '{name}' has unsupported mechanism '{m}' (val={val})")
            
        for cg in p.get('conditions', []):
            for c in cg:
                if not is_known_cond(c):
                    issues.append(f"Passive '{name}' has unhandled condition '{c}'")

print(f"Total issues found in rules: {len(issues)}")
for iss in issues:
    print(" -", iss)
