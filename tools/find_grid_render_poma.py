import urllib.request, re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'polygon|clipPath|fill=\"url|grid-tile|sync-tile|<image|<text', content)]
print("Total matches:", len(matches))
for idx in matches[:15]:
    print("--- SNIPPET ---")
    print(content[max(0, idx-50):min(len(content), idx+300)])