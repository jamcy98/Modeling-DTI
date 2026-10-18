# CLAUDE.md — H-GNN-RNN-DTI (Objective 1 implementation)

Project context + running history for this codebase. Read this first in any new
session. Detailed technical analysis lives in `docs/objective1_analysis.md`.

---

## 1. What this is

PhD thesis: **"Enhanced Drug–Target Interaction Prediction Through Hybrid Deep
Learning Approaches"** — Jamila Abdul-Hadi (USM, School of Computer Sciences;
supervisor Assoc. Prof. Dr. Nurul Hashimah Ahamed Hassain Malim).

This repo implements **Objective 1 — Dynamic Cross-Modal Fusion**:
an **H-GAT** drug encoder + **Bi-LSTM** protein encoder coupled by a
**bidirectional Gated Cross-Attention (GCA)** fusion mechanism, for DTI
classification and DTA regression.

- **RQ1:** Does bidirectional GCA between H-GAT and Bi-LSTM improve cross-modal
  feature integration vs. simpler fusion (static concat, flat gating, ungated
  cross-attention)?
- The three objectives: **Obj1** = fusion (this work), **Obj2** = representation
  enrichment + cold-start generalization, **Obj3** = four-tier interpretability.

## 2. Ratified decisions (do not silently change)

- **Fusion is isolated:** Obj1 holds features at ONE fixed reference config and
  varies *only* `fusion.type`. Obj2 does the reverse (fix fusion=GCA, vary
  features C1→C4). This factorial split keeps the two objectives unconfounded.
- **Reference config = C1 (light):** RDKit graph + basic protein tokens. No
  ChemBERTa/ESM-2/SS/physicochemical in Obj1 (those are Obj2). Set in
  `configs/default.yaml`.
- **First dataset = DAVIS.** Binary label threshold **Kd ≤ 30 nM**. Primary
  split **S1 warm-start**. Primary metric **AUPR** (DAVIS is ~4% positive).
- **Baselines:** primary RQ1 evidence is the *internal fusion ablation*
  (concat / flat_gate / ungated_xattn vs gca, identical encoders/features/
  splits). External published models deferred to week 2 / Obj2.
- **Compute:** no local GPU secured → run the ablation on a **free cloud GPU
  (Colab)**. CPU is for dev + tests only (full training on CPU is impractical).
- **No second post-pooling fusion gate** (proposal §3.6.7) — keeps GCA the only
  cross-modal interaction so the ablation isolates it.

## 3. Environment

- **Python 3.11.15 via `uv`**, venv at `.venv/` in this folder.
- Pinned quirks (see `requirements.txt`): **`PyTDC==0.4.1`** (1.x needs
  `tiledbsoma`, unbuildable on Windows), **`setuptools<81`** (PyTDC 0.4.1 imports
  `pkg_resources`), official **`rdkit`** (NOT `rdkit-pypi` — NumPy-2 compat).
  Local: torch 2.14 CPU + PyG 2.8.
- Setup: `uv venv --python 3.11 .venv` then `uv pip install -r requirements.txt`
  (plus `rdkit torch torch-geometric` as needed).
- **RDKit is imported lazily** — only preprocessing (SMILES→graph) needs it; the
  training/ablation runtime does not. This lets Colab run with just
  `torch-geometric` on top of its stock PyTorch.

## 4. Repo map

```
configs/default.yaml        Obj1 reference config (fusion.type is the ablation knob)
data/raw|processed|splits/  datasets; processed DAVIS is bundled in git (frozen)
src/hgnn_rnn_dti/
  data/      datasets(TDC+local loaders) · featurize(graphs/tokens) · labels · splits · dataset(DataLoader)
  encoders/  drug_encoder(H-GAT) · protein_encoder(Bi-LSTM)
  fusion/    build_fusion + modules (gca/ungated_xattn/flat_gate/concat)
  models/    model(assembly) · heads(MLP) · build(from config)
  training/  losses(focal) · trainer · run(run_experiment)
  evaluation/metrics(AUROC/AUPR/RMSE/MAE/PCC)
  utils/     config · seed · pooling
scripts/     download_data · download_extra_datasets · preprocess · train · run_ablation · make_colab_notebook · make_step_summary_docx
notebooks/   Objective1_Ablation_Colab.ipynb   (GPU run)
tests/       29 tests (pytest -q)
docs/        objective1_analysis.md (full analysis) · Steps1-2_Summary_PlainEnglish.docx
```

## 5. How to run

