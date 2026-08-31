import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'calcMovePower|calcBasePower|minDamage|maxDamage|avgDamage|damageTable|calcDamage', js, re.I)]
print("Total matches found:", len(matches))
for idx in matches[:10]:
    print("--- SNIPPET ---")
    print(js[max(0, idx-50):min(len(js), idx+300)])