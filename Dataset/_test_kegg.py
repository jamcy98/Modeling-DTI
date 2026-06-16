import requests

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

urls = [
    # BRITE hierarchies
    ("enzyme BRITE",         "https://rest.kegg.jp/get/br:hsa00199"),
    ("GPCR BRITE",           "https://rest.kegg.jp/get/br:hsa04030"),
    ("NR BRITE",             "https://rest.kegg.jp/get/br:hsa04040"),
    ("ion channel BRITE",    "https://rest.kegg.jp/get/br:hsa04022"),
    # Link operations
    ("enzyme→hsa link",      "https://rest.kegg.jp/link/hsa/enzyme"),
    ("hsa→drug link (head)", "https://rest.kegg.jp/link/drug/hsa:672"),
    # Pathways
    ("GPCR pathway",         "https://rest.kegg.jp/get/hsa04080"),
    ("NR pathway",           "https://rest.kegg.jp/get/hsa04933"),
    # Drug smiles test
    ("drug mol (aspirin)",   "https://rest.kegg.jp/get/D00109/mol"),
    ("drug info",            "https://rest.kegg.jp/get/D00109"),
]

for label, url in urls:
    try:
        r = s.get(url, timeout=10)
        body = r.text[:80].replace("\n", " ").strip()
        print(f"  {r.status_code}  {len(r.content):>8} bytes  {label}")
        if r.status_code == 200 and len(r.content) > 50:
            import re
            genes = re.findall(r"hsa:\d+", r.text)
            if genes:
                print(f"         sample genes: {genes[:5]}")
    except Exception as e:
        print(f"  ERR   {label}: {e}")
