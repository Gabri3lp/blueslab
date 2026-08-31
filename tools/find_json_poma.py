import urllib.request, re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

jsons = set(re.findall(r'[\'\"`][^\'\"`]*?\.json[\'\"`]', content))
for j in sorted(jsons):
    print(" ", j)