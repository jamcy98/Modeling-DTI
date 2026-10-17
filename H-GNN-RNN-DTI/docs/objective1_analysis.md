# Objective 1 Analysis — Dynamic Cross-Modal Fusion

**Model:** H-GNN-RNN-DTI/DTA
**Objective 1:** *Design and evaluate an H-GAT–Bi-LSTM architecture with bidirectional Gated Cross-Attention (GCA) for DTI prediction.*
**Research Question 1:** *How effectively can bidirectional Gated Cross-Attention between H-GAT and Bi-LSTM improve cross-modal feature integration for DTI prediction?*

**Purpose of this document:** implementation planning. It is a fresh analysis grounded only in `Draft Proposal_Updated_final.docx` (17 Oct), not an update of any earlier version.
**Scope:** novelty positioning · methodological soundness · feasibility & compute · risks & mitigation · implementation roadmap.
**Status flag:** the agreed working mode is to *attempt the full Objective 1 program within ~1 week, from scratch, with no compute yet secured*. §3 states plainly where that collides with reality; the rest of the document is written so the work is still correct and useful regardless of how far the week gets.

---

## 0. What Objective 1 actually is (and is not)

Objective 1 is a **controlled architectural claim**: holding inputs and training fixed, a *bidirectional gated cross-attention* coupling of a molecular-graph encoder and a protein-sequence encoder integrates the two modalities better than the fusion strategies used in prior work. It is **not** about feature enrichment (that is Objective 2) and **not** about interpretability (Objective 3).

The proposal correctly localises three things inside Objective 1:
1. The **architecture** (§3.6): H-GAT → Bi-LSTM → bidirectional GCA → gated integration → pooling → prediction head.
2. **Class-imbalance handling** as a *controlled training strategy* (focal loss primary; negatives constructed after splitting).
3. The **fusion baselines + fusion-mechanism ablation** (§3.5.1, §3.9.1) that constitute the evidence for RQ1.

Everything below treats those three as the deliverable boundary of Objective 1.

---

## 1. Novelty positioning

### 1.1 The precise claim
No existing DTI model combines **full GNN message-passing** + **full RNN sequence modelling** with a **bidirectional *gated* cross-attention** fusion operating at **atom-level × residue-level granularity before pooling**. The architecture also deliberately omits a second post-pooling fusion gate so that the GCA module's contribution can be isolated in ablation (§3.6.7 note). That isolation discipline is itself part of the novelty argument.

### 1.2 Position against the named Objective 1 baselines

| Baseline | Encoders | Fusion | What it lacks vs. our claim |
|---|---|---|---|
| **GCRNN** | GNN + bipartite RNN + CNN-LSTM | static feature combination | no cross-attention; shallow fusion |
| **MGNDTI** (closest) | GCN + Retentive Net (RNN-like) | **flat multimodal gating** of concatenated features | gating without cross-attention; no atom×residue interaction |
| **DFDGRU-DTI** | random-walk graph emb + BiGRU | multi-head self-attention | self-attention, not bidirectional cross-modal attention |
| **GADFDTI** | **GCN** + self-attention encoder | **gated bidirectional aggregation** (atom–residue) | has gated cross-modal interaction but **no RNN** sequence encoder |
| **BioFusionDTI** | graph + pretrained + attention | attention-based interaction | multimodal attention, but not the GNN+RNN+gated-cross-attn triad |

**The defensible gap:** MGNDTI has gating but not cross-attention; GADFDTI has gated cross-attention but uses a GCN+attention encoder, not an RNN. Our contribution is the *conjunction* — full GNN **and** full RNN co-learning, coupled by **bidirectional gated cross-attention** at pre-pooling granularity.

### 1.3 Novelty risk (be honest)
This is a **combinatorial / integrative** novelty, not a new primitive. A sceptical examiner will ask: *"Is this more than assembling GCA (from GADFDTI) onto a Bi-LSTM?"* The answer must be **empirical**, not rhetorical: the fusion ablation (§1.2 of the roadmap) has to show that (a) GCA beats flat gating and ungated cross-attention *under identical encoders/features*, and (b) the GNN+RNN pairing contributes beyond either encoder alone. If the ablation does not separate GCA from flat gating, the novelty claim weakens to "a competitive hybrid," which is still publishable but is a different, smaller claim. **Plan the ablation as the load-bearing evidence, not a nice-to-have.**

---

## 2. Methodological soundness

