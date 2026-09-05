import json, os, urllib.request, shutil

manifest_path = "src/BluesLab/wwwroot/data/pairs_manifest.json"
trainers_dir = "src/BluesLab/wwwroot/img/trainers"
output_trainers_dir = "output/wwwroot/img/trainers"
os.makedirs(trainers_dir, exist_ok=True)
os.makedirs(output_trainers_dir, exist_ok=True)

manifest = json.loads(open(manifest_path, encoding="utf-8").read())
headers = {"User-Agent": "Mozilla/5.0"}

# Load pomatools sync meta list
poma_url = "https://pomatools.site/data/sync_meta_list.json"
req = urllib.request.Request(poma_url, headers=headers)
poma_meta = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

downloaded = 0
for p in manifest:
    icon_url = p.get("iconUrl", "")
    if not icon_url:
        continue
    fname = os.path.basename(icon_url)
    dest = os.path.join(trainers_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        continue
    
    tid = str(p.get("trainerId", ""))
    meta = poma_meta.get(tid, {}).get("meta", {})
    actor = meta.get("actorId")
    if not actor:
        print(f"Skipping {tid}: no actorId found")
        continue

    img_url = f"https://pomatools.site/assets/trainer/{actor}_128.png"
    try:
        req_img = urllib.request.Request(img_url, headers=headers)
        with urllib.request.urlopen(req_img, timeout=10) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        
        # Also copy to output if directory exists
        if os.path.exists(output_trainers_dir):
            shutil.copy2(dest, os.path.join(output_trainers_dir, fname))
            
        print(f"Downloaded: {fname} ({p.get('trainerName')} & {p.get('monsterName')})")
        downloaded += 1
    except Exception as e:
        print(f"Failed {fname}: {e}")

print(f"Done. Downloaded {downloaded} missing trainer icons.")
