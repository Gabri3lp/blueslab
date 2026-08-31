import urllib.request, re, json

url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")

print(f"Downloaded PoMaTools main JS: {len(content)} bytes")

# 1. Search for calculateMoveLevel and getMoveIncreaser
print("\n=== 1. SEARCH: calculateMoveLevel ===")
for m in re.finditer(r'calculateMoveLevel', content):
    idx = m.start()
    print("--- SNIPPET ---")
    print(content[max(0, idx-100):min(len(content), idx+500)])

# 2. Search for getMoveIncreaser
print("\n=== 2. SEARCH: getMoveIncreaser ===")
for m in re.finditer(r'getMoveIncreaser', content):
    idx = m.start()
    print("--- SNIPPET ---")
    print(content[max(0, idx-100):min(len(content), idx+500)])

# 3. Search for getMoveLvlMultipliers
print("\n=== 3. SEARCH: getMoveLvlMultipliers ===")
for m in re.finditer(r'getMoveLvlMultipliers', content):
    idx = m.start()
    print("--- SNIPPET ---")
    print(content[max(0, idx-100):min(len(content), idx+500)])

# 4. Search for calculateBaseStats
print("\n=== 4. SEARCH: calculateBaseStats ===")
for m in re.finditer(r'calculateBaseStats', content):
    idx = m.start()
    print("--- SNIPPET ---")
    print(content[max(0, idx-100):min(len(content), idx+500)])

# 5. Search for role bitmasks or role numbers in PoMaTools
print("\n=== 5. SEARCH: role definitions in PoMaTools ===")
for m in re.finditer(r'colRoles|roles|roleId|role\s*&', content):
    idx = m.start()
    print("--- SNIPPET ---")
    print(content[max(0, idx-50):min(len(content), idx+200)])