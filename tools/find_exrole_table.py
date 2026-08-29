import urllib.request, json

proto_names = [
    "Trainer", "TrainerExRole", "ExRole", "ExRoleReward", "ExRoleStatusUp",
    "ActorTrainer", "Monster", "MonsterVariation", "AbilityPanel",
    "SpecialAwakingEffect", "TrainerSpecialAwaking", "Schedule",
    "TrainerRoleEx", "RoleEx", "ExRoleItem"
]

req_headers = {"User-Agent": "Mozilla/5.0"}
for name in proto_names:
    url = f"https://pokemon.brybry.ch/masters/data/proto/{name}.json"
    try:
        req = urllib.request.Request(url, headers=req_headers)
        data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        entries = data.get("entries", [])
        print(f"[FOUND] {name}: {len(entries)} entries")
        if entries:
            print("   Sample:", entries[0])
    except Exception as err:
        pass