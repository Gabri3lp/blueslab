import os
import sys
import json
import glob
import re
from pathlib import Path
from datetime import datetime

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).parent.parent
LOCALES_DIR = ROOT_DIR / "src" / "BluesLab" / "wwwroot" / "locales"
DATA_DIR = ROOT_DIR / "src" / "BluesLab" / "wwwroot" / "data"
PAIRS_DIR = DATA_DIR / "pairs"
MANIFEST_FILE = DATA_DIR / "pairs_manifest.json"
LOG_FILE = ROOT_DIR / "tools" / "diff_audit.log"

LANGS = ["es", "en", "fr", "ja", "zh"]

def load_locale_dict(lang):
    merged = {}
    common_file = LOCALES_DIR / f"common_{lang}.json"
    data_file = LOCALES_DIR / f"{lang}.json"
    
    if common_file.exists():
        with open(common_file, "r", encoding="utf-8") as f:
            merged.update(json.load(f))
            
    if data_file.exists():
        with open(data_file, "r", encoding="utf-8") as f:
            merged.update(json.load(f))
            
    return merged

def clean_tags(text):
    if not text:
        return ""
    return re.sub(r'\[[^\]]+\]', '', text).strip()

def resolve_trainer_name(loc_dict, trainer_id, trainer_key, trainer_base_id):
    candidates = [
        f"trainer_name_{trainer_key}" if trainer_key else None,
        f"trainer_name_{trainer_id}" if trainer_id else None,
        f"trainer_name_{trainer_base_id}" if trainer_base_id else None,
        f"trainer_name_ch{int(trainer_base_id):04d}" if trainer_base_id and trainer_base_id.isdigit() else None
    ]
    for k in candidates:
        if k and k in loc_dict and loc_dict[k].strip():
            return clean_tags(loc_dict[k])
    return None

def resolve_pokemon_name(loc_dict, monster_base_id, pokemon_key):
    mb = str(monster_base_id)
    candidates = [
        f"pokemon_name_{pokemon_key}" if pokemon_key else None,
        f"pokemon_name_{mb}" if mb else None,
        f"pokemon_name_{mb[:-2]}00" if len(mb) >= 10 else None,
        f"pokemon_name_200{mb[3:]}" if mb.startswith("210") else None,
        f"pokemon_name_200{mb[3:-2]}00" if mb.startswith("210") and len(mb) >= 10 else None,
        f"pokemon_name_200{mb[3:6]}00" if mb.startswith("210") and len(mb) >= 8 else None,
        f"pokemon_name_{mb[:6]}00" if len(mb) >= 8 else None,
        f"pokemon_name_{mb[:6]}11" if len(mb) >= 8 else None,
        f"pokemon_name_{mb[:6]}12" if len(mb) >= 8 else None,
        f"pokemon_name_{mb[:6]}1100" if len(mb) >= 10 else None,
        f"pokemon_name_200{mb[3:8]}" if len(mb) >= 10 else None
    ]
    for c in candidates:
        if c and c in loc_dict and loc_dict[c].strip():
            return clean_tags(loc_dict[c])
    return None

