import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

# Find all occurrences of data/sync-grids/ in sync-pairs.js
matches = set(re.findall(r'data/sync-grids/[^\'\"`\s<>]+', js))
print(f"Direct references to data/sync-grids/: {len(matches)}")
for m in sorted(matches):
    print(" ", m)

# Let us also search for how panelType and tileIcon are generated
idx = js.find("function setTileBackground(")
if idx != -1:
    print("\n--- setTileBackground context ---")
    print(js[max(0, idx-500):idx+1200])