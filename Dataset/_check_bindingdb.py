import requests, re
r = requests.get("https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp", timeout=15)
print("Page status:", r.status_code)
links = re.findall(r'href=["\']([^"\']*(?:tsv|zip|gz)[^"\']*)["\']', r.text, re.IGNORECASE)
for l in sorted(set(links))[:20]:
    print(" ", l)
