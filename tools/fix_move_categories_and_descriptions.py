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

    # Clean up stat rank grammar
    if val == 1:
        desc = desc.replace("1 stat rank(s)", "1 stat rank")
        desc = desc.replace("1 stat ranks", "1 stat rank")
    else:
        desc = desc.replace(f"{val} stat rank(s)", f"{val} stat ranks")
        desc = re.sub(rf'\b{val} stat rank\b', f"{val} stat ranks", desc)

    desc = desc.replace("stat rank(s)", "stat ranks")
    return clean_poma_text(desc)

# Explicit descriptions for newest 2026 units not yet in PoMaTools
MANUAL_MOVE_FIXES = {
    "6191": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nWhen this move is used.\n\nNever misses. Lowers the target’s Sp. Def by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. This attack’s power increases 50% when the target is paralyzed.",
    "6192": "Activation Condition:\nWhen your team’s sync pair uses a sync move once.\nDeactivation Condition:\nWhen this move is used.\n\nHas a chance (10%) of leaving the target frozen. Increases the user’s Sync Move ↑ Next effect by 3 ranks.",
    "6193": "Activation Condition:\nWhen the user is asleep.\nDeactivation Condition:\nWhen the user is not asleep.\n\nNever misses. Lowers the Attack and Sp. Atk of all opposing sync pairs by 2 stat ranks. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank. Applies Paldea Circle (Special) to the allied field of play.",
    "6195": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nCannot be deactivated.\n\nIgnores the target’s raised stats. Lowers the target’s Defense and Speed by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. If the remaining MP for the user’s Dark Wish is 1 or more when attacking with this move, reduces those MP by 1 and grants all of the following effects: Turns the field of play’s zone into a Dark Zone. Reduces the user’s sync move countdown by 2.",
    "6199": "Activation Condition:\nWhen a circle is applied to the allied field of play.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Lowers the target’s Defense and Sp. Def by 2 stat ranks. Leaves the target paralyzed. Has a chance (30%) of making the target flinch.",
    "6200": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nWhen this move is used.\n\nNever misses. The power of this move is not lowered even if there are multiple targets. Turns the field of play’s terrain into Electric Terrain. Reduces the user’s sync move countdown by 1. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6201": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nRemoves the frozen condition from the user. Never misses. The more the user’s sync buff is raised, the greater the power of this attack. (The maximum increase is 10 ranks.) Lowers the target’s Attack and Defense by 2 stat ranks. Leaves the target burned.",
    "6203": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Leaves all opposing sync pairs confused. Turns the field of play’s zone into a Ghost Zone. Reduces the user’s sync move countdown by 1. Increases the Special Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6204": "Activation Condition:\nWhen the user’s Physical Moves ↑ Next effect is increased.\nDeactivation Condition:\nWhen the user’s Physical Moves ↑ Next effect is not increased.\n\nNever misses. Except in certain circumstances, successful hits with this attack become critical hits. Increases the user’s Physical Moves ↑ Next effect by 3 ranks. Grants all of the following effects the first time this attack move is successful each battle: Applies the Physical Move Break effect to the target. Reduces the user’s sync move countdown by 2.",
    "6205": "Activation Condition:\nWhen there is at least one Pokémon with a lowered Type Rebuff on the opponent’s field of play.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Lowers the target’s Defense and Sp. Def by 3 stat ranks. Leaves the target badly poisoned. Removes a damage field from the allied field of play. Removes the trapped condition from the user.",
    "6206": "Activation Condition:\nWhen there is at least one Pokémon affected by a status condition on the opponent’s field of play.\nDeactivation Condition:\nWhen there are no longer any Pokémon affected by a status condition on the opponent’s field of play.\n\nNever misses. This attack’s power is doubled when the target is poisoned or badly poisoned. Applies the Physical Move Break effect and Special Move Break effect to the target the first time this attack move is successful each battle. Turns the field of play’s zone into a Poison Zone. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6207": "Activation Condition:\nWhen the user’s Sp. Atk is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nLowers the target’s Sp. Atk and Sp. Def by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. If the user’s Gardevoir has Mega Evolved, also decreases the amount of move gauge slots needed to use this move by 2.",
    "6208": "Activation Condition:\nWhen the user’s Gardevoir Mega Evolves.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. The more the user’s Special Moves ↑ Next effect is increased, the greater the power of this attack. Has a chance (50%) of lowering the target’s Sp. Atk by 2 stat ranks. The power and chance of applying additional effects of this move are not lowered even if there are multiple targets.",
    "6209": "Activation Condition:\nWhen the user is not in a pinch.\nDeactivation Condition:\nWhen the user is in a pinch.\n\nRemoves all status conditions from all allied sync pairs. Raises the Attack, Defense, Sp. Atk, and Sp. Def of all allied sync pairs by 2 stat ranks. In addition, increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank when the weather is rainy.",
    "6210": "Activation Condition:\nWhen the user’s Trainer uses any move 2 times.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Except in certain circumstances, successful hits with this attack become critical hits. The more fainted Pokémon on your team, the greater the power of this attack. Lowers the target’s Defense by 3 stat ranks. The power of this move is not lowered even if there are multiple targets. Restores 1 MP for this move when you have two or more Pokémon on your team.",
    "6211": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nWhen the user’s Attack is not raised.\n\nLowers the target’s Defense and Sp. Def by 2 stat ranks. Has a chance (30%) of making the target flinch. The power and chance of applying additional effects of this move are not lowered even if there are multiple targets. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "6212": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nWhen the user’s Attack is not raised.\n\nLowers the target’s Defense and Sp. Def by 2 stat ranks. Has a chance (30%) of making the target flinch. The power and chance of applying additional effects of this move are not lowered even if there are multiple targets. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "6213": "Activation Condition:\nWhen a circle is applied to the allied field of play.\nDeactivation Condition:\nWhen there are no longer any circles applied to the allied field of play.\n\nNever misses. Lowers the target’s Defense by 3 stat ranks. Applies the Physical Move Break effect to the target the first time this attack move is successful each battle. Turns the field of play’s zone into a Dark Zone the first time this attack move is successful each battle. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6214": "Activation Condition:\nWhen your team’s sync pair uses a sync move once.\nDeactivation Condition:\nWhen this move is used.\n\nLowers the target’s Attack and Sp. Atk by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. Applies the Free Move Next effect to the user.",
    "6216": "Activation Condition:\nWhen the user’s Sp. Atk is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nLowers the target’s Sp. Def by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. In addition, lowers the target’s Sp. Def by 2 stat ranks when Kalos Circle (Special) applies to the allied field of play.",
    "6218": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nLowers the target’s Defense by 2 stat ranks. The power of this move is not lowered even if there are multiple targets.",
    "6219": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nCannot be deactivated.\n\nReduces the user’s sync move countdown by 2. Increases the user’s Physical Moves ↑ Next effect by 3 ranks. If the user’s Feraligatr has Mega Evolved, also increases this attack’s power by 50%.",
    "6220": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nCannot be deactivated.\n\nLowers the target’s Attack and Sp. Atk by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. If the remaining MP for the user’s Fairy Wish is 1 or more when attacking with this move, reduces those MP by 1 and grants all of the following effects: Turns the field of play’s zone into a Fairy Zone. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6221": "Activation Condition:\nWhen the user’s Sp. Atk is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Lowers the target’s Sp. Def by 2 stat ranks.",
    "6222": "Activation Condition:\nWhen the user uses a sync move once.\nDeactivation Condition:\nWhen this move is used.\n\nNever misses. Except in certain circumstances, successful hits with this attack become critical hits. Reduces the user’s sync move countdown by 2 the first time this attack move is successful each battle. Increases the user’s Special Moves ↑ Next effect by 10 ranks.",
    "6223": "Activation Condition:\nWhen the user’s Defense is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nLowers the target’s Attack and Sp. Atk by 2 stat ranks. Leaves the target either flinching, confused, or trapped. Leaves the target paralyzed. The power of this move is not lowered even if there are multiple targets.",
    "6224": "Activation Condition:\nWhen the user uses a sync move once.\nDeactivation Condition:\nWhen this move is used.\n\nNever misses. Reduces the user’s sync move countdown by 2 the first time this attack move is successful each battle. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6225": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nWhen the user’s Attack is not raised.\n\nNever misses. Except in certain circumstances, successful hits with this attack become critical hits. Lowers the target’s Defense and Sp. Def by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. Charges the user’s move gauge by 1 for each hit.",
    "6226": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nWhen this move is used.\n\nAttacks the target two to five times in a row. Never misses. Increases the user’s Physical Moves ↑ Next effect and Special Moves ↑ Next effect by 1 rank for each hit.",
    "6228": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. Has a chance (30%) of making the target flinch. The power and chance of applying additional effects of this move are not lowered even if there are multiple targets.",
    "6229": "Activation Condition:\nWhen the user’s Dragonite Mega Evolves.\nDeactivation Condition:\nCannot be deactivated.\n\nNever misses. The more the user’s sync buff is raised, the greater the power of this attack. (The maximum increase is 10 ranks.) The power of this move is not lowered even if there are multiple targets. The more the user’s sync buff is raised, the more its sync move countdown is reduced the first time this attack move is successful each battle. (The maximum reduction is 3.)",
    "6230": "Activation Condition:\nWhen the user’s Dragonite has not Mega Evolved.\nDeactivation Condition:\nWhen the user’s Dragonite Mega Evolves.\n\nNever misses. Lowers the target’s Defense and Sp. Def by 2 stat ranks. The power of this move is not lowered even if there are multiple targets. Reduces the user’s sync move countdown by 1 the first time this attack move is successful each battle.",
    "6237": "Activation Condition:\nWhen the user’s Attack is raised.\nDeactivation Condition:\nCannot be deactivated.\n\nAttacks twice in a row. Never misses. Leaves the target badly poisoned. Has a chance (30%) of making the target flinch. Has a chance (30%) of leaving the target confused. Has a chance (30%) of leaving the target trapped. Turns the field of play’s zone into a Poison Zone the first time this attack move is successful each battle. (A Poison Zone powers up Poison-type attacks.)",
    "6238": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nCannot be deactivated.\n\nMakes the weather EX rainy. Reduces the user’s sync move countdown by 2. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "6239": "Activation Condition:\nWhen the user uses any move once.\nDeactivation Condition:\nWhen this move is used.\n\nLowers the target’s Flying Type Rebuff by 1 rank the first time this attack move is successful each battle. Turns the field of play’s zone into a Flying Zone the first time this attack move is successful each battle. (A Flying Zone powers up Flying-type attacks.) Increases the Physical Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "8209": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank. Applies Sinnoh Circle (Physical) to the allied field of play.",
    "8215": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank. Applies Kalos Circle (Physical) to the allied field of play.",
    "8216": "Increases the Special Moves ↑ Next effect of all allied sync pairs by 1 rank. Applies Kalos Circle (Special) to the allied field of play.",
    "10027": "Reduces the user’s sync move countdown by 2. Increases the user’s Physical Moves ↑ Next effect by 3 ranks. Increases the user’s Special Moves ↑ Next effect by 3 ranks.",
    "10176": "Reduces an ally’s sync move countdown by 1. Raises an ally’s Attack by 4 stat ranks. Raises an ally’s critical-hit rate by 3 stat ranks.",
    "10197": "Reduces an ally’s sync move countdown by 1. Raises an ally’s Attack by 4 stat ranks. Raises an ally’s critical-hit rate by 3 stat ranks.",
    "10212": "Removes all status conditions and the flinching, confused, and trapped conditions from the user. Applies the Damage Guard Next effect to the user. If the user’s Dragonite has Mega Evolved, also increases the user’s Physical Moves ↑ Next effect by 10 ranks.",
    "10261": "Raises the user’s Sp. Atk by 4 stat ranks. Applies the Free Move Next effect to the user. Increases the user’s Special Moves ↑ Next effect by 3 ranks.",
    "10294": "Restores an ally’s HP by approximately 40% of its maximum HP. Applies the Damage Guard Next effect to an ally. Applies the Enduring effect to an ally.",
    "10588": "Applies the Move Gauge Acceleration effect to the allied field of play. Raises the user’s Attack by 4 stat ranks. Raises the user’s Defense by 2 stat ranks.",
    "10915": "Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks. Applies the Gradual Healing effect to all allied sync pairs.",
    "10987": "Raises the Attack, Sp. Atk, and evasiveness of all allied sync pairs by 2 stat ranks.",
    "10988": "Reduces the sync move countdown of an ally by 1. Applies the Supereffective ↑ Next effect to an ally. Applies the Damage Guard Next effect to an ally.",
    "11099": "Raises the user’s Attack by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks.",
    "11127": "Raises an ally’s Sp. Atk by 4 stat ranks. Raises an ally’s critical-hit rate by 3 stat ranks. Increases the Special Moves ↑ Next effect of an ally by 2 ranks.",
    "11166": "Applies the Supereffective ↑ Next effect to the user. Increases the user’s Special Moves ↑ Next effect by 3 ranks. Applies the Enduring effect to the user.",
    "11231": "Reduces the sync move countdown of an ally by 1. Applies the Supereffective ↑ Next effect to an ally. Increases the Physical Moves ↑ Next effect of an ally by 2 ranks.",
    "11305": "Increases the user’s Physical Moves ↑ Next effect and Special Moves ↑ Next effect by 3 ranks. If the user’s Greninja has Mega Evolved, also increases the user’s Sync Move ↑ Next effect by 10 ranks.",
    "11528": "Raises the user’s Defense and Sp. Def by 2 stat ranks. Applies the Gradual Healing effect to the user.",
    "11588": "Reduces the user’s sync move countdown by 1. Applies the Gradual Healing effect to the user. Applies the Damage Guard Next effect to the user. Applies the Enduring effect to the user. If the user’s Gardevoir has Mega Evolved, also increases the user’s Special Moves ↑ Next effect by 3 ranks.",
    "11949": "Reduces an ally’s sync move countdown by 1. Raises an ally’s Attack by 4 stat ranks. Raises an ally’s critical-hit rate by 3 stat ranks.",
    "12010": "Raises the Attack, Sp. Atk, and critical-hit rate of all allied sync pairs by 2 stat ranks.",
    "12259": "Applies the Move Gauge Acceleration effect to the allied field of play. Raises the user’s Attack by 4 stat ranks. Raises the user’s Speed by 2 stat ranks. Applies the Gradual Healing effect to the user.",
    "12269": "Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks. Applies the Gradual Healing effect to the user.",
    "12279": "Reduces the user’s sync move countdown by 1. Raises the user’s Attack by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks. Increases the user’s Physical Moves ↑ Next effect by 2 ranks.",
    "12498": "Raises an ally’s Attack by 4 stat ranks. Raises an ally’s Speed by 2 stat ranks.",
    "12868": "Reduces the user’s sync move countdown by 1. Applies the Supereffective ↑ Next effect to the user. Applies the Free Move Next effect to the user.",
    "12911": "Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks. Applies the Gradual Healing effect to all allied sync pairs.",
    "12914": "Makes the weather rainy. Reduces the user’s sync move countdown by 2. Raises the Sp. Atk of all allied sync pairs by 4 stat ranks.",
    "12988": "Raises the Attack and Sp. Atk of all allied sync pairs by 2 stat ranks. Raises the Defense of all allied sync pairs by 2 stat ranks.",
    "13028": "Applies the Move Gauge Acceleration effect to the allied field of play. Increases the Physical Moves ↑ Next effect of an ally by 2 ranks. Increases the Special Moves ↑ Next effect of an ally by 2 ranks.",
    "13038": "Applies the Move Gauge Acceleration effect to the allied field of play. Increases the Physical Moves ↑ Next effect of an ally by 2 ranks. Increases the Special Moves ↑ Next effect of an ally by 2 ranks.",
    "13043": "Reduces the sync move countdown of an ally by 1. Raises an ally’s Attack and Sp. Atk by 2 stat ranks. Raises an ally’s critical-hit rate by 2 stat ranks.",
    "13124": "Reduces the user’s sync move countdown by 2. Raises the user’s Attack and Sp. Atk by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks.",
    "13150": "Raises the user’s Attack by 4 stat ranks. Applies the Supereffective ↑ Next effect to the user. Increases the user’s Physical Moves ↑ Next effect by 3 ranks.",
    "13480": "Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank. Applies the Damage Guard Next effect to the user.",
    "13568": "Reduces the user’s sync move countdown by 1. Raises the Attack of all allied sync pairs by 4 stat ranks. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 2 ranks.",
    "13571": "Increases the user’s Physical Moves ↑ Next effect by 3 ranks. Increases the user’s Special Moves ↑ Next effect by 3 ranks. Applies the Enduring effect to the user.",
    "13600": "Increases the Physical Moves ↑ Next effect of an ally by 3 ranks. Applies the Enduring effect to an ally.",
    "13660": "Raises the user’s Attack by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks. Applies Kalos Circle (Physical) to the allied field of play.",
    "13670": "Raises the user’s Sp. Atk by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks. Applies Kalos Circle (Special) to the allied field of play.",
    "13679": "Raises the Defense and Sp. Def of all allied sync pairs by 2 stat ranks. Applies the Gradual Healing effect to all allied sync pairs.",
    "17019": "Raises the Sp. Atk and Sp. Def of all allied sync pairs by 2 stat ranks. Increases the Special Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "65100": "Become Mega Gardevoir until the end of battle. Increases the user’s Special Moves ↑ Next effect by 10 ranks.",
    "124000": "Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 3 ranks the first time the user’s sync move is used each battle."
}

