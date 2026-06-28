"""
Configuration for H-GNN-RNN-DTI experiments.
"""
import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "Dataset", "processed")
CKPT_DIR  = os.path.join(BASE_DIR, "checkpoints")
LOG_DIR   = os.path.join(BASE_DIR, "logs")

os.makedirs(CKPT_DIR, exist_ok=True)
os.makedirs(LOG_DIR,  exist_ok=True)


# ── Model hyperparameters ─────────────────────────────────────────────────────
MODEL = dict(
    node_feat_dim = 65,       # RDKit atom features
    esm_dim       = 320,      # ESM-2 8M output (320); Luo_17 has 1280 → projected
    hidden_dim    = 256,
    gat_layers    = 3,
    gat_heads     = 8,
    gru_layers    = 2,
    chemberta_dim = 768,      # ChemBERTa CLS; drug graphs without CB still work
    fusion_heads  = 8,
    dropout       = 0.1,
)


# ── Training hyperparameters ──────────────────────────────────────────────────
TRAIN = dict(
    batch_size    = 32,
    lr            = 1e-4,
    weight_decay  = 1e-5,
    epochs        = 100,
    patience      = 15,       # early stopping
    grad_clip     = 1.0,
    scheduler     = 'cosine', # 'cosine' | 'step' | None
    warmup_epochs = 5,
)


# ── Dataset configurations ────────────────────────────────────────────────────
DATASETS = {
    # Primary DTA benchmarks (regression)
    'davis': dict(task='dta', split_type='random',    ratio=None),
    'kiba':  dict(task='dta', split_type='random',    ratio=None),

    # DTI benchmarks (binary classification)
    'luo_17':         dict(task='dti', split_type='random', ratio='1to1'),
    'yamanishi_e':    dict(task='dti', split_type='random', ratio='1to1'),
    'yamanishi_ic':   dict(task='dti', split_type='random', ratio='1to1'),
    'yamanishi_gpcr': dict(task='dti', split_type='random', ratio='1to1'),
    'yamanishi_nr':   dict(task='dti', split_type='random', ratio='1to1'),
    'bindingdb':      dict(task='dti', split_type='random', ratio='1to1'),
}


# ── Focal loss parameters ─────────────────────────────────────────────────────
FOCAL = dict(gamma=2.0, alpha=0.25)
