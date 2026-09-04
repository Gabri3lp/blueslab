import json
import os
import glob
import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def clean_poma_text(text):
    if not text:
        return ""
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[ ]{2,}', ' ', text)
    return text.strip()

def evaluate_skill_template(raw_desc, pid):
    if not raw_desc:
        return ""
    
    pid_str = str(pid)
    val = 1
    if pid_str[-1].isdigit() and int(pid_str[-1]) > 0:
        val = int(pid_str[-1])
    
    desc = raw_desc
    desc = desc.replace('{{value}}', str(val))
    desc = desc.replace('{{plus}}', str(val + 1))
    desc = desc.replace('{{chance}}', str(10 * (val + 1)))
    desc = desc.replace('{{heal}}', str(10 * val))
    desc = desc.replace('{{sheal}}', str(20 * val))

    if val == 1:
        desc = desc.replace("1 stat rank(s)", "1 stat rank")
        desc = desc.replace("1 stat ranks", "1 stat rank")
    else:
        desc = desc.replace(f"{val} stat rank(s)", f"{val} stat ranks")
        desc = re.sub(rf'\b{val} stat rank\b', f"{val} stat ranks", desc)

    desc = desc.replace("stat rank(s)", "stat ranks")
    return clean_poma_text(desc)

# Explicit manual overrides for the newest 2025/2026 abilities
MANUAL_GRID_FIXES = {
    "19069801": "Turns the field of play’s zone into a Dark Zone the first time the user’s attack move is successful each battle. (A Dark Zone powers up Dark-type attacks.)",
    "13088005": "Powers up the user’s moves and sync move when the zone is a Dark Zone.",
    "19070001": "Turns the field of play’s zone into a Bug Zone the first time the user’s sync move is used each battle. (A Bug Zone powers up Bug-type attacks.)",
    "19070505": "Turns the field of play’s terrain into Psychic Terrain the first time the user’s sync move is used each battle. Extends the duration of Psychic Terrain when the terrain turns into Psychic Terrain while the user is on the field.",
    "19068703": "Turns the field of play’s zone into a Dragon Zone the first time the user’s sync move is used each battle. (A Dragon Zone powers up Dragon-type attacks.) Extends the duration of the Dragon Zone when the zone turns into a Dragon Zone while the user is on the field.",
    "17096801": "Applies the Supereffective ↑ Next effect to the user the first time its attack move is successful each battle.",
    "17015201": "Prevents all allied sync pairs from being inflicted with status conditions, flinching, becoming confused, or becoming trapped when the zone is a Ghost Zone.",
    "16032003": "Powers up the sync moves of all allied sync pairs when the zone is a Poison Zone.",
    "13024802": "Reduces damage when the user is hit by an attack move while the zone is an Ice Zone.",
    "17098409": "Leaves the target either flinching, confused, or trapped when the user’s Water-type attack move against it is successful.",
    "18131109": "Raises the user’s Attack by 1 stat rank when its Pokémon uses a move.",
    "16031909": "Powers up the user’s sync move when the target’s Defense is lowered.",
    "17093301": "Increases the user’s Physical Moves ↑ Next effect by 3 ranks the first time the remaining MP for its Dark Wish is zero each battle.",
    "19070301": "Restores 1 MP of the user’s Kalos Analysis the first time the remaining MP for that move is zero each battle.",
    "13063401": "Restores 1 MP of the user’s Paldea Analysis the first time the remaining MP for that move is zero each battle.",
    "13063601": "Restores 1 MP of the user’s Sinnoh Solidarity the first time the remaining MP for that move is zero each battle.",
    "15016401": "Reduces the user’s sync move countdown by 1 when it applies Sinnoh Circle (Physical) to the allied field of play.",
    "19069701": "Applies Kalos Circle (Special) to the allied field of play the first time the user’s sync move is used each battle.",
    "19069503": "Extends the duration of the Ice Zone when the zone turns into an Ice Zone while the user is on the field. Extends the duration of Paldea Circle (Special) when Paldea Circle (Special) is applied to the allied field of play.",
    "99052201": "Applies Kalos Circle (Physical) to the allied field of play when the user enters a battle. Extends the duration of Kalos Circle (Physical) when Kalos Circle (Physical) is applied to the allied field of play.",
    "99052101": "Applies Kalos Circle (Special) to the allied field of play when the user enters a battle. Extends the duration of Kalos Circle (Special) when Kalos Circle (Special) is applied to the allied field of play.",
    "99052401": "Reduces the user’s sync move countdown by 1 the first time it enters a battle each battle. Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks the first time the user enters a battle each battle.",
    "17097601": "Increases the user’s Sync Move ↑ Next effect by 10 ranks when an ally on your team faints.",
    "17096409": "Increases the user’s Special Moves ↑ Next effect by 5 ranks after using its sync move.",
    "19070209": "Increases the user’s Special Moves ↑ Next effect by 1 rank after your team’s sync pair uses their sync move.",
    "17095009": "When the user’s move targeting an allied sync pair (excluding field effects) is successful, increases the Physical Moves ↑ Next effect of the allied sync pair affected by the move by 2 ranks.",
    "17096109": "When the user’s move targeting an allied sync pair (excluding field effects) is successful, increases the Special Moves ↑ Next effect of the allied sync pair affected by the move by 2 ranks.",
    "17097209": "When the user’s move targeting an allied sync pair (excluding field effects) is successful, increases the Sync Move ↑ Next effect of the allied sync pair affected by the move by 2 ranks.",
    "17096702": "Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 2 ranks the first time the user’s buddy move is used each battle.",
    "13063501": "Restores 1 MP for the user the first time its Trainer uses a move each battle.",
    "18129802": "Raises the Attack and Sp. Atk of all allied sync pairs by 2 stat ranks when the user enters a battle.",
    "18128809": "Raises one of the user’s following stats by 1 stat rank at random when its attack move is successful while it is asleep: Attack, Defense, Sp. Atk, Sp. Def, Speed, accuracy, or evasiveness.",
    "18129709": "Lowers the target’s Sp. Atk by 2 stat ranks when the user’s Pokémon uses a status move targeting that opponent.",
    "17097503": "Reduces the user’s sync move countdown by 3 the first time its move is successful each battle. Applies the Supereffective ↑ Next effect to all allied sync pairs the first time the user’s move is successful each battle.",
    "17096309": "Increases the user’s Physical Moves ↑ Next effect by 3 ranks when an ally turns the field of play’s terrain into Electric Terrain.",
    "18129309": "Lowers one of the target’s following stats by 2 stat ranks at random when the user’s attack move is successful against a burned opponent: Attack, Defense, Sp. Atk, Sp. Def, Speed, accuracy, or evasiveness. (The same stat is lowered for all opponents.)",
    "17096909": "Increases the user’s Sync Move ↑ Next effect by 3 ranks when its attack move is successful against a burned opponent.",
    "99045701": "Grants all of the following effects the first time the user’s sync move is used each battle: Reduces the user’s sync move countdown by 2. Makes the weather rainy. Turns the field of play’s zone into a Dark Zone. (A Dark Zone powers up Dark-type attacks.)",
    "17096209": "Increases the user’s Physical Moves ↑ Next effect and Special Moves ↑ Next effect by 1 rank when its attack move is successful. Increases the user’s Physical Moves ↑ Next effect and Special Moves ↑ Next effect by 1 rank after using its sync move.",
    "99045901": "Reduces the user’s sync move countdown by 1 when it uses Rain Dance. Extends the duration of rainy weather when the weather turns rainy while the user is on the field.",
    "17097409": "Increases the Special Moves ↑ Next effect of all allied sync pairs by 2 ranks when the user makes the weather rainy.",
    "17096009": "Increases the user’s Special Moves ↑ Next effect by 2 ranks when its move is successful while its team does not have a sync buff.",
    "17095209": "Increases the user’s Physical Moves ↑ Next effect by 2 ranks when the user takes up a counter attacking posture or gets ready to attack.",
    "17095309": "Increases the user’s Physical Moves ↑ Next effect by 3 ranks when the user takes up a counter attacking posture or gets ready to attack.",
    "18129109": "Raises the Defense and Sp. Def of all allied sync pairs by 1 stat rank when the user’s attack move is successful.",
    "19072101": "Turns the field of play’s zone into a Dragon Zone when the user’s move is successful. (A Dragon Zone powers up Dragon-type attacks.) Applies Sinnoh Circle (Special) to the allied field of play when the user’s move is successful.",
    "19072001": "Applies Sinnoh Circle (Special) to the allied field of play the first time the user’s attack move is successful each battle.",
    "19069405": "Extends the duration of Johto Circle (Physical) when Johto Circle (Physical) is applied to the allied field of play. Extends the duration of Johto Circle (Special) when Johto Circle (Special) is applied to the allied field of play.",
    "99052301": "Reduces the user’s sync move countdown by 1 the first time it enters a battle each battle. Increases the user’s Sync Move ↑ Next effect by 3 ranks the first time it enters a battle each battle.",
    "17097701": "Reduces the user’s sync move countdown by 1 the first time its move is successful each battle. Applies the Supereffective ↑ Next effect to all allied sync pairs the first time the user’s move is successful each battle."
}

