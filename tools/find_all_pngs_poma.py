import urllib.request, re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

pngs = set(re.findall(r'[\'\"`][^\'\"`]*?\.png[\'\"`]', content))
print(f"Total distinct PNG references: {len(pngs)}")
for p in sorted(pngs):
    if any(k in p.lower() for k in ["tile", "grid", "pokemon", "trainer", "battle", "star", "type"]):
        print(" ", p)