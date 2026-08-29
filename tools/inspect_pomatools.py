import urllib.request
import re

url = "https://pomatools.github.io"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8")

scripts = re.findall(r'src="([^"]+\.js)"', html)
print("Scripts found in HTML:")
for s in scripts:
    print(" -", s)

links = re.findall(r'href="([^"]+\.(?:json|css|webmanifest))"', html)
print("Links/Assets found:")
for l in links:
    print(" -", l)