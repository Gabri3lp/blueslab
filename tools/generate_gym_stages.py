import urllib.request
import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://raw.githubusercontent.com/absolutelypm/pokemas-datamine/main/2.71/%F0%9F%A5%8A%20Pasio%20Gym%20Battle%20No.%203.txt"
headers = {"User-Agent": "Mozilla/5.0"}
print(f"Downloading gym datamine from: {url}")
req = urllib.request.Request(url, headers=headers)
raw_text = urllib.request.urlopen(req).read().decode('utf-8')
lines = raw_text.splitlines()

# Map of leader info
LEADERS_INFO = {
    "Falkner": {
        "pokemon": "Swellow",
        "icon": "img/pokemon/027700_128.png",
        "pokemonId": "027700",
        "sideIcon": "img/pokemon/001800_128.png",
        "sideMon": "Pidgeot"
    },
    "Bugsy": {
        "pokemon": "Beedrill",
        "icon": "img/pokemon/001500_128.png",
        "pokemonId": "001500",
        "sideIcon": "img/pokemon/012300_128.png",
        "sideMon": "Scyther"
    },
    "Whitney": {
        "pokemon": "Miltank",
        "icon": "img/pokemon/024101_128.png",
        "pokemonId": "024101",
        "sideIcon": "img/pokemon/024101_128.png",
        "sideMon": "Clefairy"
    },
    "Morty": {
        "pokemon": "Drifblim",
        "icon": "img/pokemon/042600_128.png",
        "pokemonId": "042600",
        "sideIcon": "img/pokemon/009400_128.png",
        "sideMon": "Gengar"
    },
    "Chuck": {
        "pokemon": "Poliwrath",
        "icon": "img/pokemon/006200_128.png",
        "pokemonId": "006200",
        "sideIcon": "img/pokemon/006200_128.png",
        "sideMon": "Machamp"
    },
    "Jasmine": {
        "pokemon": "Steelix",
        "icon": "img/pokemon/020801_128.png",
        "pokemonId": "020801",
        "sideIcon": "img/pokemon/008100_128.png",
        "sideMon": "Magnemite"
    },
    "Pryce": {
        "pokemon": "Seel",
        "icon": "img/pokemon/093600_128.png",
        "pokemonId": "093600",
        "sideIcon": "img/pokemon/093600_128.png",
        "sideMon": "Dewgong"
    },
    "Clair": {
        "pokemon": "Kingdra",
        "icon": "img/pokemon/023001_128.png",
        "pokemonId": "023001",
        "sideIcon": "img/pokemon/014800_128.png",
        "sideMon": "Dragonair"
    }
}

CIRCUIT_TITLES = {
    "Circuit 1": "Circuit 1 (Poké Ball Tier - 10,000 pts)",
    "Circuit 2": "Circuit 2 (Great Ball Tier - 35,000 pts)",
    "Circuit 3": "Circuit 3 (Ultra Ball Tier - 80,000 pts)",
    "Extra Battle 1": "Extra Battle 1 (Master Ball Tier - 100,000 pts)",
    "Extra Battle 2": "Extra Battle 2 (Master Ball Tier - 125,000 pts)",
    "Extra Battle 3": "Extra Battle 3 (Master Ball Tier - 150,000 pts)",
    "Extra Battle 4": "Extra Battle 4 (Master Ball Tier - 175,000 pts)",
    "Extra Battle 5": "Extra Battle 5 (Master Ball Tier - 200,000 pts)",
    "Extra Battle 6": "Extra Battle 6 (Master Ball Tier - 225,000 pts)",
    "Extra Battle 7": "Extra Battle 7 (Master Ball Tier - 260,000 pts)",
    "Extra Battle 8": "Extra Battle 8 (Master Ball Tier - 295,000 pts)",
    "Extra Battle 9": "Extra Battle 9 (Master Ball Tier - 330,000 pts)",
    "Extra Battle 10": "Extra Battle 10 (Master Ball Tier - 370,000 pts)",
    "Extra Battle 11": "Extra Battle 11 (Master Ball Tier - 410,000 pts)",
    "Extra Battle 12 and onward": "Extra Battle 12+ (Master Ball Tier - 450,000 pts)"
}

