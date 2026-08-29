import urllib.request
import re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req).read().decode("utf-8")

# Search for how pokemon variations/forms are calculated in PoMaTools
idx = content.find(".statFunctions[")
if idx != -1:
    print("Found statFunctions:")
    print(content[idx-300:idx+700])

idx2 = content.find("calculateBattleStat(")
if idx2 != -1:
    print("\nFound calculateBattleStat:")
    print(content[idx2-200:idx2+600])