MANUAL_PASSIVE_FIXES = {
    "12023009": "Increases the user’s Sync Move ↑ Next effect by 3 ranks when its attack move is successful against a poisoned or badly poisoned opponent.",
    "17093201": "Increases the Special Moves ↑ Next effect of all allied sync pairs by 1 rank when the user applies Paldea Circle (Special) to the allied field of play.",
    "17093401": "Increases the user’s Sync Move ↑ Next effect by 10 ranks the first time the remaining MP for its Dark Wish is zero each battle.",
    "17093509": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user turns the field of play’s zone into a Dark Zone.",
    "17093609": "Increases the Special Moves ↑ Next effect of all allied sync pairs by 1 rank when an ally turns the field of play’s zone into a Normal Zone.",
    "17094509": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user’s attack move (except its buddy move) is successful while the remaining MP for its buddy move is zero.",
    "17095709": "Increases the user’s Special Moves ↑ Next effect by 2 ranks when an ally turns the field of play’s zone into a Fairy Zone.",
    "17095809": "Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank when the user makes the weather rainy.",
    "17096601": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user applies Paldea Circle (Physical) to the allied field of play.",
    "17097003": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 3 ranks the first time the remaining MP for the user’s Fairy Wish is zero each battle.",
    "17097809": "Increases the user’s Special Moves ↑ Next effect by 2 ranks when an ally applies a circle to the allied field of play.",
    "17098209": "Increases the user’s Physical Moves ↑ Next effect by 2 ranks when its attack move is successful while the zone is an Ice Zone.",
    "17098309": "Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user turns the field of play’s zone into a Flying Zone.",
    "18128309": "Lowers the target’s Attack and Sp. Atk by 1 stat rank when the user’s attack move is successful against targets that are affected by a status condition.",
    "18128903": "Raises the user’s Attack and Sp. Atk by 4 stat ranks the first time its Trainer uses a move each battle. Raises the user’s critical-hit rate by 3 stat ranks the first time its Trainer uses a move each battle.",
    "18129003": "Raises the user’s Attack by 6 stat ranks the first time its Trainer uses a move each battle. Raises the user’s critical-hit rate by 3 stat ranks the first time its Trainer uses a move each battle.",
    "18129609": "Lowers the target’s Defense by 2 stat ranks when the user’s attack move is successful while the zone is a Fairy Zone.",
    "18130209": "Lowers the Sp. Def of all opposing sync pairs by 3 stat ranks when the user’s Pokémon uses a status move.",
    "18130501": "When an opponent’s stat is lowered by the additional effects of the user’s Lunge, it is lowered by three times the stat ranks.",
    "18130606": "Raises the Speed of all allied sync pairs by 6 stat ranks the first time the user’s sync move is used each battle.",
    "18130709": "Lowers the target’s Attack and Sp. Atk by 1 stat rank when the user’s Pokémon uses a move targeting that opponent.",
    "18130802": "Lowers the Attack and Sp. Atk of all opposing sync pairs by 2 stat ranks when the user enters a battle.",
    "18130909": "Raises the evasiveness of all allied sync pairs by 2 stat ranks when the user causes a hailstorm.",
    "25010501": "Grants all of the following effects when the user uses Sunny Day or an ally turns the weather sunny: Reduces the user’s sync move countdown by 1. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "25010601": "Grants all of the following effects when the user uses Electric Terrain or an ally turns the field of play’s terrain into Electric Terrain: Reduces the user’s sync move countdown by 1. Increases the Physical Moves ↑ Next effect and Special Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "28041101": "Powers up the moves and sync moves of all allied sync pairs by 20%. Reduces attack move and sync move damage taken by all allied sync pairs by 25%. The more allied sync pairs with the Johto theme you have on your team, the higher these percentages are. (Each additional sync pair powers up moves and sync moves by 15% and reduces damage by 3%. The maximum power-up is 50%, and the maximum damage reduction is 31%.) Raises the sync buff of the user’s team by 1 rank the first time its sync move is used each battle.",
    "28041201": "Powers up the moves and sync moves of all allied sync pairs by 20%. Reduces attack move and sync move damage taken by all allied sync pairs by 25%. The more allied sync pairs with the Johto theme you have on your team, the higher these percentages are. (Each additional sync pair powers up moves and sync moves by 15% and reduces damage by 3%. The maximum power-up is 50%, and the maximum damage reduction is 31%.) Raises the sync buff of the user’s team by 1 rank the first time its sync move is used each battle.",
    "28041401": "Powers up the moves and sync moves of all allied sync pairs by 20%. Reduces attack move and sync move damage taken by all allied sync pairs by 25%. The more allied sync pairs with the Sinnoh theme you have on your team, the higher these percentages are. (Each additional sync pair powers up moves and sync moves by 15% and reduces damage by 3%. The maximum power-up is 50%, and the maximum damage reduction is 31%.) Increases the user’s Special Moves ↑ Next effect by 2 ranks when an ally applies a circle to the allied field of play.",
    "29021201": "Raises the Fairy Type Rebuff of all allied sync pairs by 1 rank the first time the user enters a battle each battle. Lowers the Fairy Type Rebuff of all opposing sync pairs by 1 rank the first time the user enters a battle each battle.",
    "29021301": "Raises the Poison Type Rebuff of all allied sync pairs by 1 rank the first time the user enters a battle each battle. Lowers the Poison Type Rebuff of all opposing sync pairs by 1 rank the first time the user enters a battle each battle.",
    "99041401": "Reduces the MP for the user’s Trainer move by 1 and grants all of the following effects after your team’s sync pair uses their sync move: Applies Paldea Circle (Physical) to the allied field of play. Increases the user’s Physical Moves ↑ Next effect by 3 ranks. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank.",
    "99042301": "When the user’s status move is used and inflicted a status condition on an opponent, inflicts the same status condition on all opposing sync pairs. Lowers the target’s Attack and Sp. Atk by 1 stat rank when the user’s attack move is successful against targets that are affected by a status condition.",
    "99042401": "Grants all of the following effects the first time the user enters a battle each battle: Applies Sinnoh Circle (Physical) to the allied field of play. Raises the user’s Attack by 6 stat ranks. Increases the user’s Physical Moves ↑ Next effect by 3 ranks.",
    "99042501": "Applies the Free Move Next effect to the user when its attack move (except its buddy move) is successful while the remaining MP for its buddy move is zero. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user’s attack move (except its buddy move) is successful while the remaining MP for its buddy move is zero.",
    "99042701": "Raises the Attack, Defense, Sp. Atk, and Sp. Def of all allied sync pairs by 1 stat rank when the user’s attack move is successful.",
    "99042801": "Grants all of the following effects the first time the user enters a battle each battle: Reduces the user’s sync move countdown by 1. Raises the user’s Attack and Sp. Atk by 3 stat ranks. Increases the user’s Physical Moves ↑ Next effect by 3 ranks.",
    "99042901": "Grants all of the following effects after your team’s sync pair uses their sync move: Restores the user’s HP by approximately 20% of its maximum HP. Increases the user’s Physical Moves ↑ Next effect by 3 ranks. Restores 1 MP of the user’s buddy move.",
    "99044001": "Reduces the user’s sync move countdown by 1 when it enters a battle. Raises the user’s Sp. Atk by 6 stat ranks and critical-hit rate by 3 stat ranks when it enters a battle. Except in certain circumstances, successful hits with the user’s following attacks become critical hits: Pokémon’s moves or sync move.",
    "99044401": "Leaves all opposing sync pairs badly poisoned the first time the user enters a battle each battle. Raises the Attack and Sp. Atk of all allied sync pairs by 4 stat ranks when the user enters a battle.",
    "99044701": "Grants all of the following effects the first time the user’s Trainer uses a move each battle: Turns the field of play’s zone into a Ground Zone. (A Ground Zone powers up Ground-type attacks.) Raises the user’s Attack and Sp. Atk by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks.",
    "99044801": "Grants all of the following effects the first time the user’s Trainer uses a move each battle: Turns the field of play’s zone into a Steel Zone. (A Steel Zone powers up Steel-type attacks.) Raises the user’s Attack and Sp. Atk by 4 stat ranks. Raises the user’s critical-hit rate by 3 stat ranks.",
    "99046501": "Grants all of the following effects the first time the user enters a battle each battle: Turns the field of play’s zone into a Dragon Zone. (A Dragon Zone powers up Dragon-type attacks.) Applies Free Move Next to the allied field of play. Raises the user’s Sp. Atk by 6 stat ranks.",
    "99046801": "Reduces the user’s sync move countdown by 1 when it enters a battle. Raises the user’s Attack and Sp. Atk by 6 stat ranks when it enters a battle.",
    "99047101": "Normal-type moves become Flying-type moves. Turns the field of play’s zone into a Flying Zone the first time the user enters a battle each battle. (A Flying Zone powers up Flying-type attacks.) Raises the user’s Attack by 6 stat ranks the first time it enters a battle each battle.",
    "99047201": "Grants all of the following effects the first time the user enters a battle each battle: Turns the field of play’s zone into a Dragon Zone. (A Dragon Zone powers up Dragon-type attacks.) Applies Free Move Next to the allied field of play. Raises the Defense and Sp. Def of all allied sync pairs by 4 stat ranks.",
    "99049901": "When the user’s status move is used and inflicted a status condition on an opponent, inflicts the same status condition on all opposing sync pairs. Lowers the Sp. Def of all opposing sync pairs by 3 stat ranks when the user’s Pokémon uses a status move.",
    "99050201": "The power of the user’s Lunge is tripled. When an opponent’s stat is lowered by the additional effects of the user’s Lunge, it is lowered by three times the stat ranks. When the user’s sync move attacks an opponent, the target becomes all opposing sync pairs. The power of sync moves affected by this passive skill is not lowered even if there are multiple targets.",
    "99050401": "Normal-type moves become Flying-type moves. Applies Physical Move Break to the allied field of play when the user turns the field of play’s zone into a Flying Zone. Increases the Physical Moves ↑ Next effect of all allied sync pairs by 1 rank when the user turns the field of play’s zone into a Flying Zone."
}