### 2.1 The fusion/enrichment confound — the single most important design decision
The architecture in §3.6 writes the encoders with ChemBERTa (drug) and ESM-2 + secondary structure + physicochemical (protein) baked in — i.e. the **C4 full-enriched** configuration. But enrichment (C1→C4) is *Objective 2's* independent variable, and Objective 1 is supposed to isolate fusion. If Objective 1 experiments run on C4, fusion and enrichment effects are confounded in the headline result.

**Recommendation (factorial decoupling):**
- **Objective 1:** fix features at a single **reference configuration**; vary **only** `fusion.type` ∈ {GCA, concat, flat-gate, ungated-cross-attn}.
- **Objective 2:** fix fusion at GCA; vary **features** C1→C4.

This makes each objective a clean one-factor experiment and means the two objectives share one codebase with two different "what varies" switches. In `configs/default.yaml` the reference config is set to **C1 (light)** so the pipeline runs before compute is secured; the RQ1 claim is then *"given identical inputs, GCA > other fusions."* If you prefer the claim to hold at full enrichment, change the reference config to C4 and keep it constant across the fusion variants — the decoupling logic is identical, only the (heavier) compute cost changes. **This choice is yours to ratify; the default is reversible.**

### 2.2 Architecture review (equation-level)
Walking §3.6 as written, the formulation is sound, with a few points to pin down in code:

- **Drug encoder (H-GAT):** attention message passing with multi-head + hierarchical aggregation; atom-level states `D ∈ ℝ^{n×d}` retained for cross-attention. ✔ Correct to keep atom states rather than pooling early.
- **Protein encoder (Bi-LSTM):** residue states `P ∈ ℝ^{m×d}` = concatenated forward/backward. ✔
- **Bidirectional GCA:** `A_DP = softmax(Q_D K_Pᵀ / √d_k) ∈ ℝ^{n×m}` and `A_PD ∈ ℝ^{m×n}`. ✔ Standard scaled dot-product in both directions.
- **Gated integration:** `G_D = σ(W_D[D ∥ D̃] + b_D)`, `D' = G_D ⊙ D̃ + (1−G_D) ⊙ D` (and symmetrically for protein). ✔ The gate blends *cross-attended* (`D̃`) and *original* (`D`) states — this is exactly the "how much to incorporate" control the text argues for.
- **Pooling → joint:** `z_joint = Pool(D') ∥ Pool(P') ∈ ℝ^{2d}`; masked-mean baseline, attention pooling optional. ✔ No second fusion gate — good for isolation.
- **Heads:** sigmoid (classification), linear (regression), trained separately. ✔

**Things to get right in implementation (not errors, but failure points):**
1. **Common latent dim `d` before projection.** H-GAT output dim, Bi-LSTM `2×hidden`, and the GCA projection must all reconcile to a shared `d`/`d_k`. Put an explicit projection layer on each branch; don't assume dims line up.
2. **The `n×m` attention matrix is the memory bottleneck.** For a 1000-residue protein and a 50-atom drug, `A_PD` is 1000×50 per sample — fine; but batching many long proteins multiplies it. Enforce `max_protein_length` (config default 1000) and mask padded positions in the softmax.
3. **Masking is load-bearing twice:** in the cross-attention softmax (ignore padded atoms/residues) and in masked-mean pooling. A masking bug silently leaks padding into attention and inflates/deflates results.
4. **Separate classification and regression runs** (as the proposal states) — different labels, losses, metrics. Multi-task only as an exploratory extension.

### 2.3 Imbalance handling (inside Objective 1)
Correctly scoped as a controlled training strategy: candidate negatives generated **after** splitting (avoids leakage), **focal loss** as the primary imbalance-aware objective, held constant across the fusion comparisons so fusion differences aren't confounded by class-balancing. ✔ Report **AUPR alongside AUROC** — AUPR is the honest metric under imbalance and the proposal already lists it.

### 2.4 Evaluation design for RQ1
- Metrics: AUROC + AUPR (classification), RMSE/MAE/PCC (regression). ✔
- **Repeated runs with different seeds + mean ± std and a significance test** across fusion variants. This is what turns "GCA scored higher" into "GCA is better." The proposal mentions repeated runs; make sure the *fusion ablation specifically* reports variance and a paired test (e.g., paired t-test or Wilcoxon across seeds/folds).
- For the RQ1 claim, **S1 warm-start is sufficient and primary.** Cold-start splits belong to Objective 2's generalisation question — running the fusion ablation across all five split regimes multiplies cost without strengthening the core RQ1 claim. Keep Objective 1 evaluation focused on warm-start (plus optionally one cold split as a robustness check).

