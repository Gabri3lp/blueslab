import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/", headers=headers)).read().decode("utf-8")
scripts = re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html)
print("Scripts on index.html:", scripts)

# Find all chunk names in runtime or polyfills
for s in scripts:
    url = f"https://pomatools.github.io/{s}"
    try:
        content = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode("utf-8")
        chunks = re.findall(r'[a-zA-Z0-9_-]+\.[a-f0-9]{16}\.js', content)
        print(f"Chunks in {s}:", set(chunks))
    except Exception as e:
        print(f"Err {s}:", e)