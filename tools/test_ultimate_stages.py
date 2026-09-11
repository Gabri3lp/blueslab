import json
import os

path = "src/BluesLab/wwwroot/data/ultimate_stages.json"
assert os.path.exists(path), f"File {path} not found"

with open(path, "r", encoding="utf-8") as f:
    stages = json.load(f)

print(f"Total Ultimate Battles loaded: {len(stages)}")
assert len(stages) == 18, f"Expected 18 stages, got {len(stages)}"

for stg in stages:
    fid = stg["fightId"]
    title = stg["title"]
    opps = stg["opponents"]
    rules = stg["rules"]
    print(f"[{fid}] {title} - {len(opps)} opponents, {len(rules)} rules")
    
    assert len(opps) >= 1, f"Stage {fid} has no opponents"
    center = next((o for o in opps if o["slotIndex"] == 1), None)
    assert center is not None, f"Stage {fid} has no center opponent"
    assert center["hp"] > 0, f"Stage {fid} center has 0 HP"
    assert center["atk"] > 0, f"Stage {fid} center has 0 Atk"
    assert center["def"] > 0, f"Stage {fid} center has 0 Def"
    assert center["spa"] > 0, f"Stage {fid} center has 0 SpA"
    assert center["spd"] > 0, f"Stage {fid} center has 0 SpD"
    assert len(center["weakness"]) > 0, f"Stage {fid} center has empty weakness"

# Specific check for Anabel
anabel = next(s for s in stages if "anabel" in s["fightId"])
anabel_center = next(o for o in anabel["opponents"] if o["slotIndex"] == 1)
assert any(p["name"] == "Fluid Fortification" for p in anabel_center["passives"]), "Anabel missing Fluid Fortification"
assert anabel_center["mitigations"]["def"] == 3, f"Expected Anabel def mitigation 3, got {anabel_center['mitigations']['def']}"

# Specific check for Thorton
thorton = next(s for s in stages if "thorton" in s["fightId"])
thorton_center = next(o for o in thorton["opponents"] if o["slotIndex"] == 1)
assert any("No Negative Status Change" in p["name"] for p in thorton_center["passives"]), "Thorton missing No Negative Status Change"

print("All automated verification checks passed successfully!")