def resolve_passive_desc(pid, p_name, current_desc, poma_skills):
    pid_str = str(pid)
    
    # Check manual overrides first
    if pid_str in MANUAL_PASSIVE_FIXES:
        return MANUAL_PASSIVE_FIXES[pid_str]
    
    # Check PoMaTools
    base_pid = str(int(pid_str) // 10) if len(pid_str) > 1 else pid_str
    base_pid0 = pid_str[:-1] + "0" if len(pid_str) > 1 else pid_str

    if pid_str in poma_skills:
        return evaluate_skill_template(poma_skills[pid_str].get("DESC", ""), pid_str)
    elif base_pid in poma_skills:
        return evaluate_skill_template(poma_skills[base_pid].get("DESC", ""), pid_str)
    elif base_pid0 in poma_skills:
        return evaluate_skill_template(poma_skills[base_pid0].get("DESC", ""), pid_str)

    # General cleanup for any remaining passive description
    desc = current_desc
    # If it contains "by stat ranks" or "by stat rank", infer from name if possible
    m = re.search(r'[↑↓]\s*(\d+)', p_name)
    if m:
        num = m.group(1)
        rank_str = "1 stat rank" if num == "1" else f"{num} stat ranks"
        desc = re.sub(r'\bby stat ranks\b', f"by {rank_str}", desc)
        desc = re.sub(r'\bby stat rank\b', f"by {rank_str}", desc)
    else:
        desc = re.sub(r'\bby stat ranks\b', "by 1 stat rank", desc)
    
    return clean_poma_text(desc)

def resolve_move_desc(mid, m_name, current_desc, poma_moves):
    mid_str = str(mid)

    # Check manual overrides first
    if mid_str in MANUAL_MOVE_FIXES:
        return MANUAL_MOVE_FIXES[mid_str]

    # Check PoMaTools
    if mid_str in poma_moves:
        return clean_poma_text(poma_moves[mid_str].get("DESC", ""))

    # Fallback cleanup
    desc = current_desc
    desc = re.sub(r'\bby stat ranks\b', "by 2 stat ranks", desc)
    return clean_poma_text(desc)

def main():
    print("1. Fetching Move.json proto...")
    move_proto = fetch_json("https://pokemon.brybry.ch/masters/data/proto/Move.json")
    move_map = {m.get("moveId"): m for m in move_proto.get("entries", [])}
    print(f"   Loaded {len(move_map)} moves from proto.")

    print("2. Fetching PoMaTools en.json...")
    poma_en = fetch_json("https://pomatools.github.io/assets/i18n/en.json")
    poma_moves = poma_en.get("DATA", {}).get("MOVES", {})
    poma_skills = poma_en.get("DATA", {}).get("SKILLS", {})
    print(f"   Loaded {len(poma_moves)} moves and {len(poma_skills)} skills from PoMaTools.")

    pairs_dir = "C:/Users/Gabri/Documents/blueslab/src/BluesLab/wwwroot/data/pairs"
    files = glob.glob(f"{pairs_dir}/*.json")
    print(f"3. Updating {len(files)} pair JSON files in {pairs_dir}...")

    updated_count = 0
    total_moves_updated = 0
    total_passives_updated = 0

    for f in files:
        with open(f, "r", encoding="utf-8") as inf:
            data = json.load(inf)
        changed = False

        # Update moves
        for m in data.get("moves", []):
            mid = m.get("id")
            if mid in move_map:
                proto_mv = move_map[mid]
                cat = proto_mv.get("category")
                if cat in ["Physical", "Special", "Status"]:
                    if m.get("category") != cat:
                        m["category"] = cat
                        changed = True
                
                gd = proto_mv.get("gaugeDrain")
                if gd is not None:
                    m["gauge"] = str(gd)
                    changed = True
                
                tgt = proto_mv.get("target")
                if tgt:
                    tgt_name = "An opponent" if tgt == "OpponentSingle" else ("All opponents" if tgt == "OpponentAll" else ("Self" if tgt == "Self" else ("All allies" if tgt == "AllyAll" else "An ally")))
                    if m.get("target") != tgt_name:
                        m["target"] = tgt_name
                        changed = True

                # Uses / Max Uses
                uses = proto_mv.get("uses", 0)
                if m.get("maxUses") != uses:
                    m["maxUses"] = uses
                    changed = True

                # Trainer Move
                is_trainer = (proto_mv.get("user") == "Trainer") or (proto_mv.get("type") == 0) or (10000 <= mid < 20000)
                if m.get("isTrainer") != is_trainer:
                    m["isTrainer"] = is_trainer
                    changed = True

                if is_trainer:
                    if m.get("type") != "Trainer":
                        m["type"] = "Trainer"
                        changed = True
                    if m.get("accuracy") != "-":
                        m["accuracy"] = "-"
                        changed = True
                    if m.get("gauge") != "-":
                        m["gauge"] = "-"
                        changed = True

            orig_desc = m.get("description", "")
            resolved_desc = resolve_move_desc(mid, m.get("name", ""), orig_desc, poma_moves)
            if resolved_desc and resolved_desc != orig_desc:
                m["description"] = resolved_desc
                changed = True
                total_moves_updated += 1

        # Update passives
        for p in data.get("passives", []):
            orig_desc = p.get("description", "")
            pid = p.get("id")
            p_name = p.get("name", "")
            resolved_desc = resolve_passive_desc(pid, p_name, orig_desc, poma_skills)
            if resolved_desc and resolved_desc != orig_desc:
                p["description"] = resolved_desc
                changed = True
                total_passives_updated += 1
            
            for cp in p.get("childPassives", []):
                cp_orig = cp.get("description", "")
                cpid = cp.get("id")
                cp_name = cp.get("name", "")
                cp_resolved = resolve_passive_desc(cpid, cp_name, cp_orig, poma_skills)
                if cp_resolved and cp_resolved != cp_orig:
                    cp["description"] = cp_resolved
                    changed = True
                    total_passives_updated += 1

        if changed:
            with open(f, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
            updated_count += 1

    print(f"\nDone! Updated {updated_count} files.")
    print(f"Moves updated: {total_moves_updated}")
    print(f"Passives updated: {total_passives_updated}")

    # Also update tools/fix_move_categories_and_descriptions.py with the new code
    script_path = "C:/Users/Gabri/Documents/blueslab/tools/fix_move_categories_and_descriptions.py"
    with open(__file__, "r", encoding="utf-8") as cur:
        code = cur.read()
    with open(script_path, "w", encoding="utf-8") as out_script:
        out_script.write(code)
    print(f"Also updated {script_path} successfully!")

if __name__ == "__main__":
    main()
