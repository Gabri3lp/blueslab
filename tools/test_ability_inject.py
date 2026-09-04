import glob
import json
import urllib.request
from pathlib import Path

panel_url = "https://pokemon.brybry.ch/masters/data/proto/AbilityPanel.json"
panel_data = json.loads(urllib.request.urlopen(urllib.request.Request(panel_url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8'))
panel_map = {p['cellId']: p['abilityId'] for p in panel_data.get('entries', []) if 'cellId' in p and 'abilityId' in p}

pairs_dir = "src/BluesLab/wwwroot/data/pairs"
files = glob.glob(f"{pairs_dir}/*.json")
print(f"Total pair files: {len(files)}")

# Check sample
with open(files[0], 'r', encoding='utf-8-sig') as f:
    sample = json.load(f)
print("Sample cell before:", sample['grid'][0])
sample['grid'][0]['abilityId'] = panel_map.get(sample['grid'][0]['cellId'], 0)
print("Sample cell after:", sample['grid'][0])
