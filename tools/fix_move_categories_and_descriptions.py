import json, os, glob, urllib.request, re

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def clean_lsd_text(text):
    if not text:
        return ""
    
    # Handle [EN:Qty ...]
    def replace_qty(m):
        content = m.group(1)
        p_match = re.search(r'P="([^"]+)"', content)
        s_match = re.search(r'S="([^"]+)"', content)
        if p_match:
            return p_match.group(1)
        if s_match:
            return s_match.group(1)
        return ""

    text = re.sub(r'\[EN:Qty\s+([^\]]+)\]', replace_qty, text)
    # Handle [Digit:...]
    text = re.sub(r'\[Digit:\d*digits?[^\]]*\]', '', text)
    # Handle [Name:...]
    text = re.sub(r'\[Name:PokemonName[^\]]*\]', 'Pokémon', text)
    text = re.sub(r'\[Name:TrainerName[^\]]*\]', 'Trainer', text)
    text = re.sub(r'\[Name:[^\]]+\]', '', text)
    # Remove any other remaining bracketed template tags
    text = re.sub(r'\[[^\]]+\]', '', text)
    # Remove double spaces
    text = re.sub(r'\s{2,}', ' ', text)
    # Fix punctuation spacing e.g. "by ranks ." -> "by ranks."
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    return text.strip()

def main():
    print("1. Fetching Move.json proto...")
    move_proto = fetch_json("https://pokemon.brybry.ch/masters/data/proto/Move.json")
    move_map = {m.get("moveId"): m for m in move_proto.get("entries", [])}
    print(f"   Loaded {len(move_map)} moves from proto.")

    pairs_dir = "src/BluesLab/wwwroot/data/pairs"
    files = glob.glob(f"{pairs_dir}/*.json")
    print(f"2. Updating {len(files)} pair JSON files...")

    updated_count = 0
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        changed = False

        # Update moves
        for m in data.get("moves", []):
            mid = m.get("id")
            if mid in move_map:
                proto_mv = move_map[mid]
                cat = proto_mv.get("category")
                if cat in ["Physical", "Special", "Status"]:
                    if m.get("category") != cat:
                        m["category"] = cat
                        changed = True
                
                gd = proto_mv.get("gaugeDrain")
                if gd is not None:
                    m["gauge"] = str(gd)
                    changed = True
                
                tgt = proto_mv.get("target")
                if tgt:
                    tgt_name = "An opponent" if tgt == "OpponentSingle" else ("All opponents" if tgt == "OpponentAll" else ("Self" if tgt == "Self" else ("All allies" if tgt == "AllyAll" else "An ally")))
                    m["target"] = tgt_name
                    changed = True

            # Clean description
            orig_desc = m.get("description", "")
            cleaned_desc = clean_lsd_text(orig_desc)
            if cleaned_desc != orig_desc:
                m["description"] = cleaned_desc
                changed = True

        # Update passives
        for p in data.get("passives", []):
            orig_desc = p.get("description", "")
            cleaned_desc = clean_lsd_text(orig_desc)
            if cleaned_desc != orig_desc:
                p["description"] = cleaned_desc
                changed = True
            
            for cp in p.get("childPassives", []):
                cp_orig = cp.get("description", "")
                cp_cleaned = clean_lsd_text(cp_orig)
                if cp_cleaned != cp_orig:
                    cp["description"] = cp_cleaned
                    changed = True

        if changed:
            with open(f, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
            updated_count += 1

    print(f"Done! Updated {updated_count} files.")

if __name__ == "__main__":
    main()