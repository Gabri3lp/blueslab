import urllib.request, re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'calcMoveDamage|calculateDamage|_calculateDamage|calcSyncDamage', content)]
print("Total occurrences found:", len(matches))
for idx in matches:
    print("--- SNIPPET ---")
    print(content[max(0, idx-50):min(len(content), idx+500)])