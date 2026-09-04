import json
with open('src/BluesLab/wwwroot/locales/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
print("move_name_80700:", es.get("move_name_80700"))
print("move_desc_80700:", es.get("move_desc_80700"))
