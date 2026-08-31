import urllib.request, json, os

headers = {"User-Agent": "Mozilla/5.0"}
dest_dir = "src/BluesLab/wwwroot/data"
os.makedirs(dest_dir, exist_ok=True)

for name in ["champion.json", "battlerally.json"]:
    url = f"https://pomatools.github.io/assets/data/{name}"
    dest = os.path.join(dest_dir, name)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            open(dest, "wb").write(r.read())
        print(f"Downloaded {name}: {os.path.getsize(dest)} bytes")
    except Exception as e:
        print(f"Err {name}: {e}")