import urllib.request
import re

main_url = "https://pomatools.github.io/main.df16a9338a373a1c.js"
req = urllib.request.Request(main_url, headers={"User-Agent": "Mozilla/5.0"})
content = urllib.request.urlopen(req).read().decode("utf-8")

print(f"main.js size: {len(content)} bytes")

# Find json endpoints or data assets fetched
json_urls = set(re.findall(r'["\']([^"\']+\.json[^"\']*)["\']', content))
print("JSON endpoints/files referenced:")
for j in list(json_urls)[:25]:
    print(" -", j)