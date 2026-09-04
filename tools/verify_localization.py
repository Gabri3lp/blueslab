import json
import glob
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== VERIFYING LOCALIZATION SYSTEM ===")

# 1. Check all locale files exist and are valid JSON
locales_dir = "src/BluesLab/wwwroot/locales"
langs = ["es", "en", "ja", "zh", "fr"]

for lang in langs:
    common_f = os.path.join(locales_dir, f"common_{lang}.json")
    data_f = os.path.join(locales_dir, f"{lang}.json")
    assert os.path.exists(common_f), f"Missing {common_f}"
    assert os.path.exists(data_f), f"Missing {data_f}"
    
    with open(common_f, 'r', encoding='utf-8') as cf:
        c_dict = json.load(cf)
    with open(data_f, 'r', encoding='utf-8') as df:
        d_dict = json.load(df)
    
    print(f"[{lang}] OK: common_{lang}.json ({len(c_dict)} keys), {lang}.json ({len(d_dict)} keys)")

# 2. Check manifest
manifest_f = "src/BluesLab/wwwroot/data/pairs_manifest.json"
with open(manifest_f, 'r', encoding='utf-8') as mf:
    manifest = json.load(mf)

assert len(manifest) >= 660, f"Expected 660 pairs, got {len(manifest)}"
for p in manifest:
    assert 'trainerKey' in p, f"Missing trainerKey for {p.get('trainerId')}"
    assert 'pokemonKey' in p, f"Missing pokemonKey for {p.get('trainerId')}"
print(f"[Manifest] OK: {len(manifest)} pairs verified with trainerKey and pokemonKey.")

# 3. Check pairs grid abilityIds
pairs_dir = "src/BluesLab/wwwroot/data/pairs"
pair_files = glob.glob(f"{pairs_dir}/*.json")
total_cells = 0
cells_with_ability = 0

for pf in pair_files:
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for cell in data.get('grid', []):
        total_cells += 1
        if 'abilityId' in cell and int(cell['abilityId']) > 0:
            cells_with_ability += 1

print(f"[Grid Cells] OK: {cells_with_ability} / {total_cells} cells have valid abilityId.")
assert cells_with_ability == total_cells, "All cells must have abilityId!"

# 4. Spot check translations across languages
with open(os.path.join(locales_dir, "es.json"), 'r', encoding='utf-8') as f:
    es = json.load(f)
with open(os.path.join(locales_dir, "en.json"), 'r', encoding='utf-8') as f:
    en = json.load(f)

# Acerola Fall 2020 & Mimikyu
print("\n=== Sample Translations (EN vs ES) ===")
print("Trainer (Acerola Fall 2020):")
print("  EN:", en.get("trainer_name_10007400000"))
print("  ES:", es.get("trainer_name_10007400000"))

print("Trainer (Red Base):")
print("  EN:", en.get("trainer_name_ch0000"))
print("  ES:", es.get("trainer_name_ch0000"))

print("Move (Shadow Claw / Garra Umbría - 421):")
print("  EN:", en.get("move_name_421"), "->", en.get("move_desc_421"))
print("  ES:", es.get("move_name_421"), "->", es.get("move_desc_421"))

print("Passive (Criticonfuse 9 - 17042409):")
print("  EN:", en.get("passive_name_17042409"), "->", en.get("passive_desc_17042409"))
print("  ES:", es.get("passive_name_17042409"), "->", es.get("passive_desc_17042409"))

print("Grid Tile (Headstrong - 1802010100000):")
print("  EN:", en.get("tile_name_1802010100000"), "->", en.get("tile_desc_1802010100000"))
print("  ES:", es.get("tile_name_1802010100000"), "->", es.get("tile_desc_1802010100000"))

print("\n=== ALL LOCALIZATION CHECKS PASSED SUCCESSFULLY! ===")
