import os
import glob
import json
import urllib.request
from datetime import datetime, timezone

BASE_PROTO_URL = "https://pokemon.brybry.ch/masters/data/proto"

def fetch_proto(name):
    print(f"Fetching {name}.json...")
    req = urllib.request.Request(f"{BASE_PROTO_URL}/{name}.json", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))['entries']

def main():
    print("=== BluesLab: Enriching Release Dates ===")

    trainers = {str(t['trainerId']): t for t in fetch_proto("Trainer")}
    schedules = {s['scheduleId']: s for s in fetch_proto("Schedule")}
    item_exchanges = fetch_proto("ItemExchange")

    manifest_path = os.path.join("src", "BluesLab", "wwwroot", "data", "pairs_manifest.json")
    pairs_dir = os.path.join("src", "BluesLab", "wwwroot", "data", "pairs")

    with open(manifest_path, "r", encoding="utf-8-sig") as f:
        manifest = json.load(f)

    # Precompute earliest timestamp for update prefixes
    prefix_dates = {}
    for pfx in ['3050', '4080', '7010']:
        matching = [int(s['startDate']) for s in schedules.values() if pfx in s['scheduleId'] and int(s['startDate']) > 0]
        if matching:
            prefix_dates[pfx] = min(matching)

    LAUNCH_DATE = 1567036800  # 2019-08-29 00:00:00 UTC (Global launch)

    # Date resolution map: trainerId -> (releaseTimestamp, releaseDate)
    date_map = {}

    for p in manifest:
        tid = str(p['trainerId'])
        t = trainers.get(tid, {})
        sid = t.get('scheduleId')
        sch = schedules.get(sid, {})
        ts = int(sch.get('startDate', 0))

        if ts == 0:
            # Check ItemExchange
            for ie in item_exchanges:
                if str(ie.get('itemId')) in [tid, f"180{tid}"]:
                    ie_sid = ie.get('scheduleId')
                    ie_sch = schedules.get(ie_sid, {})
                    ie_ts = int(ie_sch.get('startDate', 0))
                    if ie_ts > 0:
                        ts = ie_ts
                        break
                    # Check itemSetId prefix
                    item_set = str(ie.get('itemSetId', ''))
                    for pfx, pfx_ts in prefix_dates.items():
                        if item_set.startswith(pfx):
                            ts = pfx_ts
                            break
                    if ts > 0:
                        break

        if ts < LAUNCH_DATE:
            ts = LAUNCH_DATE

        dt_str = datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d')
        date_map[tid] = (ts, dt_str)

    print(f"Resolved release dates for {len(date_map)} pairs.")

    # Update manifest items
    for p in manifest:
        tid = str(p['trainerId'])
        ts, dt_str = date_map.get(tid, (LAUNCH_DATE, "2019-08-29"))
        p['releaseTimestamp'] = ts
        p['releaseDate'] = dt_str

    # Sort manifest by releaseTimestamp descending, then by displayName
    manifest.sort(key=lambda x: (-x['releaseTimestamp'], x['displayName']))

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Updated and sorted {manifest_path} (newest pair first: {manifest[0]['displayName']} - {manifest[0]['releaseDate']})")

    # Update individual pair json files
    updated_files = 0
    pair_files = glob.glob(os.path.join(pairs_dir, "*.json"))
    for pf in pair_files:
        tid = os.path.splitext(os.path.basename(pf))[0]
        if tid in date_map:
            ts, dt_str = date_map[tid]
            with open(pf, "r", encoding="utf-8-sig") as f:
                pair_data = json.load(f)
            pair_data['releaseTimestamp'] = ts
            pair_data['releaseDate'] = dt_str
            with open(pf, "w", encoding="utf-8") as f:
                json.dump(pair_data, f, indent=2, ensure_ascii=False)
            updated_files += 1

    print(f"Updated {updated_files} pair detail files with releaseDate and releaseTimestamp.")
    print("=== Done! ===")

if __name__ == "__main__":
    main()
