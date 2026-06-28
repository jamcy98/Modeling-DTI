"""
Preprocess protein sequences: FASTA -> ESM-2 residue-level embeddings.

Uses the ESM-2 (650M parameter) pre-trained protein language model from Meta AI
via HuggingFace Transformers to generate contextualised residue embeddings.

Run:
    python 11_preprocess_proteins.py

Output:
    processed/protein_embeddings/{dataset}_protein_embeddings.npy
        -> numpy array, shape: (n_proteins, max_len, 1280)
    processed/protein_embeddings/{dataset}_protein_ids.json
        -> list of protein IDs in the same row order as the .npy file

Notes:
    - ESM-2 (650M) requires ~3 GB GPU VRAM or ~8 GB RAM if running on CPU.
    - Processing will be slow on CPU. Use a GPU if available.
    - Sequences are truncated to MAX_SEQ_LEN residues (set below).

Requirements:
    pip install torch transformers tqdm numpy biopython
"""

import os
import json
import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
RAW_DIR   = os.path.join(BASE_DIR, "raw")
OUT_DIR   = os.path.join(BASE_DIR, "processed", "protein_embeddings")

ESM2_MODEL   = "facebook/esm2_t6_8M_UR50D"   # 8M params, 320-dim, ~50MB RAM
MAX_SEQ_LEN  = 1200    # truncate sequences longer than this
BATCH_SIZE   = 16      # safe with small model


# ── Dataset-specific sequence loaders ────────────────────────────────────────

def load_davis_proteins():
    path = os.path.join(RAW_DIR, "davis", "proteins.txt")
    with open(path) as f:
        return json.load(f)   # {protein_name: sequence}


def load_kiba_proteins():
    path = os.path.join(RAW_DIR, "kiba", "proteins.txt")
    with open(path) as f:
        return json.load(f)


def fetch_uniprot_sequences(uniprot_ids, cache_path=None):
    """
    Fetch protein sequences from UniProt REST API with caching.
    cache_path: optional JSON file to persist results across runs.
    """
    import requests, time
    cache = {}
    if cache_path and os.path.exists(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)

    to_fetch = [uid for uid in uniprot_ids if uid not in cache]
    print(f"  UniProt: {len(uniprot_ids)} proteins, "
          f"{len(to_fetch)} to fetch, {len(uniprot_ids)-len(to_fetch)} cached.")

    for i, uid in enumerate(tqdm(to_fetch, desc="  UniProt fetch")):
        try:
            r = requests.get(f"https://rest.uniprot.org/uniprotkb/{uid}.fasta",
                             timeout=10)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                cache[uid] = "".join(lines[1:])
            else:
                cache[uid] = None
        except Exception:
            cache[uid] = None
        time.sleep(0.05)
        if cache_path and (i + 1) % 500 == 0:
            with open(cache_path, "w") as f:
                json.dump(cache, f)

    if cache_path:
        with open(cache_path, "w") as f:
            json.dump(cache, f)

    seqs = {uid: seq for uid, seq in cache.items() if seq}
    print(f"  Successfully fetched {len(seqs)}/{len(uniprot_ids)} sequences.")
    return seqs


def load_yamanishi_proteins(subclass):
    """Load unique protein sequences directly from Yamanishi pairs.csv."""
    import pandas as pd
    path = os.path.join(RAW_DIR, "yamanishi_08", subclass, "pairs.csv")
    df   = pd.read_csv(path, usecols=["protein_id", "sequence"]).dropna().drop_duplicates("protein_id")
    return dict(zip(df["protein_id"], df["sequence"]))


def load_luo17_proteins():
    """UniProt accessions from protein_dict_map.txt -> sequences via UniProt REST."""
    map_path   = os.path.join(RAW_DIR, "luo_17", "protein_dict_map.txt")
    cache_path = os.path.join(RAW_DIR, "luo_17", "protein_seq_cache.json")
    ids = []
    with open(map_path) as f:
        for line in f:
            line = line.strip()
            if line:
                ids.append(line.split(":")[0].strip())
    print(f"  Luo_17: {len(ids)} proteins.")
    return fetch_uniprot_sequences(ids, cache_path=cache_path)


