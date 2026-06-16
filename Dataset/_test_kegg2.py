import requests, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

# Print first 30 lines of each BRITE file to understand the format
for label, url in [
    ("Enzyme   br:hsa00199", "https://rest.kegg.jp/get/br:hsa00199"),
    ("GPCR     br:hsa04030", "https://rest.kegg.jp/get/br:hsa04030"),
    ("NR       br:hsa04040", "https://rest.kegg.jp/get/br:hsa04040"),
]:
    print(f"\n=== {label} ===")
    r = s.get(url, timeout=15)
    lines = r.text.strip().split("\n")[:25]
    for l in lines:
        print(repr(l))

# Also test what link/hsa/enzyme looks like
print("\n=== link/hsa/enzyme (first 10 lines) ===")
r = s.get("https://rest.kegg.jp/link/hsa/enzyme", timeout=15)
for l in r.text.strip().split("\n")[:10]:
    print(repr(l))

# Test drug link for a known gene
print("\n=== drug link for hsa:2099 (NR3C1) ===")
r = s.get("https://rest.kegg.jp/link/drug/hsa:2099", timeout=15)
print(r.status_code, r.text[:300])

# Find ion channel BRITE
print("\n=== Searching for ion channel BRITE ===")
for brite_id in ["hsa04022", "hsa04010", "hsa04100", "hsa04070"]:
    r = s.get(f"https://rest.kegg.jp/get/br:{brite_id}", timeout=10)
    print(f"  br:{brite_id} -> {r.status_code} {len(r.content)} bytes")
