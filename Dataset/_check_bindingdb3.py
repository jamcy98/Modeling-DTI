import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp",
})

# Try the direct file path
urls = [
    "https://www.bindingdb.org/rwd/bind/downloads/BindingDB_All_202606_tsv.zip",
    "https://www.bindingdb.org/bind/downloads/BindingDB_All_202606_tsv.zip",
]

for url in urls:
    try:
        r = session.head(url, timeout=15, allow_redirects=True)
        size = int(r.headers.get("content-length", 0))
        ctype = r.headers.get("content-type", "unknown")
        print(f"  {r.status_code}  {round(size/1e6, 1)} MB  {ctype}")
        print(f"  URL: {url}")
    except Exception as e:
        print(f"  ERROR: {e}  URL: {url}")
