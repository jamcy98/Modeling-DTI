import json, numpy as np
from pathlib import Path

LOG = Path('logs')
SEEDS = [1,2,3,4,5]
SPLITS = ['random','cold_drug','cold_target','cold_pair']

configs = [
    ('hgnn_rnn_dti',       'Focal 1:1 (baseline)'),
    ('hgnn_rnn_dti_1to5',  'Focal 1:5'),
    ('hgnn_rnn_dti_1to10', 'Focal 1:10'),
]

for ds in ['yamanishi_e', 'luo_17']:
    print(f'\n=== {ds} AUROC ===')
    print(f"  {'Split':<14}  {'1:1 base':<16}  {'1:5':<16}  {'1:10':<16}")
    for sp in SPLITS:
        row = f"  {sp:<14}"
        for run_name, label in configs:
            vals = []
            for s in SEEDS:
                p = LOG / f'{run_name}_{ds}_dti_{sp}_fold0_seed{s}.json'
                if p.exists():
                    d = json.loads(p.read_text())
                    vals.append(d['test_metrics']['auroc'])
            if vals:
                row += f"  {np.mean(vals):.3f}+-{np.std(vals,ddof=1):.3f}   "
            else:
                row += f"  {'N/A':<16}"
        print(row)

    print(f"\n=== {ds} AUPRC ===")
    print(f"  {'Split':<14}  {'1:1 base':<16}  {'1:5':<16}  {'1:10':<16}")
    for sp in SPLITS:
        row = f"  {sp:<14}"
        for run_name, label in configs:
            vals = []
            for s in SEEDS:
                p = LOG / f'{run_name}_{ds}_dti_{sp}_fold0_seed{s}.json'
                if p.exists():
                    d = json.loads(p.read_text())
                    vals.append(d['test_metrics']['auprc'])
            if vals:
                row += f"  {np.mean(vals):.3f}+-{np.std(vals,ddof=1):.3f}   "
            else:
                row += f"  {'N/A':<16}"
        print(row)
