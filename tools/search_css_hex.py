import glob

for path in glob.glob("src/BluesLab/**/*.css", recursive=True):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if "hex" in content or "polygon" in content or "active" in content or "stroke" in content or "border" in content:
            print(f"=== {path} ===")
            for line in content.splitlines():
                if any(k in line.lower() for k in ["hex", "polygon", "tile", "stroke", "border", "white"]):
                    print(" ", line)