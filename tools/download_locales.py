import os
import urllib.request
from pathlib import Path

LOCALES_DIR = Path("src/BluesLab/wwwroot/locales")
LOCALES_DIR.mkdir(parents=True, exist_ok=True)

langs = ["en", "es", "ja", "zh", "fr"]
files_to_fetch = []

for lang in langs:
    files_to_fetch.append(f"{lang}.json")
    files_to_fetch.append(f"common_{lang}.json")

for fn in files_to_fetch:
    out_file = LOCALES_DIR / fn
    if out_file.exists() and out_file.stat().st_size > 5000:
        print(f"Already exists: {fn} ({out_file.stat().st_size} bytes)")
        continue
    url = f"https://pomatools.site/locales/{fn}"
    print(f"Downloading {url} to {out_file}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        content = resp.read()
        with open(out_file, 'wb') as f:
            f.write(content)
    print(f"Saved {fn} ({len(content)} bytes)")