### 2.5 Baselines — recommended per-baseline strategy
- **Primary RQ1 evidence = internal fusion ablation.** Implement concat / flat-gate / ungated-cross-attn as *swappable fusion modules* behind one interface (`src/hgnn_rnn_dti/fusion/`), sharing identical encoders, features, splits, and training. This is the only strictly fair comparison and directly realises §3.9.1.
- **External published models:**
  - *GADFDTI, DFDGRU-DTI, BioFusionDTI, GCRNN, MGNDTI* — use **original authors' code** where released and dataset/split-compatible; otherwise **cite reported numbers** on shared benchmarks (DAVIS/KIBA are the common ground).
  - Do **not** attempt to reimplement all five from scratch — that alone exceeds the week and risks unfair, under-tuned reproductions that weaken rather than strengthen the comparison.

---

## 3. Feasibility & compute (the honest part)

### 3.1 The full program, quantified
A *complete* Objective 1 program as the proposal frames the surrounding methodology implies, at minimum:
- datasets: up to 5 (DAVIS, KIBA, BindingDB, Yamanishi_08, Luo_17)
- fusion variants: 4 (GCA + 3 ablation baselines)
- repeated runs: ≥3 seeds
- plus external baselines, plus hyperparameter search (Optuna), plus regression as well as classification.

That is `5 × 4 × 3 = 60` training runs for the *internal ablation alone*, before hyperparameter search, external baselines, or regression. With ESM-2 embeddings and Bi-LSTM over long sequences, each run is non-trivial.

### 3.2 Compute reality
Compute is **not secured**. ESM-2 variants span `t12_35M` (laptop-feasible) to `t33_650M` and larger (needs a real GPU, ~several GB VRAM just for inference). The only way this is tractable without secured GPUs is to **precompute and cache embeddings once** (`scripts/precompute_embeddings.py` → `data/embeddings/`) so training never re-runs the language models. Even then, 60+ runs is not a free-tier-Colab week.

### 3.3 What "attempt the full program in a week" really gets you
Stated plainly, so there are no surprises: **the full program will not finish in a week from scratch with no compute.** Attempting it is still a legitimate choice — it surfaces the real walls empirically — but the honest expectation for ~7 days is:

| Day(s) | Realistic outcome |
|---|---|
| 1 | Environment + data acquisition (DAVIS first — smallest, cleanest) |
| 2 | Preprocessing, graph construction, split generation, leakage tests |
| 2–3 | Feature pipeline + **embedding precompute/cache** |
| 3–4 | Encoders (H-GAT, Bi-LSTM) + GCA + gating + heads, wired end-to-end |
| 4–5 | Training loop + focal loss; **first working run on DAVIS / S1** |
| 5–6 | **Fusion ablation on one dataset** → first real RQ1 evidence |
| 6–7 | Partial scale-out; begin external baselines; document the walls hit |

So the *expected* week-1 artifact is: a working pipeline + the fusion ablation on **one** dataset — which is exactly the core of RQ1. The remaining datasets, external baselines, hyperparameter search, regression, and statistics are **week-2+ and conditional on secured compute.** This document and the code are structured so that reaching only Day 5–6 is still a coherent, defensible result rather than a half-built dead end.

### 3.4 Compute recommendation
1. Precompute embeddings; never train through the LMs.
2. Start on **DAVIS** (smallest) with the **light reference config** (C1 or `esm2_t12_35M`).
3. Prove the fusion ablation on DAVIS/S1 before touching other datasets.
4. Secure compute (university HPC, Colab Pro, or a single rented A100-hour budget) *before* scaling to KIBA/BindingDB and the full `5×4×3` grid.

---

## 4. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **GCA does not beat flat gating / ungated cross-attn** → core novelty weakens | Medium | High | Make the ablation primary and early (Day 5–6); if null, pivot the claim to "competitive hybrid + analysis of *when* GCA helps" — still publishable |
| R2 | **Fusion/enrichment confound** (running Obj1 on C4) | High if unaddressed | High | Fixed reference config in Obj1; features vary only in Obj2 (§2.1) |
| R3 | **Compute/time wall** (full program ≠ 1 week) | Certain | High | Phase by dataset; precompute embeddings; DAVIS-first; §3.3 checkpoints |
| R4 | **Unfair external baselines** (rushed reimplementations) | Medium | Medium | Internal ablation = primary evidence; external = original code / reported numbers only |
| R5 | **Cold-start / split leakage** (negatives or embeddings leaking across splits) | Medium | High | Negatives after split; split-aware preprocessing; a unit test asserting zero drug/target overlap for S2/S3 |
| R6 | **Memory blow-up** from `n×m` cross-attention on long proteins | Medium | Medium | `max_protein_length`, masking, gradient checkpointing if needed |
| R7 | **Dim mismatch** across H-GAT / Bi-LSTM / GCA | Medium | Low | Explicit per-branch projection to shared `d`; shape unit tests |
| R8 | **Non-reproducibility** | Medium | Medium | Global seeding, config capture, logged software/hardware versions, frozen split files |
| R9 | **Scope creep from Obj2/Obj3** into Obj1 | Medium | Medium | Hard boundary: Obj1 = architecture + imbalance + fusion ablation on warm-start only |

