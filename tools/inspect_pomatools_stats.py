import urllib.request
import re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req).read().decode("utf-8")

idx = content.find("_getUserOffenses(")
if idx != -1:
    print("Found _getUserOffenses:")
    print(content[idx-200:idx+1500])

idx2 = content.find("recalculateBaseStat(")
if idx2 != -1:
    print("\nFound recalculateBaseStat:")
    print(content[idx2-200:idx2+1500])