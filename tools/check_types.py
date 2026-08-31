import urllib.request

url = "https://pokemon.brybry.ch/masters/js/sync-pairs.js"
js = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")
idx = js.find('gVisual.setAttribute("data-type"')
if idx != -1:
    print(js[max(0, idx-100):idx+250])