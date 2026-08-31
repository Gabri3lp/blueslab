import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

idx = js.find("createElementNS(\"http://www.w3.org/2000/svg\"")
if idx != -1:
    print("--- SVG creation snippet ---")
    print(js[idx:idx+3500])