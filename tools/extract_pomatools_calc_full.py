import urllib.request
import re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req).read().decode("utf-8")

# Find index of `calculate(){`
idx = content.find("calculate(){if(!this.damageForm.valid)return;")
if idx != -1:
    start = max(0, idx - 1000)
    end = min(len(content), idx + 8000)
    code = content[start:end]
    with open("tools/pomatools_calc_snippet.js", "w", encoding="utf-8") as f:
        f.write(code)
    print("Saved pomatools_calc_snippet.js")
else:
    print("calculate() not found directly")