import requests, re

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Check what SDFdownload.jsp returns
url = "https://www.bindingdb.org/rwd/bind/chemsearch/marvin/SDFdownload.jsp?download_file=/rwd/bind/downloads/BindingDB_All_202606_tsv.zip"
r = session.get(url, timeout=20, allow_redirects=True)
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))
print("Final URL:", r.url)
print("Content length:", len(r.content))
print("First 500 chars:", r.text[:500])

# Look for any redirect URL in the content
links = re.findall(r'https?://[^\s"\'<>]+(?:zip|tsv|gz)', r.text)
print("\nURLs found:", links)