def resolve_grid_desc(cell_id, title, current_desc, panel_map, ability_map, poma_skills, poma_moves):
    # If there are no tags, keep existing description
    if not re.search(r'\[[^\]]+\]', current_desc):
        return current_desc

    ab_id = panel_map.get(cell_id)
    ab = ability_map.get(ab_id) if ab_id else None
    
    if ab:
        pid = ab.get('passiveId')
        mid = ab.get('moveId')
        pid_str = str(pid) if pid else ""
        mid_str = str(mid) if mid else ""

        # 1. Check manual fixes
        if pid_str in MANUAL_GRID_FIXES:
            return MANUAL_GRID_FIXES[pid_str]
        
        # 2. Check PoMaTools passive skills
        if pid and pid != 0:
            base_pid = str(int(pid_str) // 10) if len(pid_str) > 1 else pid_str
            base_pid0 = pid_str[:-1] + "0" if len(pid_str) > 1 else pid_str

            if pid_str in poma_skills:
                desc = evaluate_skill_template(poma_skills[pid_str].get("DESC", ""), pid_str)
                if desc and not re.search(r'\[[^\]]+\]', desc):
                    return desc
            if base_pid in poma_skills:
                desc = evaluate_skill_template(poma_skills[base_pid].get("DESC", ""), pid_str)
                if desc and not re.search(r'\[[^\]]+\]', desc):
                    return desc
            if base_pid0 in poma_skills:
                desc = evaluate_skill_template(poma_skills[base_pid0].get("DESC", ""), pid_str)
                if desc and not re.search(r'\[[^\]]+\]', desc):
                    return desc

        # 3. Check PoMaTools moves
        if mid and mid != 0 and mid_str in poma_moves:
            desc = clean_poma_text(poma_moves[mid_str].get("DESC", ""))
            if desc and not re.search(r'\[[^\]]+\]', desc):
                return desc

    # 4. Fallback: contextual cleanup of tags
    desc = current_desc
    # Clean standard tags
    desc = re.sub(r'\[Digit:1digit(?: Idx="[^"]*")?\s*\]', '1', desc)
    desc = re.sub(r'\[Digit:2digits(?: Idx="[^"]*")?\s*\]', '20', desc)
    desc = re.sub(r'\[EN:Qty(?: Ref="[^"]*")? S="([^"]*)" P="([^"]*)"\s*\]', r'\2', desc)
    desc = re.sub(r'\[Name:MoveId Idx="(\d+)"\s*\]', lambda m: poma_moves.get(m.group(1), {}).get("NAME", "move"), desc)
    
    # Clean remaining ReferencedMessageTag
    if "[Name:ReferencedMessageTag" in desc:
        # Contextual inference from title
        t = title.lower()
        if "grassy" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Grassy Terrain', desc)
        elif "electric" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Electric Terrain', desc)
        elif "psychic terrain" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Psychic Terrain', desc)
        elif "dark zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Dark Zone', desc)
            desc = re.sub(r'\[Name:ReferencedMessageTag Idx="1"\s*\]', 'Dark', desc)
        elif "bug zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Bug Zone', desc)
            desc = re.sub(r'\[Name:ReferencedMessageTag Idx="1"\s*\]', 'Bug', desc)
        elif "dragon zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Dragon Zone', desc)
            desc = re.sub(r'\[Name:ReferencedMessageTag Idx="1"\s*\]', 'Dragon', desc)
        elif "ice zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Ice Zone', desc)
            desc = re.sub(r'\[Name:ReferencedMessageTag Idx="1"\s*\]', 'Ice', desc)
        elif "ghost zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Ghost Zone', desc)
        elif "poison zone" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Poison Zone', desc)
        elif "supereffective" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Supereffective ↑ Next effect', desc)
        elif "free move next" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Free Move Next effect', desc)
        elif "physical boost" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Physical Moves ↑ Next effect', desc)
        elif "special boost" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Special Moves ↑ Next effect', desc)
        elif "sync move boost" in t:
            desc = re.sub(r'\[Name:ReferencedMessageTag\s*\]', 'Sync Move ↑ Next effect', desc)
        else:
            desc = re.sub(r'\[Name:ReferencedMessageTag(?: Idx="[^"]*")?\s*\]', '', desc)

    return clean_poma_text(desc)

def process_directory(dir_path, panel_map, ability_map, poma_skills, poma_moves):
    files = glob.glob(f"{dir_path}/*.json")
    print(f"Processing {len(files)} files in {dir_path}...")
    updated_files = 0
    updated_cells = 0

    for f in files:
        with open(f, "r", encoding="utf-8") as inf:
            data = json.load(inf)
        changed = False

        for cell in data.get("grid", []):
            orig_desc = cell.get("description", "")
            if re.search(r'\[[^\]]+\]', orig_desc):
                new_desc = resolve_grid_desc(
                    cell.get("cellId"),
                    cell.get("title", ""),
                    orig_desc,
                    panel_map,
                    ability_map,
                    poma_skills,
                    poma_moves
                )
                if new_desc and new_desc != orig_desc:
                    cell["description"] = new_desc
                    changed = True
                    updated_cells += 1

        if changed:
            with open(f, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
            updated_files += 1

    print(f"  -> Updated {updated_cells} cells across {updated_files} files in {dir_path}")

def main():
    print("1. Fetching AbilityPanel.json proto...")
    panel_data = fetch_json("https://pokemon.brybry.ch/masters/data/proto/AbilityPanel.json")
    panel_map = {p['cellId']: p['abilityId'] for p in panel_data.get('entries', []) if 'cellId' in p and 'abilityId' in p}
    print(f"   Loaded {len(panel_map)} panel entries.")

    print("2. Fetching Ability.json proto...")
    ability_data = fetch_json("https://pokemon.brybry.ch/masters/data/proto/Ability.json")
    ability_map = {e['abilityId']: e for e in ability_data.get('entries', [])}
    print(f"   Loaded {len(ability_map)} ability entries.")

    print("3. Fetching PoMaTools en.json...")
    poma_en = fetch_json("https://pomatools.github.io/assets/i18n/en.json")
    poma_skills = poma_en.get("DATA", {}).get("SKILLS", {})
    poma_moves = poma_en.get("DATA", {}).get("MOVES", {})
    print(f"   Loaded {len(poma_skills)} skills and {len(poma_moves)} moves.")

    process_directory("src/BluesLab/wwwroot/data/pairs", panel_map, ability_map, poma_skills, poma_moves)
    if os.path.exists("output/wwwroot/data/pairs"):
        process_directory("output/wwwroot/data/pairs", panel_map, ability_map, poma_skills, poma_moves)

    print("\nAll done!")

if __name__ == "__main__":
    main()
