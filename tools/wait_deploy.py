import time, urllib.request, json
url = "https://api.github.com/repos/Gabri3lp/blueslab/actions/runs?per_page=1"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
for i in range(12):
    time.sleep(5)
    data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    run = data["workflow_runs"][0]
    status = run.get("status")
    conclusion = run.get("conclusion")
    print(f"Attempt {i+1}: id={run.get('id')}, status={status}, conclusion={conclusion}")
    if status == "completed":
        break