def run_descriptions_audit(log_mode="a"):
    print("=" * 60)
    print("   BLUESLAB: AUDITORÍA DE DESCRIPCIONES Y LOCALIZACIÓN")
    print("=" * 60)
    
    total_checks = 0
    passed_checks = 0
    discrepancies = []
    
    # 1. Structural Check for all 5 languages
    locales = {}
    for lang in LANGS:
        total_checks += 1
        common_path = LOCALES_DIR / f"common_{lang}.json"
        data_path = LOCALES_DIR / f"{lang}.json"
        if not common_path.exists() or not data_path.exists():
            discrepancies.append({
                "category": "Structural",
                "id": lang,
                "field": "Locale files existence",
                "expected": f"common_{lang}.json and {lang}.json exist",
                "actual": "Missing locale file(s)",
                "reason": "Locale file not found on disk"
            })
            continue
        
        try:
            d = load_locale_dict(lang)
            locales[lang] = d
            if len(d) > 5000:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Structural",
                    "id": lang,
                    "field": "Key count",
                    "expected": "> 5000 keys",
                    "actual": len(d),
                    "reason": "Dictionary appears truncated or underpopulated"
                })
        except Exception as e:
            discrepancies.append({
                "category": "Structural",
                "id": lang,
                "field": "JSON Parsing",
                "expected": "Valid JSON",
                "actual": str(e),
                "reason": "Corrupted JSON format in locale files"
            })

    print(f"[*] Diccionarios cargados correctamente para: {list(locales.keys())}")
    
    # 2. Check Manifest & Pairs Semantic Integrity in ES and EN
    if not MANIFEST_FILE.exists():
        print(f"[ERROR] Manifest file not found: {MANIFEST_FILE}")
        return
        
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    print(f"[*] Total de parejas a evaluar: {len(manifest)}")
    
    for item in manifest:
        tid = item.get("trainerId", "")
        t_key = item.get("trainerKey", "")
        t_base = item.get("trainerBaseId", "")
        mb_id = item.get("monsterBaseId", "")
        p_key = item.get("pokemonKey", "")
        pair_name = item.get("displayName", f"Pair {tid}")
        
        # Check Trainer and Pokemon name resolution in ES and EN
        for lang in ["es", "en"]:
            ld = locales.get(lang, {})
            # Trainer name
            total_checks += 1
            tr_res = resolve_trainer_name(ld, tid, t_key, t_base)
            if tr_res:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Trainer Name",
                    "id": tid,
                    "name": pair_name,
                    "field": f"Trainer Name ({lang.upper()})",
                    "expected": "Resolved localized trainer name",
                    "actual": "None / Fallback",
                    "reason": f"Missing key for trainerId={tid}, trainerKey={t_key}, baseId={t_base}"
                })
                
            # Pokemon name
            total_checks += 1
            pk_res = resolve_pokemon_name(ld, mb_id, p_key)
            if pk_res:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Pokemon Name",
                    "id": tid,
                    "name": pair_name,
                    "field": f"Pokemon Name ({lang.upper()})",
                    "expected": "Resolved localized pokemon name",
                    "actual": "None / Fallback",
                    "reason": f"Missing key for monsterBaseId={mb_id}, pokemonKey={p_key}"
                })

        # Detailed pair checks from pairs/{tid}.json
        p_file = PAIRS_DIR / f"{tid}.json"
        if not p_file.exists():
            continue
            
        try:
            with open(p_file, "r", encoding="utf-8") as pf:
                pair_detail = json.load(pf)
        except Exception:
            continue

        # Check Moves
        moves = pair_detail.get("moves", [])
        for m in moves:
            m_id = m.get("id", 0)
            m_name = m.get("name", "")
            m_desc = m.get("description", "")
            
            # Check move has non-empty name and description
            total_checks += 1
            if m_name and m_name.strip():
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Move Name",
                    "id": tid,
                    "name": pair_name,
                    "field": f"Move {m_id} Name",
                    "expected": "Non-empty string",
                    "actual": repr(m_name),
                    "reason": "Move name is empty or missing"
                })

            total_checks += 1
            if m_desc and m_desc.strip() and "[MISSING_KEY]" not in m_desc:
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Move Description",
                    "id": tid,
                    "name": pair_name,
                    "field": f"Move '{m_name}' ({m_id}) Description",
                    "expected": "Valid non-empty description",
                    "actual": repr(m_desc),
                    "reason": "Move description missing or contains [MISSING_KEY]"
                })

        # Check Passives
        passives = pair_detail.get("passives", [])
        if pair_detail.get("hasSuperAwakening") and pair_detail.get("superAwakeningPassive"):
            passives.append(pair_detail["superAwakeningPassive"])
            
        for ps in passives:
            ps_name = ps.get("name", "")
            ps_desc = ps.get("description", "")
            total_checks += 1
            if ps_name and ps_name.strip():
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Passive Name",
                    "id": tid,
                    "name": pair_name,
                    "field": "Passive Skill Name",
                    "expected": "Non-empty string",
                    "actual": repr(ps_name),
                    "reason": "Passive name is empty"
                })

            total_checks += 1
            if ps_desc and ps_desc.strip():
                passed_checks += 1
            else:
                discrepancies.append({
                    "category": "Passive Description",
                    "id": tid,
                    "name": pair_name,
                    "field": f"Passive '{ps_name}' Description",
                    "expected": "Valid non-empty description",
                    "actual": repr(ps_desc),
                    "reason": "Passive description is empty"
                })

        # Check Sync Grid Cells
        grid = pair_detail.get("grid", [])
        for cell in grid:
            ab_id = cell.get("abilityId", 0)
            if ab_id and int(ab_id) > 0:
                total_checks += 1
                tile_name_es = locales.get("es", {}).get(f"tile_name_{ab_id}")
                tile_name_en = locales.get("en", {}).get(f"tile_name_{ab_id}")
                if tile_name_es or tile_name_en:
                    passed_checks += 1
                else:
                    discrepancies.append({
                        "category": "Sync Grid Tile",
                        "id": tid,
                        "name": pair_name,
                        "field": f"Grid Cell {cell.get('cellId')} (abilityId={ab_id})",
                        "expected": "Resolved tile name in ES or EN",
                        "actual": "Unresolved in locales",
                        "reason": f"Missing tile_name_{ab_id} key in locales"
                    })

    # Summary
    fidelity = (passed_checks / total_checks * 100.0) if total_checks > 0 else 0.0
    print("-" * 60)
    print(f"[+] Total de verificaciones realizadas: {total_checks}")
    print(f"[+] Verificaciones superadas con éxito: {passed_checks}")
    print(f"[+] Discrepancias detectadas:           {len(discrepancies)}")
    print(f"[+] PORCENTAJE DE FIDELIDAD DE TEXTOS:  {fidelity:.2f}%")
    print("-" * 60)

    # Write log
    with open(LOG_FILE, log_mode, encoding="utf-8") as lf:
        lf.write(f"\n{'='*60}\n")
        lf.write(f"AUDITORÍA DE DESCRIPCIONES Y LOCALIZACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lf.write(f"Total verificaciones: {total_checks} | Aprobadas: {passed_checks} | Discrepancias: {len(discrepancies)}\n")
        lf.write(f"Fidelidad: {fidelity:.2f}%\n")
        lf.write(f"{'='*60}\n")
        for d in discrepancies:
            lf.write(f"[DISCREPANCY][PHASE-2][PAIR: {d.get('id')} - {d.get('name', 'N/A')}]\n")
            lf.write(f"  Category: {d.get('category')}\n")
            lf.write(f"  Field:    {d.get('field')}\n")
            lf.write(f"  Expected: {d.get('expected')}\n")
            lf.write(f"  Actual:   {d.get('actual')}\n")
            lf.write(f"  Reason:   {d.get('reason')}\n\n")

    if discrepancies:
        print(f"[!] Se registraron {len(discrepancies)} discrepancias en {LOG_FILE}")
    else:
        print(f"[OK] 100% de descripciones y textos son fieles a la especificación.")

    return {
        "total": total_checks,
        "passed": passed_checks,
        "discrepancies": len(discrepancies),
        "fidelity": fidelity
    }

if __name__ == "__main__":
    run_descriptions_audit(log_mode="a")
