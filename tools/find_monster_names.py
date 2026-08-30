import urllib.request, json

req_headers = {"User-Agent": "Mozilla/5.0"}
for url in [
    "https://pokemon.brybry.ch/masters/data/lsd/monster_name_en.json",
    "https://pokemon.brybry.ch/masters/data/lsd/pokemon_name_en.json",
    "https://pokemon.brybry.ch/masters/data/proto/Monster.json"
]:
    try:
        req = urllib.request.Request(url, headers=req_headers)
        data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        print(f"FOUND: {url} -> type: {type(data)}, length: {len(data)}")
        if isinstance(data, dict):
            print("  sample keys:", list(data.items())[:5])
        elif isinstance(data, list) and len(data) > 0:
            print("  sample:", data[0])
    except Exception as e:
        print(f"FAILED {url}: {e}")