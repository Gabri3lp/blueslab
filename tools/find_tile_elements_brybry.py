import urllib.request

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

idx = js.find("allPanels.forEach(panel =>")
if idx == -1:
    idx = js.find("ap.forEach(panel =>")
    if idx != -1:
        idx = js.find("allPanels.forEach", idx)

if idx != -1:
    print("--- allPanels.forEach snippet ---")
    print(js[idx:idx+4000])
else:
    print("Not found, searching for bg-layer")
    idx = js.find("bg-layer")
    print(js[max(0, idx-500):idx+1000])