import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'icon-layer|bg-layer|overlay-layer', js)]
print(f"Total layer occurrences: {len(matches)}")
for idx in matches:
    print("--- SNIPPET ---")
    print(js[max(0, idx-100):min(len(js), idx+500)])