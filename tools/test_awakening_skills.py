import urllib.request, json, sys

sys.stdout.reconfigure(encoding="utf-8")
en = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/i18n/en.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))

count = 0
for p in poma_pairs:
    askill = p.get("awakeningSkill", 0)
    if askill > 0:
        count += 1
        name = en["DATA"]["SKILLS"].get(str(askill), f"Skill #{askill}")
        if count <= 10:
            print(f"Pair {p.get('id')} ({p.get('trainerId')}): awakeningSkill={askill} -> {name}")

print(f"\nTotal SA pairs in PoMaTools with awakeningSkill > 0: {count}")