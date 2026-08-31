import json, os, urllib.request

headers = {"User-Agent": "Mozilla/5.0"}
en = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/i18n/en.json", headers=headers)).read().decode("utf-8"))
champ_data = json.loads(open("src/BluesLab/wwwroot/data/champion.json", encoding="utf-8").read())

char_dict = en.get("DATA", {}).get("CHAR", {})
pkmn_dict = en.get("DATA", {}).get("PKMN", {})

league_names = {
    "1": "Kanto Challenge",
    "2": "Johto Challenge",
    "3": "Hoenn Challenge",
    "4": "Sinnoh Challenge",
    "5": "Unova Challenge",
    "6": "Kalos Challenge",
    "7": "Alola Challenge",
    "8": "Galar Challenge"
}

types_map = {
    1: "Normal", 2: "Fire", 3: "Water", 4: "Grass", 5: "Electric", 6: "Ice",
    7: "Fighting", 8: "Poison", 9: "Ground", 10: "Flying", 11: "Psychic", 12: "Bug",
    13: "Rock", 14: "Ghost", 15: "Dragon", 16: "Dark", 17: "Steel", 18: "Fairy"
}

leagues_output = []

for lid, fights in champ_data.get("leagues", {}).items():
    lname = league_names.get(str(lid), f"League {lid}")
    league_obj = {
        "leagueId": str(lid),
        "name": lname,
        "fights": []
    }

    for f_idx, f in enumerate(fights):
        teams = f.get("teams", [])
        if len(teams) < 3:
            continue

        # teams[0]=Center, teams[1]=Left, teams[2]=Right
        center_t = teams[0]
        c_tid = center_t.get("trainerId", "")
        c_pkm = center_t.get("pokemon", [{}])[0]
        c_pkmid = c_pkm.get("pokemonId", "")
        t_name = char_dict.get(c_tid, f"Trainer #{c_tid}")
        p_name = pkmn_dict.get(c_pkmid, f"Pokemon #{c_pkmid}")
        weak_id = center_t.get("weakness", 1)
        weak_str = types_map.get(weak_id, "Normal")

        fight_title = f"vs. {t_name} & {p_name} ({weak_str}-weak)"

        opponents = []
        # Order: 0=Left (teams[1]), 1=Center (teams[0]), 2=Right (teams[2])
        for slot_idx, t in enumerate([teams[1], teams[0], teams[2]]):
            tid = t.get("trainerId", "")
            pkm = t.get("pokemon", [{}])[0]
            pkmid = pkm.get("pokemonId", "")
            stats_raw = pkm.get("stats", [2000, 60, 100, 60, 100, 300]) # HP, Atk, Def, SpA, SpD, Spe
            w_id = t.get("weakness", 1)

            opponents.append({
                "slotIndex": slot_idx, # 0=Left, 1=Center, 2=Right
                "trainerName": char_dict.get(tid, f"Trainer #{tid}"),
                "pokemonName": pkmn_dict.get(pkmid, f"Pokemon #{pkmid}"),
                "pokemonId": pkmid,
                "iconUrl": f"img/pokemon/{pkmid}_128.png",
                "weakness": types_map.get(w_id, "Normal"),
                "hp": stats_raw[0] if len(stats_raw) > 0 else 2000,
                "atk": stats_raw[1] if len(stats_raw) > 1 else 60,
                "def": stats_raw[2] if len(stats_raw) > 2 else 100,
                "spa": stats_raw[3] if len(stats_raw) > 3 else 60,
                "spd": stats_raw[4] if len(stats_raw) > 4 else 100,
                "spe": stats_raw[5] if len(stats_raw) > 5 else 300
            })

        league_obj["fights"].append({
            "fightId": f"{lid}_{f_idx}",
            "title": fight_title,
            "opponents": opponents
        })

    leagues_output.append(league_obj)

dest = "src/BluesLab/wwwroot/data/stages_manifest.json"
open(dest, "w", encoding="utf-8").write(json.dumps(leagues_output, indent=2, ensure_ascii=False))
print(f"Generated {dest} with {len(leagues_output)} leagues and {sum(len(l['fights']) for l in leagues_output)} fights!")