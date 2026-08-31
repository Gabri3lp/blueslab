import urllib.request, re

headers = {"User-Agent": "Mozilla/5.0"}
html = urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/damage-calculator/", headers=headers)).read().decode("utf-8")
scripts = re.findall(r'<script\s+[^>]*src=[\"\']([^\"\']+)[\"\']', html)
print("Scripts on damage-calculator page:", scripts)

# Also check index.html
html2 = urllib.request.urlopen(urllib.request.Request("https://pomatools.github.io/", headers=headers)).read().decode("utf-8")
scripts2 = re.findall(r'<script\s+[^>]*src=[\"\']([^\"\']+)[\"\']', html2)
print("Scripts on root index.html:", scripts2)