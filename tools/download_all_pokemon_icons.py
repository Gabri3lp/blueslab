import json, os, urllib.request, glob, time

pokemon_dir = "src/BluesLab/wwwroot/img/pokemon"
pairs_dir = "src/BluesLab/wwwroot/data/pairs"
os.makedirs(pokemon_dir, exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0"}

seen = set()
ok = 0
fail = 0

for f in sorted(glob.glob(f"{pairs_dir}/*.json")):
    try:
        data = json.loads(open(f, encoding="utf-8").read())
        pkm_icon = data.get("pokemonIconUrl", "")
        if not pkm_icon:
            continue
        filename = pkm_icon.split("/")[-1] # e.g. 028200_128.png
        if filename in seen:
            continue
        seen.add(filename)
        dest = os.path.join(pokemon_dir, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 500:
            ok += 1
            continue
        url = f"https://pomatools.github.io/assets/img/pokemon/{filename}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                open(dest, "wb").write(r.read())
            ok += 1
        except Exception as e:
            fail += 1
        time.sleep(0.01)
    except Exception as e:
        pass

print(f"Downloaded Pokemon icons: {ok} ok, {fail} failed")