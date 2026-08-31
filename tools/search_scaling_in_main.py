import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'Gorging Crunch|Almighty Obsidian|Explosive Mystical|Nihil Meteor|B Fleur Cannon|B Thunderbolt|B Volt Tackle', js, re.I)]
print("Total occurrences of famous unique moves:", len(matches))
for idx in matches:
    print("--- SNIPPET ---")
    print(js[max(0, idx-100):min(len(js), idx+500)])