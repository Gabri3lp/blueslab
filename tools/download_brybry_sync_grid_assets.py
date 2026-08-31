import os, urllib.request

base_url = "https://pokemon.brybry.ch/masters/data/sync-grids"
headers = {"User-Agent": "Mozilla/5.0"}

dest_dir = "src/BluesLab/wwwroot/data/sync-grids"
icons_dest_dir = "src/BluesLab/wwwroot/data/sync-grids/icons"
os.makedirs(dest_dir, exist_ok=True)
os.makedirs(icons_dest_dir, exist_ok=True)

panel_types = [
    "statsup", "passiveskill", "moveeffect", "syncmove", "maxmove",
    "movepowerup", "learnmove", "arceuspanel", "center"
]

images_to_download = [
    "center.png",
    "selected-overlay.png",
]

for pt in panel_types:
    images_to_download.append(f"{pt}.png")
    images_to_download.append(f"{pt}-selected.png")

icon_types = [
    "statsup", "passiveskill", "moveeffect", "syncmove", "maxmove", "learnmove",
    "locked-2", "locked-3", "locked-4", "locked-5", "transcendance"
]
for i in range(1, 19):
    icon_types.append(f"movepowerup-{i}")

icons_to_download = []
for it in icon_types:
    icons_to_download.append(f"{it}.png")
    icons_to_download.append(f"{it}-selected.png")

ok = 0
fail = 0

for img in images_to_download:
    url = f"{base_url}/{img}"
    dest = os.path.join(dest_dir, img)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            open(dest, "wb").write(r.read())
        print(f"200 OK: {img}")
        ok += 1
    except Exception as e:
        print(f"ERR: {img} -> {e}")
        fail += 1

for icon in icons_to_download:
    url = f"{base_url}/icons/{icon}"
    dest = os.path.join(icons_dest_dir, icon)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            open(dest, "wb").write(r.read())
        print(f"200 OK icon: {icon}")
        ok += 1
    except Exception as e:
        print(f"ERR icon: {icon} -> {e}")
        fail += 1

print(f"\nCompleted sync-grid assets download: {ok} succeeded, {fail} failed.")