---

## 5. Implementation roadmap (build order)

Mapped to the module layout in the repo. Each phase has a concrete "done" test.

1. **Env & data** (`data/`, `scripts/`) — install stack; download DAVIS; sanity-load. *Done:* row counts match published DAVIS. ✅ **COMPLETE (17 Oct):** Python 3.11.15 venv via `uv`; PyTDC 0.4.1 (pinned — see note). DAVIS via TDC = **25,772 pairs = 68 drugs × 379 targets** (a complete matrix), Kd 0.016–10000 nM, no missing SMILES/sequences. Differs from the DeepDTA reference (68/442/30056) because TDC uses 379 unique target sequences; **25,772/68/379 is this project's ground truth.** Cached at `data/raw/davis.csv`. Env quirks: PyTDC must be `==0.4.1` (1.x needs `tiledbsoma`, unbuildable on Windows) and `setuptools<81` (0.4.1 imports `pkg_resources`).
2. **Preprocessing & splits** (`data/`) — SMILES→graph (RDKit), protein tokenisation, negative sampling after split, S1 index files. *Done:* leakage test passes (no train/test entity overlap for the chosen protocol). ✅ **COMPLETE (17 Oct):** All three TDC datasets downloaded (DAVIS 25,772; KIBA 117,657; BindingDB_Kd 52,274). Yamanishi_08 (5,127 interactions: E 2,926 / IC 1,476 / GPCR 635 / NR 90) and Luo_17/DTINet (1,923 interactions, 708×1512) also downloaded via `scripts/download_extra_datasets.py` — but as **ID/matrix data (KEGG/DrugBank/UniProt), not SMILES/FASTA**; they need an ID→structure/sequence mapping before model use (see each `data/raw/<name>/README_PROVENANCE.md`) and are Objective-2 (cold-start) datasets. DAVIS preprocessed at **Kd ≤ 30 nM** → 1,063 pos / 24,709 neg (**4.1% positive** — strong imbalance, validates focal-loss choice). Stratified S1 split 20,618/2,577/2,577, each ~4.1% pos; pair-leakage check passes; 7/7 unit tests pass. Artifacts in `data/processed/davis/` (drug_graphs.pkl, protein_tokens.pkl, pairs.csv, meta.json) + `data/splits/davis/S1_seed42.json`. **Feature dims: atom=80, bond=10, protein_vocab=22** (these are the step-4 encoder input sizes). Env: torch 2.14.1+cpu, PyG 2.8.1, rdkit 2026.9.1. Note: BindingDB has Kd=0 rows (clean before use); DAVIS is clean.
3. **Features + precompute** (`features/`, `scripts/precompute_embeddings.py`) — reference config features; cache to `data/embeddings/`. *Done:* embeddings load in O(1) from cache.
4. **Encoders** (`encoders/`) — H-GAT, Bi-LSTM, each with projection to `d`. *Done:* shape tests `D∈ℝ^{n×d}`, `P∈ℝ^{m×d}`. ✅ **COMPLETE (17 Oct):** `HGATEncoder` (GATv2 ×3 layers, 4 heads, edge features, jumping-knowledge concat, residual; retains atom states → dense `[B,n,d]` + mask) and `BiLSTMEncoder` (embedding → packed 2-layer Bi-LSTM → `[B,m,d]` + mask). `data/dataset.py` assembles PyG `Batch` + padded protein tensors from the step-2 artifacts. Verified on a real DAVIS batch: D `(4,27,128)`, P `(4,1000,128)`, masks reflect true lengths. H-GAT ≈164K params, Bi-LSTM ≈695K.
5. **Fusion modules** (`fusion/`) — one interface, four implementations: `gca`, `concat`, `flat_gate`, `ungated_xattn`. *Done:* each returns `(D', P')` with correct shapes and masking. ✅ **COMPLETE (17 Oct):** `build_fusion(name, dim, attn_dim)` factory + single `forward(D, drug_mask, P, prot_mask) → (D',P')` interface. GCA = bidirectional single-head scaled-dot-product cross-attention (drug↔protein) + learned sigmoid gate `D'=G⊙D̃+(1−G)⊙D`; `ungated_xattn` drops the gate (residual add); `flat_gate` = global gating only (no token attention); `concat` = identity (no interaction). Key-masking verified (padded keys cannot influence output). End-to-end encoders→GCA→masked-mean→`z_joint ∈ ℝ^{2d}` runs on DAVIS. **Full suite 17/17 green (~16s).**
6. **Model + heads** (`models/`) — assemble; classification + regression heads. *Done:* one forward/backward step runs. ✅ **COMPLETE (17 Oct):** `HGNNRNNDTI` wires encoders → `fusion` → masked pooling → `z_joint ∈ ℝ^{2d}` → `PredictionHead` MLP (single logit for classification, single value for regression; **no second post-pooling gate** per §3.6.7). `build_model(cfg)` constructs everything from `configs/default.yaml`, with encoder input dims pulled from the featurizer constants (single source of truth). `utils/config.py` loads/clones YAML. ~1.12M trainable params. Verified on DAVIS: forward gives `[B]` logits (probs in [0,1]); all four fusion variants assemble and run; regression task runs; a BCE loss backpropagates with finite grads. **Full suite 24/24 green (~44s).**
7. **Training** (`training/`) — trainer, focal loss, early stopping, seeding. *Done:* loss decreases on DAVIS; checkpoint saved. ✅ **COMPLETE (17 Oct):** `FocalLoss` (γ=2, α=0.25; the imbalance-aware objective) + `build_loss` (focal/bce/mse); `evaluation/metrics.py` (AUROC+AUPR classification, RMSE/MAE/PCC regression, one-class guard); `utils/seed.py`; `Trainer` (AdamW, grad-clip, early stopping on val AUPR/RMSE, best-checkpoint restore, `max_batches` for quick runs); `scripts/train.py` CLI (fusion/seed/epochs overrides → saves results JSON to `experiments/results/`). **Overfit test proves the pipeline learns**: on a small balanced DAVIS batch, loss drops >40% and train AUPR > 0.8. Training tests 5/5. ⚠️ CPU cost is real — the overfit micro-test alone took ~4 min; full-dataset training needs the GPU that isn't secured yet.
8. **Evaluation** (`evaluation/`) — AUROC/AUPR (+ regression metrics), repeated-run stats. *Done:* metrics reproduce across two identical-seed runs.
9. **Fusion ablation** (`ablation/`) — sweep `fusion.type`, ≥3 seeds, paired significance test. *Done:* **RQ1 result table on DAVIS/S1.** ← core Objective 1 deliverable. 🟡 **ORCHESTRATOR READY (17 Oct), RUN PENDING GPU:** `scripts/run_ablation.py` (via `training/run.py` `run_experiment`) sweeps gca/concat/flat_gate/ungated_xattn × seeds, aggregates AUROC/AUPR mean±std, runs a paired t-test of GCA vs each baseline on AUPR, saves `experiments/results/ablation_<ds>_<split>.json`. Plumbing validated by a capped CPU smoke (clean exit, JSON written). **Compute decision: run on a free cloud GPU** — `notebooks/Objective1_Ablation_Colab.ipynb` (generated by `scripts/make_colab_notebook.py`) clones the repo, installs deps, preprocesses DAVIS, and runs the full ablation on a Colab T4. Fixed a logging crash (None/NaN best metric) and made the summary table ASCII-safe. `data/dataset.py` gained `make_collate(max_protein_length)` as a CPU cost lever.
10. **Scale-out (compute-gated)** — further datasets, external baselines, hyperparameter search, regression, additional split as robustness.

**The minimal defensible Objective 1 result is step 9 on one dataset.** Everything after is strengthening, not foundation.

---

## 6. Open decisions for you to ratify

1. **Reference feature config for Objective 1** — default is **C1 (light)** for the week-1 attempt. Confirm, or set it to C4 (heavier, needs compute) if you want the fusion claim stated at full enrichment.
2. **First dataset** — default **DAVIS**. Confirm or substitute.
3. **ESM-2 variant** when enrichment is turned on later — default `t12_35M` (feasible) vs `t33_650M` (needs GPU).
4. **How hard to chase external baselines in week 1** — recommended: defer to week 2, lead with the internal ablation.

---

*Grounded in `Draft Proposal_Updated_final.docx` (17 Oct 2026): objectives (§1.3), architecture (§3.6), baselines (§3.5.1), feature configs C1–C4 (§3.7), imbalance handling (§3.3.7), evaluation (§3.10), ablation (§3.9), expected outcomes (§3.14).*
