import urllib.request, re, json

headers = {"User-Agent": "Mozilla/5.0"}

# Let us fetch the pair page on brybry.ch for Red or Wally or any character
# e.g. https://pokemon.brybry.ch/masters/duo.html?id=10128100000 or similar
for url in [
    "https://pokemon.brybry.ch/masters/duo.html",
    "https://pokemon.brybry.ch/masters/index.html",
    "https://pokemon.brybry.ch/masters/plateau.html",
    "https://pokemon.brybry.ch/masters/grid.html",
    "https://pokemon.brybry.ch/masters/duos.html",
]:
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=5).read().decode("utf-8", errors="ignore")
        print(f"FOUND: {url} -> len: {len(html)}")
        # find all scripts
        scripts = re.findall(r'<script\s+[^>]*src=[\"\']([^\"\']+)[\"\']', html)
        print("  scripts:", scripts)
    except Exception as e:
        print(f"ERR {url}: {e}")