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

ESM2_MODEL   = "facebook/esm2_t33_650M_UR50D"
MAX_SEQ_LEN  = 1200    # truncate sequences longer than this
BATCH_SIZE   = 4       # reduce to 1 or 2 if you run out of GPU memory


# ── Dataset-specific sequence loaders ────────────────────────────────────────

def load_davis_proteins():
    path = os.path.join(RAW_DIR, "davis", "proteins.txt")
    with open(path) as f:
        return json.load(f)   # {protein_name: sequence}


def load_kiba_proteins():
    path = os.path.join(RAW_DIR, "kiba", "proteins.txt")
    with open(path) as f:
        return json.load(f)


def load_yamanishi_proteins(subclass):
    """
    Load protein sequences from Yamanishi_08 sub-class.
    The DTINet repo stores sequences in 'protein_sequences.txt' or similar.
    Falls back to fetching from UniProt if file is not found.
    """
    seq_path = os.path.join(RAW_DIR, "yamanishi_08", subclass, "target_sequence.txt")
    if not os.path.exists(seq_path):
        seq_path = os.path.join(RAW_DIR, "yamanishi_08", subclass, "protein_sequences.txt")

    if os.path.exists(seq_path):
        proteins = {}
        with open(seq_path) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    proteins[parts[0]] = parts[1]
        return proteins

    # File not found — warn and return empty
    print(f"    WARNING: Protein sequences not found for yamanishi_{subclass}.")
    print(f"    Expected at: {seq_path}")
    print(f"    Please download sequences manually from UniProt and save in that path.")
    return {}


def load_bindingdb_proteins():
    import pandas as pd
    dti_path = os.path.join(RAW_DIR, "bindingdb", "BindingDB_DTI.csv")
    df = pd.read_csv(dti_path)
    # BindingDB DTI file may not have sequences; protein_id is UniProt accession
    # Sequences would need to be fetched from UniProt
    if "protein_sequence" in df.columns:
        return dict(zip(df["uniprot_id"], df["protein_sequence"]))
    print("  NOTE: BindingDB file has no sequences. Fetching from UniProt...")
    return fetch_uniprot_sequences(df["uniprot_id"].dropna().unique().tolist())


def load_chembl_proteins():
    import pandas as pd
    dta_path = os.path.join(RAW_DIR, "chembl", "chembl_DTA.csv")
    df = pd.read_csv(dta_path)
    if "protein_sequence" in df.columns:
        return dict(zip(df["uniprot_id"], df["protein_sequence"]))
    # ChEMBL SQLite query already returned sequences in column 'protein_sequence'
    # but they were not saved in the CSV. Load from chembl_DTI.csv if available.
    dti_path = os.path.join(RAW_DIR, "chembl", "chembl_DTI.csv")
    if os.path.exists(dti_path):
        df2 = pd.read_csv(dti_path)
        if "protein_sequence" in df2.columns:
            return dict(zip(df2["uniprot_id"], df2["protein_sequence"]))
    print("  NOTE: Sequences not in ChEMBL CSV. Fetching from UniProt...")
    return fetch_uniprot_sequences(df["uniprot_id"].dropna().unique().tolist())


def fetch_uniprot_sequences(uniprot_ids, max_fetch=5000):
    """Batch fetch protein sequences from the UniProt REST API."""
    import requests
    print(f"  Fetching {min(len(uniprot_ids), max_fetch)} sequences from UniProt...")
    sequences = {}
    ids_to_fetch = uniprot_ids[:max_fetch]

    for uid in tqdm(ids_to_fetch, desc="  UniProt fetch"):
        url = f"https://rest.uniprot.org/uniprotkb/{uid}.fasta"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                seq   = "".join(lines[1:])   # skip header line
                sequences[uid] = seq
        except Exception:
            pass

    print(f"  Successfully fetched {len(sequences)} sequences.")
    return sequences


