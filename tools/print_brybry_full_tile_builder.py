import urllib.request

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode("utf-8")

idx = js.find('bgImg.setAttribute("width", "69")')
if idx != -1:
    print(js[max(0, idx-600):min(len(js), idx+2500)])