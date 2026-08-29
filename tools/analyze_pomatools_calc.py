import urllib.request
import re

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req).read().decode("utf-8")

# Let us search for damage formulas, damage roll array, stat stage calculation, rebuffs, circles, weather, zone, terrain, sync multipliers, tech ex bonus
keywords = ["Math.floor", "damageRoll", "calculateDamage", "calcDamage", "battleBonus", "stageMultiplier", "0.9", "0.91", "1.5", "rebuff", "circle", "masterPassive", "superAwakening", "syncBuff"]

matches = []
# Find sections with damage formula calculation
calc_sections = re.findall(r'(\w+=[^;]{0,100}(?:damage|movePower|statRatio|battleBonus|syncBonus)[^;]{0,300};)', content, re.I)
print(f"Found {len(calc_sections)} snippets matching damage terms.")
for s in calc_sections[:15]:
    print("Snippet:", s[:200])

# Search specifically for the main calculation function in PoMaTools
# Look for where 0.9, 0.91 or damage range / rolls are computed
roll_matches = [m.start() for m in re.finditer(r'0\.9(?:0|5)?,\s*0\.91', content)]
print(f"Roll matches count: {len(roll_matches)}")
for idx in roll_matches:
    start = max(0, idx - 500)
    end = min(len(content), idx + 1000)
    print("\n--- FOUND DAMAGE CALC CODE BLOCK ---")
    print(content[start:end])