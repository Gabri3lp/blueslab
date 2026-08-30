import urllib.request, re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

matches = [m.start() for m in re.finditer(r'statFunctions\[', content)]
for idx in matches:
    print("--- assign/use ---")
    print(content[max(0, idx-100):min(len(content), idx+250)])