```bash
# data (TDC: DAVIS/KIBA/BindingDB)
python scripts/download_data.py --dataset all
python scripts/download_extra_datasets.py          # Yamanishi + Luo (ID/matrix form)
# preprocess DAVIS (Kd<=30nM, S1 split) — processed copy is already bundled in git
python scripts/preprocess.py --dataset davis
# train one config
python scripts/train.py --dataset davis --fusion gca --seed 42
# THE RQ1 RESULT: fusion ablation (use a GPU)
python scripts/run_ablation.py --dataset davis --device cuda --seeds 42 43 44
pytest -q                                          # 29 tests
```
Colab (one click): open
`https://colab.research.google.com/github/jamcy98/Modeling-DTI/blob/objective1-impl/H-GNN-RNN-DTI/notebooks/Objective1_Ablation_Colab.ipynb`
→ Runtime → GPU → Run all.

## 6. Datasets acquired

| Dataset | Pairs | Drugs | Targets | Notes |
|---|---|---|---|---|
| DAVIS (TDC) | 25,772 | 68 | 379 | Kd nM; **project ground truth** (not DeepDTA's 68/442/30056). Processed copy bundled in git. |
| KIBA (TDC) | 117,657 | 2,068 | 229 | KIBA score (threshold 12.1) |
| BindingDB_Kd (TDC) | 52,274 | 10,636 | 1,090 | has Kd=0 rows → clean before use |
| Yamanishi_08 | 5,127 | — | — | 4 classes (E 2926/IC 1476/GPCR 635/NR 90). KEGG IDs, **not SMILES/FASTA** |
| Luo_17 / DTINet | 1,923 | 708 | 1,512 | DrugBank/UniProt IDs, **not SMILES/FASTA** |

Yamanishi + Luo need an ID→SMILES/FASTA mapping before the model can use them
(they're Obj2 / cold-start datasets; see each `data/raw/<name>/README_PROVENANCE.md`).

## 7. Progress log

**2026-10-17 → 2026-10-18 (session 1, with Claude):**
- Reviewed the updated proposal (`../Proposal Document/Draft Proposal_Updated_final.docx`);
  wrote `docs/objective1_analysis.md` (novelty / soundness / feasibility & compute /
  risks + a phased build roadmap).
- **Step 1** env + dataset download (DAVIS/KIBA/BindingDB via TDC).
- **Step 2** preprocessing: RDKit graphs, protein tokens, Kd≤30nM binarization
  (DAVIS = 4.1% positive), stratified S1 split, leakage test. Feature dims:
  atom=80, bond=10, protein_vocab=22.
- Downloaded Yamanishi + Luo (ID/matrix form; mapping pending).
- Produced a plain-English review doc: `docs/Steps1-2_Summary_PlainEnglish.docx`.
- **Steps 4–5** encoders (H-GAT, Bi-LSTM) + 4 swappable fusion modules.
- **Step 6** full model + prediction head (~1.12M params; no 2nd post-pooling gate).
- **Step 7** focal loss + metrics + Trainer + `train.py`. Overfit test proves the
  pipeline learns (loss −40%+, train AUPR>0.8). **29 tests pass.**
- **Step 8/9** `run_ablation.py` (fusion sweep × seeds, AUROC/AUPR mean±std,
  paired t-test); validated by a capped CPU smoke.
- Pushed branch **`objective1-impl`** to `github.com/jamcy98/Modeling-DTI`.
- Built the Colab GPU notebook; made RDKit optional + bundled processed DAVIS so
  Colab needs only `torch-geometric`; made the clone re-run-safe; added
  private-repo support via **Colab Secrets** (`GH_TOKEN`), never a hardcoded token.
- Repo visibility: being switched to public (verify with the `info/refs` curl).

## 8. Status & next steps

- **Done:** steps 1–7 built and tested; ablation orchestrator + Colab notebook ready.
- **Pending (the key deliverable):** run `run_ablation.py` on a GPU (Colab) →
  the RQ1 fusion-ablation result → interpret (RQ1 supported if `gca` AUPR beats
  the baselines with a small paired-test p).
- **After that:** step 10 — scale to more datasets/splits + external baselines
  (week 2 / Obj2); the Yamanishi/Luo ID→SMILES/FASTA mapping; then Obj2 (feature
  enrichment / cold-start) and Obj3 (interpretability).

## 9. Conventions & gotchas

- Prediction head emits **logits**; apply sigmoid only at inference
  (`model.predict_proba`). Pair with focal/BCE loss.
- `latent_dim = 128` throughout; change in `configs/default.yaml`.
- Reproducibility: fixed seeds, frozen split file `data/splits/davis/S1_seed42.json`,
  pinned deps.
- **Security:** never commit tokens/keys. A GitHub PAT was pasted in chat on
  2026-10-18 and must be revoked. Use Colab Secrets for private-repo cloning.
- Windows console is cp1252 — keep script stdout ASCII (no ±/Δ/→).
