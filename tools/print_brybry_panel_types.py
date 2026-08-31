import urllib.request

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

idx = js.find("switch (panel.ability.type)")
if idx != -1:
    print(js[idx:idx+2500])