def load_bindingdb_proteins():
    """
    Load BindingDB protein sequences from pre-built cache.
    Cache is built from BindingDB_All.tsv (column: BindingDB Target Chain Sequence 1)
    which contains the actual sequences — no UniProt API needed.
    Run: python -c "..." to rebuild cache if needed (see extraction script).
    """
    cache_path = os.path.join(RAW_DIR, "bindingdb", "protein_seq_cache.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            seqs = json.load(f)
        valid = {k: v for k, v in seqs.items() if v and len(v) > 0}
        print(f"  BindingDB: {len(valid):,} proteins loaded from sequence cache.")
        return valid
    print("  BindingDB: no sequence cache found — run extraction script first.")
    return {}


def load_chembl_proteins():
    import pandas as pd
    cache_path = os.path.join(RAW_DIR, "chembl", "protein_seq_cache.json")
    df  = pd.read_csv(os.path.join(RAW_DIR, "chembl", "chembl_DTI.csv"),
                      usecols=["uniprot_id"]).dropna().drop_duplicates()
    ids = df["uniprot_id"].tolist()
    print(f"  ChEMBL: {len(ids)} unique proteins.")
    return fetch_uniprot_sequences(ids, cache_path=cache_path)


RAW_CHECK_MAP = {
    "davis":          "davis",
    "kiba":           "kiba",
    "luo_17":         "luo_17",
    "yamanishi_e":    os.path.join("yamanishi_08", "e"),
    "yamanishi_ic":   os.path.join("yamanishi_08", "ic"),
    "yamanishi_gpcr": os.path.join("yamanishi_08", "gpcr"),
    "yamanishi_nr":   os.path.join("yamanishi_08", "nr"),
    "bindingdb":      "bindingdb",
    "chembl":         "chembl",
}

DATASET_LOADERS = {
    "davis":           load_davis_proteins,
    "kiba":            load_kiba_proteins,
    "luo_17":          load_luo17_proteins,
    "yamanishi_e":     lambda: load_yamanishi_proteins("e"),
    "yamanishi_ic":    lambda: load_yamanishi_proteins("ic"),
    "yamanishi_gpcr":  lambda: load_yamanishi_proteins("gpcr"),
    "yamanishi_nr":    lambda: load_yamanishi_proteins("nr"),
    "bindingdb":       load_bindingdb_proteins,
    "chembl":          load_chembl_proteins,
}


# ── ESM-2 Encoder ─────────────────────────────────────────────────────────────

class ESM2Encoder:
    def __init__(self, model_name=ESM2_MODEL, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"  Loading ESM-2 model: {model_name}")
        print(f"  Device: {self.device}")
        print("  NOTE: First run will download ~2.5 GB model weights from HuggingFace.")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model     = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.embed_dim = self.model.config.hidden_size   # 1280 for ESM-2 650M

    @torch.no_grad()
    def encode(self, sequences, max_len=MAX_SEQ_LEN, mean_pool=False):
        """
        Encode a list of sequences.

        mean_pool=False: returns (n_seqs, max_len, embed_dim)  — full residue embeddings
        mean_pool=True:  returns (n_seqs, embed_dim)           — mean-pooled, memory-safe
        """
        all_embeddings = []

        for i in range(0, len(sequences), BATCH_SIZE):
            batch_seqs = sequences[i : i + BATCH_SIZE]
            batch_seqs_trunc = [s[:max_len] for s in batch_seqs]

            tokens = self.tokenizer(
                batch_seqs_trunc,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_len + 2,
            ).to(self.device)

            out    = self.model(**tokens)
            hidden = out.last_hidden_state       # (batch, seq_len+2, embed_dim)

            # Strip [CLS] and [EOS] tokens
            residue_emb = hidden[:, 1:-1, :]    # (batch, seq_len, embed_dim)

            if mean_pool:
                # Mean over residue dimension → (batch, embed_dim)
                # Mask padding tokens so they don't affect the mean
                attention = tokens["attention_mask"][:, 1:-1].unsqueeze(-1).float()
                pooled    = (residue_emb * attention).sum(dim=1) / attention.sum(dim=1).clamp(min=1)
                all_embeddings.append(pooled.cpu().numpy())
            else:
                # Pad/truncate to fixed max_len
                seq_len = residue_emb.size(1)
                if seq_len < max_len:
                    pad = torch.zeros(
                        residue_emb.size(0), max_len - seq_len, self.embed_dim,
                        device=self.device)
                    residue_emb = torch.cat([residue_emb, pad], dim=1)
                else:
                    residue_emb = residue_emb[:, :max_len, :]
                all_embeddings.append(residue_emb.cpu().numpy())

        return np.concatenate(all_embeddings, axis=0)


# Datasets with > this many proteins use mean-pooling to avoid OOM
# (full residue arrays would exceed available RAM)
MEAN_POOL_THRESHOLD = 1000


# ── Main processing ───────────────────────────────────────────────────────────

def process_dataset(name, protein_dict, encoder):
    if not protein_dict:
        print(f"  No sequences loaded for {name} — skipping.")
        return

    print(f"\nProcessing {name} ({len(protein_dict):,} proteins)...")

    ids   = list(protein_dict.keys())
    seqs  = [protein_dict[pid] for pid in ids]

    valid = [(pid, seq) for pid, seq in zip(ids, seqs) if seq and len(seq) > 0]
    if len(valid) < len(ids):
        print(f"  Removed {len(ids) - len(valid)} proteins with empty sequences.")
    ids  = [v[0] for v in valid]
    seqs = [v[1] for v in valid]

    lengths   = [len(s) for s in seqs]
    mean_pool = len(seqs) > MEAN_POOL_THRESHOLD

    if mean_pool:
        est_gb = len(seqs) * MAX_SEQ_LEN * encoder.embed_dim * 4 / 1e9
        print(f"  Large dataset ({len(seqs):,} proteins) — using mean-pooling.")
        print(f"  (Full residue arrays would require ~{est_gb:.1f} GB RAM.)")
    else:
        print(f"  Small dataset — storing full residue embeddings (max_len={MAX_SEQ_LEN}).")

    print(f"  Sequence lengths: min={min(lengths)}, max={max(lengths)}, "
          f"mean={int(sum(lengths)/len(lengths))}, "
          f"truncated={sum(l > MAX_SEQ_LEN for l in lengths)}")
    print(f"  Encoding {len(seqs):,} sequences with ESM-2...")

    embeddings = encoder.encode(seqs, mean_pool=mean_pool)
    print(f"  Output shape: {embeddings.shape}")

    emb_path = os.path.join(OUT_DIR, f"{name}_protein_embeddings.npy")
    id_path  = os.path.join(OUT_DIR, f"{name}_protein_ids.json")

    np.save(emb_path, embeddings)
    with open(id_path, "w") as f:
        json.dump(ids, f)

    print(f"  Saved -> {emb_path}")
    print(f"  IDs  -> {id_path}")


def main():
    print("=" * 55)
    print(" Protein Preprocessing (Sequences -> ESM-2 Embeddings)")
    print("=" * 55)

    os.makedirs(OUT_DIR, exist_ok=True)
    encoder = ESM2Encoder()

    for name, loader_fn in DATASET_LOADERS.items():
        raw_sub   = RAW_CHECK_MAP.get(name, name)
        raw_check = os.path.join(RAW_DIR, raw_sub)
        if not os.path.isdir(raw_check) or not os.listdir(raw_check):
            print(f"\nSkipping {name} — raw data not found.")
            continue

        emb_path = os.path.join(OUT_DIR, f"{name}_protein_embeddings.npy")
        if os.path.exists(emb_path):
            print(f"\n{name}: embeddings already exist — skipping.")
            continue

        try:
            proteins = loader_fn()
            process_dataset(name, proteins, encoder)
        except FileNotFoundError as e:
            print(f"\nSkipping {name}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
