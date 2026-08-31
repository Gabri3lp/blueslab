import json, glob, urllib.request

pairs_dir = "src/BluesLab/wwwroot/data/pairs"
sample_files = glob.glob(f"{pairs_dir}/*.json")
print(f"Total pair JSON files: {len(sample_files)}")

sa_pairs = 0
has_sa_skill_field = 0
for f in sample_files:
    try:
        data = json.loads(open(f, encoding="utf-8").read())
        if data.get("hasSuperAwakening"):
            sa_pairs += 1
            if "awakeningSkill" in data or "superAwakeningPassive" in data or "awakeningPassive" in data:
                has_sa_skill_field += 1
    except Exception:
        pass

print(f"Sync pairs with hasSuperAwakening: {sa_pairs}")
print(f"Sync pairs with awakening skill field: {has_sa_skill_field}")

# Let us check PoMaTools pairs.json for awakeningSkill
poma_pairs = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/pairs.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))
poma_skills = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/skills.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))
poma_es = json.loads(urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/assets/data/es.json", headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8"))

sa_with_skill = 0
sample_sa = []
for p in poma_pairs:
    askill = p.get("awakeningSkill", 0)
    if askill > 0 or p.get("dateAwakening", -1) != -1:
        sa_with_skill += 1
        skill_name = poma_es.get("MSGS.SKILLS", {}).get(f"SKILL_{str(askill).padStart(8, '0')}", "") if hasattr(str(askill), 'padStart') else ""
        sample_sa.append({
            "id": p.get("id"),
            "trainerId": p.get("trainerId"),
            "awakeningSkill": askill,
        })

print(f"PoMaTools pairs with awakeningSkill > 0 or dateAwakening: {sa_with_skill}")
print("Sample PoMaTools SA pairs:", sample_sa[:5])