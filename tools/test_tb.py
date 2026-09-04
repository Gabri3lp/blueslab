import urllib.request
import json

url = "https://pokemon.brybry.ch/masters/data/proto/TrainerBase.json"
tb_data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8'))
entries = tb_data.get('entries', [])

print("TrainerBase sample entries:")
for e in entries[:10]:
    print(e)
