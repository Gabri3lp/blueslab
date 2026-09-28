import urllib.request
import json
import re
import os
import sys
from PIL import Image
import io

sys.stdout.reconfigure(encoding='utf-8')

url = "https://raw.githubusercontent.com/absolutelypm/pokemas-datamine/main/2.73/%F0%9F%A5%8A%20Pasio%20Gym%20Battle%20No.%204.txt"
headers = {"User-Agent": "Mozilla/5.0"}
print(f"Downloading gym datamine from: {url}")
req = urllib.request.Request(url, headers=headers)
raw_text = urllib.request.urlopen(req).read().decode('utf-8')
lines = raw_text.splitlines()

# Ensure all needed Pokemon icons exist in src/BluesLab/wwwroot/img/pokemon
pokemon_dir = "src/BluesLab/wwwroot/img/pokemon"
MISSING_ICONS = [
    ("004500_128.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/45.png"),
    ("088200_128.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/882.png"),
    ("042900_128.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/429.png"),
    ("041100_128.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/411.png"),
    ("003861_128.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/10104.png")
]

for fname, icon_url in MISSING_ICONS:
    fpath = os.path.join(pokemon_dir, fname)
    if not os.path.exists(fpath):
        r = urllib.request.Request(icon_url, headers=headers)
        data = urllib.request.urlopen(r).read()
        img = Image.open(io.BytesIO(data)).resize((128, 128), Image.Resampling.LANCZOS)
        img.save(fpath)
        print(f"Downloaded and resized {fname}")

# Map of Sinnoh Gym Battle No. 4 leader & side minion info (from Quest.txt)
LEADERS_INFO = {
    "Roark": {
        "pokemon": "Cranidos",
        "icon": "img/pokemon/040800_128.png",
        "pokemonId": "040800",
        "leftTrainer": "Camper",
        "leftMon": "Rhyperior",
        "leftIcon": "img/pokemon/046400_128.png",
        "rightTrainer": "Youngster",
        "rightMon": "Onix",
        "rightIcon": "img/pokemon/009500_128.png"
    },
    "Gardenia": {
        "pokemon": "Roserade",
        "icon": "img/pokemon/040700_128.png",
        "pokemonId": "040700",
        "leftTrainer": "Lass",
        "leftMon": "Breloom",
        "leftIcon": "img/pokemon/028600_128.png",
        "rightTrainer": "Beauty",
        "rightMon": "Vileplume",
        "rightIcon": "img/pokemon/004500_128.png"
    },
    "Maylene": {
        "pokemon": "Medicham",
        "icon": "img/pokemon/030800_128.png",
        "pokemonId": "030800",
        "leftTrainer": "Street Thug",
        "leftMon": "Annihilape",
        "leftIcon": "img/pokemon/097900_128.png",
        "rightTrainer": "Black Belt",
        "rightMon": "Gallade",
        "rightIcon": "img/pokemon/047500_128.png"
    },
    "Crasher Wake": {
        "pokemon": "Kingdra",
        "icon": "img/pokemon/023000_128.png",
        "pokemonId": "023000",
        "leftTrainer": "Swimmer",
        "leftMon": "Dracovish",
        "leftIcon": "img/pokemon/088200_128.png",
        "rightTrainer": "Swimmer",
        "rightMon": "Dracovish",
        "rightIcon": "img/pokemon/088200_128.png"
    },
    "Fantina": {
        "pokemon": "Mismagius",
        "icon": "img/pokemon/042900_128.png",
        "pokemonId": "042900",
        "leftTrainer": "Pokémon Ranger",
        "leftMon": "Drifblim",
        "leftIcon": "img/pokemon/042600_128.png",
        "rightTrainer": "Rising Star",
        "rightMon": "Gengar",
        "rightIcon": "img/pokemon/009400_128.png"
    },
    "Byron": {
        "pokemon": "Bastiodon",
        "icon": "img/pokemon/041100_128.png",
        "pokemonId": "041100",
        "leftTrainer": "Collector",
        "leftMon": "Probopass",
        "leftIcon": "img/pokemon/047600_128.png",
        "rightTrainer": "Hiker",
        "rightMon": "Steelix",
        "rightIcon": "img/pokemon/020801_128.png"
    },
    "Candice": {
        "pokemon": "Abomasnow",
        "icon": "img/pokemon/046000_128.png",
        "pokemonId": "046000",
        "leftTrainer": "Poké Fan",
        "leftMon": "Ninetales (Alola)",
        "leftIcon": "img/pokemon/003861_128.png",
        "rightTrainer": "Ace Trainer",
        "rightMon": "Ninetales (Alola)",
        "rightIcon": "img/pokemon/003861_128.png"
    },
    "Volkner": {
        "pokemon": "Luxray",
        "icon": "img/pokemon/040500_128.png",
        "pokemonId": "040500",
        "leftTrainer": "Ace Trainer",
        "leftMon": "Raichu",
        "leftIcon": "img/pokemon/002600_128.png",
        "rightTrainer": "Scientist",
        "rightMon": "Electivire",
        "rightIcon": "img/pokemon/046600_128.png"
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
            "pokemonId": "000000"
        })

        leader_slug = leader_name.lower().replace(" ", "_")
        fight_id = f"{current_league['leagueId']}_{leader_slug}"
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
                # Slot 0: Left
                current_fight["opponents"].append({
                    "slotIndex": 0,
                    "trainerName": info.get("leftTrainer", "Gym Minion"),
                    "pokemonName": info.get("leftMon", "Minion"),
                    "pokemonId": "000000",
                    "iconUrl": info.get("leftIcon", info.get("icon", "img/trainers/unknown.png")),
                    "weakness": w,
                    "hp": int(hp.replace(",", "")),
                    "atk": int(atk.replace(",", "")),
                    "def": int(df.replace(",", "")),
                    "spa": int(spa.replace(",", "")),
                    "spd": int(spd.replace(",", "")),
                    "spe": int(spe.replace(",", ""))
                })
                # Slot 2: Right
                current_fight["opponents"].append({
                    "slotIndex": 2,
                    "trainerName": info.get("rightTrainer", "Gym Minion"),
                    "pokemonName": info.get("rightMon", "Minion"),
                    "pokemonId": "000000",
                    "iconUrl": info.get("rightIcon", info.get("icon", "img/trainers/unknown.png")),
                    "weakness": w,
                    "hp": int(hp.replace(",", "")),
                    "atk": int(atk.replace(",", "")),
                    "def": int(df.replace(",", "")),
                    "spa": int(spa.replace(",", "")),
                    "spd": int(spd.replace(",", "")),
                    "spe": int(spe.replace(",", ""))
                })

for dest in ["src/BluesLab/wwwroot/data/gym_stages.json", "src/BluesLab/wwwroot/data/stages_manifest.json"]:
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(leagues_output, f, indent=2, ensure_ascii=False)
    print(f"Generated {dest} with {len(leagues_output)} circuits and {sum(len(l['fights']) for l in leagues_output)} fights!")
