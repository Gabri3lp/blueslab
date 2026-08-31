import urllib.request

req_headers = {"User-Agent": "Mozilla/5.0"}
# Wally's pokemon: 20028200 (Gardevoir) or 21028200 or 20128100000
test_urls = [
    "https://pomatools.github.io/assets/img/pokemon/20028200_128.png",
    "https://pomatools.github.io/assets/img/pokemon/21028200_128.png",
    "https://pomatools.github.io/assets/img/pokemon/20000600_128.png", # Charizard
    "https://pomatools.github.io/assets/img/pokemon/20002500_128.png", # Pikachu
    "https://pokemon.brybry.ch/masters/img/pokemon/20028200.png",
    "https://pokemon.brybry.ch/masters/img/pokemon/20000600.png",
]

for url in test_urls:
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            print(f"200 OK: {url} ({resp.length} bytes)")
    except Exception as e:
        print(f"ERR: {url} ({e})")