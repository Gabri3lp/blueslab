import urllib.request, json

req = urllib.request.Request("https://pomatools.github.io/data/pairs.json", headers={"User-Agent": "Mozilla/5.0"})
try:
    data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    print("Total pairs in PoMaTools:", len(data))
    for p in data[:5]:
        print(p.get("id"), p.get("trainerId"), p.get("pokemon"))
except Exception as e:
    print("Err:", e)