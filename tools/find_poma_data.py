import urllib.request, re

url = "https://pomatools.github.io/index.html"
content = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")
print("index.html script tags:")
print(re.findall(r'<script[^>]*src="([^"]+)"', content))