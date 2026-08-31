import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

idx = js.find("function setTileBackground(")
if idx != -1:
    print("=== setTileBackground ===")
    print(js[idx:idx+2500])

idx2 = js.find("function setGridPicker(")
if idx2 != -1:
    print("\n=== setGridPicker ===")
    print(js[idx2:idx2+3000])