with open("src/BluesLab/wwwroot/css/app.css", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if any(k in line.lower() for k in ["hex", "tile", "grid", "polygon", "overlay", "active"]):
        print(f"{i+1}: {line.strip()}")