circuit_re = re.compile(r"📋\s*(Circuit \d+|Extra Battle \d+(?:\s*and onward)?)")
leader_re = re.compile(r"🆔\s*([A-Za-z0-9\s’'\-]+?)\s*\|\s*🏷️\s*([A-Za-z]+)\s*\|\s*(.*)")
stats_re = re.compile(r"Weakness:\s*([A-Za-z]+)\s*\|\s*HP:\s*([\d,]+)\s*\|\s*Attack:\s*([\d,]+)\s*\|\s*Defense:\s*([\d,]+)\s*\|\s*Sp\.Attack:\s*([\d,]+)\s*\|\s*Sp\.Def:\s*([\d,]+)\s*\|\s*Speed:\s*([\d,]+)")

leagues_output = []
current_league = None
current_fight = None

for line in lines:
    stripped = line.strip()

    c_match = circuit_re.search(stripped)
    if c_match and ("Circuit" in stripped or "Extra Battle" in stripped):
        c_raw = c_match.group(1).strip()
        c_id = c_raw.lower().replace(" ", "_")
        c_display_name = CIRCUIT_TITLES.get(c_raw, c_raw)
        current_league = {
            "leagueId": c_id,
            "name": c_display_name,
            "fights": []
        }
        leagues_output.append(current_league)
        current_fight = None
        continue

    l_match = leader_re.search(stripped)
    if l_match and current_league is not None:
        leader_name = l_match.group(1).strip()
        stage_type = l_match.group(2).strip()
        stage_desc = l_match.group(3).strip()
        
        info = LEADERS_INFO.get(leader_name, {
            "pokemon": f"{leader_name}'s Pokémon",
            "icon": "img/trainers/unknown.png",
            "pokemonId": "000000",
            "sideIcon": "img/trainers/unknown.png",
            "sideMon": "Minion"
        })

        fight_id = f"{current_league['leagueId']}_{leader_name.lower()}"
        current_fight = {
            "fightId": fight_id,
            "title": f"vs. {leader_name} & {info['pokemon']} ({stage_type})",
            "leader": leader_name,
            "stageType": stage_type,
            "theme": "",
            "rules": [],
            "opponents": []
        }
        current_league["fights"].append(current_fight)
        continue

    if current_fight is not None:
        if stripped.startswith("Theme:"):
            current_fight["theme"] = stripped.replace("Theme:", "").strip()
        elif stripped.startswith("Rules 1:") or stripped.startswith("Rules 2:") or stripped.startswith("Rules 3:"):
            current_fight["rules"].append(stripped)
        elif stripped.startswith("Rule:"):
            current_fight["rules"].append(stripped.replace("Rule:", "").strip())
        elif "[Center]" in stripped:
            m = stats_re.search(stripped)
            if m:
                w, hp, atk, df, spa, spd, spe = m.groups()
                info = LEADERS_INFO.get(current_fight["leader"], {})
                current_fight["opponents"].append({
                    "slotIndex": 1, # Center
                    "trainerName": current_fight["leader"],
                    "pokemonName": info.get("pokemon", "Boss"),
                    "pokemonId": info.get("pokemonId", "000000"),
                    "iconUrl": info.get("icon", "img/trainers/unknown.png"),
                    "weakness": w,
                    "hp": int(hp.replace(",", "")),
                    "atk": int(atk.replace(",", "")),
                    "def": int(df.replace(",", "")),
                    "spa": int(spa.replace(",", "")),
                    "spd": int(spd.replace(",", "")),
                    "spe": int(spe.replace(",", ""))
                })
        elif "[Left/Right]" in stripped:
            m = stats_re.search(stripped)
            if m:
                w, hp, atk, df, spa, spd, spe = m.groups()
                info = LEADERS_INFO.get(current_fight["leader"], {})
                for slot in [0, 2]:
                    current_fight["opponents"].append({
                        "slotIndex": slot,
                        "trainerName": "Gym Minion",
                        "pokemonName": info.get("sideMon", "Minion"),
                        "pokemonId": "000000",
                        "iconUrl": info.get("sideIcon", info.get("icon", "img/trainers/unknown.png")),
                        "weakness": w,
                        "hp": int(hp.replace(",", "")),
                        "atk": int(atk.replace(",", "")),
                        "def": int(df.replace(",", "")),
                        "spa": int(spa.replace(",", "")),
                        "spd": int(spd.replace(",", "")),
                        "spe": int(spe.replace(",", ""))
                    })

dest = "src/BluesLab/wwwroot/data/stages_manifest.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(leagues_output, f, indent=2, ensure_ascii=False)

print(f"Generated {dest} with {len(leagues_output)} circuits and {sum(len(l['fights']) for l in leagues_output)} fights!")
