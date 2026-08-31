import urllib.request

req_headers = {"User-Agent": "Mozilla/5.0"}
test_urls = [
    "https://pomatools.github.io/assets/img/grid/tile_0.png",
    "https://pomatools.github.io/assets/img/grid/tile_1.png",
    "https://pomatools.github.io/assets/img/grid/stat.png",
    "https://pomatools.github.io/assets/img/grid/move.png",
    "https://pomatools.github.io/assets/img/grid/skill.png",
    "https://pomatools.github.io/assets/img/grid/sync.png",
    "https://pomatools.github.io/assets/img/battle/stat_atk.png",
    "https://pomatools.github.io/assets/img/battle/stat_spa.png",
    "https://pomatools.github.io/assets/img/battle/stat_def.png",
    "https://pomatools.github.io/assets/img/battle/stat_spd.png",
    "https://pomatools.github.io/assets/img/battle/stat_spe.png",
    "https://pomatools.github.io/assets/img/battle/stat_hp.png",
]

for url in test_urls:
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"200 OK: {url} ({resp.length} bytes)")
    except Exception as e:
        print(f"404/ERR: {url} ({e})")