DATASET_LOADERS = {
    # DAVIS and KIBA first — small and fast on CPU (~442 and ~229 proteins)
    "davis":           load_davis_proteins,
    "kiba":            load_kiba_proteins,
    # Large datasets commented out — enable after confirming GPU or run overnight
    # "yamanishi_e":     lambda: load_yamanishi_proteins("e"),
    # "yamanishi_ic":    lambda: load_yamanishi_proteins("ic"),
    # "yamanishi_gpcr":  lambda: load_yamanishi_proteins("gpcr"),
    # "yamanishi_nr":    lambda: load_yamanishi_proteins("nr"),
    # "bindingdb":       load_bindingdb_proteins,
    # "chembl":          load_chembl_proteins,
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
    def encode(self, sequences, max_len=MAX_SEQ_LEN):
        """
        Encode a list of sequences.
        Returns: numpy array of shape (n_seqs, max_len, embed_dim)
        """
        all_embeddings = []

        for i in range(0, len(sequences), BATCH_SIZE):
            batch_seqs = sequences[i : i + BATCH_SIZE]

            # Truncate long sequences
            batch_seqs_trunc = [s[:max_len] for s in batch_seqs]

            tokens = self.tokenizer(
                batch_seqs_trunc,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_len + 2,   # +2 for [CLS] and [EOS] tokens
            ).to(self.device)

            out        = self.model(**tokens)
            hidden     = out.last_hidden_state  # (batch, seq_len+2, embed_dim)

            # Remove [CLS] and [EOS] tokens; keep residue embeddings only
            residue_emb = hidden[:, 1:-1, :]    # (batch, seq_len, embed_dim)

            # Pad to max_len if shorter
            seq_len = residue_emb.size(1)
            if seq_len < max_len:
                pad = torch.zeros(
                    residue_emb.size(0), max_len - seq_len, self.embed_dim,
                    device=self.device
                )
                residue_emb = torch.cat([residue_emb, pad], dim=1)
            else:
                residue_emb = residue_emb[:, :max_len, :]

            all_embeddings.append(residue_emb.cpu().numpy())

        return np.concatenate(all_embeddings, axis=0)   # (n_seqs, max_len, 1280)


# ── Main processing ───────────────────────────────────────────────────────────

def process_dataset(name, protein_dict, encoder):
    if not protein_dict:
        print(f"  No sequences loaded for {name} — skipping.")
        return

    print(f"\nProcessing {name} ({len(protein_dict):,} proteins)...")

    ids       = list(protein_dict.keys())
    seqs      = [protein_dict[pid] for pid in ids]

    # Remove proteins with empty sequences
    valid = [(pid, seq) for pid, seq in zip(ids, seqs) if seq and len(seq) > 0]
    if len(valid) < len(ids):
        print(f"  Removed {len(ids) - len(valid)} proteins with empty sequences.")
    ids  = [v[0] for v in valid]
    seqs = [v[1] for v in valid]

    print(f"  Encoding {len(seqs)} sequences with ESM-2 (max_len={MAX_SEQ_LEN})...")
    print(f"  Sequence length stats:")
    lengths = [len(s) for s in seqs]
    print(f"    min={min(lengths)}, max={max(lengths)}, "
          f"mean={int(sum(lengths)/len(lengths))}, "
          f"truncated={sum(l > MAX_SEQ_LEN for l in lengths)}")

    embeddings = encoder.encode(seqs)   # (n_proteins, MAX_SEQ_LEN, 1280)

    # Save embeddings
    emb_path = os.path.join(OUT_DIR, f"{name}_protein_embeddings.npy")
    id_path  = os.path.join(OUT_DIR, f"{name}_protein_ids.json")

    np.save(emb_path, embeddings)
    with open(id_path, "w") as f:
        json.dump(ids, f)

    print(f"  Embeddings saved -> {emb_path}  shape: {embeddings.shape}")
    print(f"  IDs saved        -> {id_path}")


def main():
    print("=" * 55)
    print(" Protein Preprocessing (Sequences -> ESM-2 Embeddings)")
    print("=" * 55)

    encoder = ESM2Encoder()

    for name, loader_fn in DATASET_LOADERS.items():
        emb_path = os.path.join(OUT_DIR, f"{name}_protein_embeddings.npy")
        if os.path.exists(emb_path):
            print(f"\n{name} embeddings already exist — skipping.")
            continue

        try:
            proteins = loader_fn()
            process_dataset(name, proteins, encoder)
        except FileNotFoundError as e:
            print(f"\nSkipping {name}: {e}")

    print("\nDone. Run 12_preprocess_labels.py next.")


if __name__ == "__main__":
    main()
