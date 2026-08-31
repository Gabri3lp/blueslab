import time, urllib.request, json

url = "https://api.github.com/repos/Gabri3lp/blueslab/actions/runs?per_page=1"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

for i in range(15):
    time.sleep(3)
    try:
        data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        run = data["workflow_runs"][0]
        st = run.get("status")
        conc = run.get("conclusion")
        print(f"Attempt {i+1}: Status={st}, Conclusion={conc}")
        if st == "completed":
            break
    except Exception as e:
        print(f"Attempt {i+1}: {e}")