import json

test_keys = [
    "trainer_name_10007400000",
    "trainer_name_ch0000",
    "pokemon_name_20081911",
    "move_name_421",
    "move_desc_421",
    "passive_name_17042409",
    "passive_desc_17042409",
    "tile_name_1100000010",
    "tile_name_1802010100000",
    "tile_desc_1802010100000"
]

for lang in ["en", "es", "ja", "zh", "fr"]:
    with open(f"src/BluesLab/wwwroot/locales/{lang}.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"=== Language: {lang} ===")
    for k in test_keys:
        val = d.get(k)
        print(f"  {k} -> {repr(val)[:60]}")
