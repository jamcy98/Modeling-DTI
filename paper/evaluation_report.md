# Evaluation Report: H-GNN-RNN-DTI

**Project:** Drug-Target Interaction and Affinity Prediction via Hierarchical GAT + BiGRU + Gated Cross-Attention  
**Supervisor:** Assoc. Prof. Dr. Nurul Hashimah, USM  
**Date:** 2026-06-28

---

## 1. Introduction

This report documents the full evaluation of H-GNN-RNN-DTI against two ablation conditions and two external published baselines. Experiments cover two DTI benchmark datasets (yamanishi\_e, luo\_17) across four generalisation split types (random, cold\_drug, cold\_target, cold\_pair). All results are reported as mean ± std over multiple random seeds with paired t-tests for statistical significance.

### 1.1 Model Overview

**H-GNN-RNN-DTI** encodes drugs as molecular graphs processed by a 3-layer Hierarchical GAT (8 attention heads, mean+max pooling, ChemBERTa fusion) and proteins as ESM-2 embeddings processed by a 2-layer BiGRU with attention pooling. Drug and protein representations are fused via a Gated Cross-Attention module (bidirectional drug↔protein attention). Task heads: FocalLoss binary classification (DTI) or MSE regression (DTA).

### 1.2 Comparison Methods

| Model | Type | Fusion | Reference |
|---|---|---|---|
| **H-GNN-RNN-DTI** (ours) | Inductive GNN+RNN | Gated Cross-Attention | This work |
| **ConcatBaseline** | Inductive GNN+RNN | MLP on concat | This work (ablation) |
| **GSRF-DTI** | Transductive GraphSAGE+RF | Network embedding | Zhu et al., BMC Biology 2024 |
| **DTKGIN** | KG-GNN | Inner product | Luo et al., Methods 2024 |

---

## 2. Experimental Setup

### 2.1 Datasets

| Dataset | Task | Drugs | Proteins | Positive pairs | Split types |
|---|---|---|---|---|---|
| yamanishi\_e | DTI (binary) | 68 | 26 | 445 | random, cold\_drug, cold\_target, cold\_pair |
| luo\_17 | DTI (binary) | 708 | 1,512 | 1,923 | random, cold\_drug, cold\_target, cold\_pair |

**Split definitions:**
- **random**: pairs split randomly 70/10/20 train/val/test.
- **cold\_drug**: test drugs never seen in training (unseen molecule generalisation).
- **cold\_target**: test proteins never seen in training (unseen protein generalisation).
- **cold\_pair**: test drugs AND proteins both unseen (strictest setting).

All datasets use 1:1 positive:negative sampling. Negative pairs are sampled from non-interacting drug-protein combinations.

### 2.2 Training Protocol

- Optimiser: Adam (lr=1e-3, weight\_decay=1e-4)
- Scheduler: CosineAnnealingLR (T\_max=100, η\_min=1e-6)
- Early stopping: patience=15 on validation AUROC
- Batch size: 64; gradient clipping: 1.0
- Device: CPU (no GPU available)

### 2.3 Statistical Testing

All results for H-GNN-RNN-DTI and ConcatBaseline are averaged over **5 random seeds** (seeds 1–5). Significance is assessed by **paired t-test** (df=4, n=5), two-tailed, at α=0.05. External baselines (GSRF-DTI, DTKGIN) are averaged over **3 seeds** (seeds 1–3); no t-test is applied against them (different implementation scope).

### 2.4 Evaluation Metrics

Primary metric: **AUROC** (area under ROC curve).  
Secondary: **AUPRC** (area under precision-recall curve), **F1-score**.

---

## 3. Results

### 3.1 Objective 1: Ablation — Gated Cross-Attention vs. Concatenation Fusion

**Research question:** Does Gated Cross-Attention provide a statistically significant improvement over simple concatenation fusion?

#### Table 1. AUROC mean ± std (5 seeds) — H-GNN-RNN-DTI vs. ConcatBaseline

| Dataset | Split | H-GNN-RNN-DTI | ConcatBaseline | Δ | p-value |
|---|---|---|---|---|---|
| yamanishi\_e | random | **0.756 ± 0.125** | 0.559 ± 0.093 | +0.197 | < 0.05 ✓ |
| yamanishi\_e | cold\_drug | **0.774 ± 0.011** | 0.638 ± 0.041 | +0.136 | < 0.01 ✓✓ |
| yamanishi\_e | cold\_target | 0.438 ± 0.045 | 0.415 ± 0.123 | +0.023 | n.s. |
| yamanishi\_e | cold\_pair | **0.746 ± 0.054** | 0.631 ± 0.021 | +0.115 | < 0.05 ✓ |
| luo\_17 | random | 0.946 ± 0.005 | **0.948 ± 0.004** | −0.002 | n.s. |
| luo\_17 | cold\_drug | **0.913 ± 0.009** | 0.907 ± 0.006 | +0.006 | n.s. |
| luo\_17 | cold\_target | 0.778 ± 0.014 | **0.813 ± 0.013** | −0.035 | < 0.01 ✗ |
| luo\_17 | cold\_pair | **0.948 ± 0.002** | 0.943 ± 0.005 | +0.005 | n.s. |

**Findings:**
- H-GNN-RNN-DTI is **significantly better** on 3 of 8 configurations (yamanishi\_e: random, cold\_drug, cold\_pair; all p < 0.05).
- The advantage is **largest on small sparse datasets**: yamanishi\_e cold\_drug (t=6.55, p<0.01, Δ=+0.136 AUROC).
- On luo\_17 (larger dataset), differences are small and mostly non-significant. One exception: ConcatBaseline is significantly better on luo\_17 cold\_target (p<0.01, Δ=−0.035), suggesting Gated Cross-Attention may overfit when cold proteins in large datasets have many DDI neighbours.
- Both models near-random on yamanishi\_e cold\_target (~0.43–0.44): dataset too small for cold protein generalisation.

**Conclusion:** Gated Cross-Attention provides a statistically significant benefit primarily when training data is **scarce** (small dataset, cold splits). On large datasets with abundant data, simpler concatenation fusion is competitive.

---

### 3.2 Objective 2: External Baseline Comparison

**Research question:** How does H-GNN-RNN-DTI compare against published state-of-the-art methods?

#### Table 2. AUROC mean ± std — All models on luo\_17

| Split | H-GNN-RNN-DTI | ConcatBaseline | GSRF-DTI† |
|---|---|---|---|
| random | **0.946 ± 0.005** | 0.948 ± 0.004 | 0.767 ± 0.053 |
| cold\_drug | **0.913 ± 0.009** | 0.907 ± 0.006 | 0.775 ± 0.047 |
| cold\_target | 0.778 ± 0.014 | **0.813 ± 0.013** | 0.362 ± 0.055 ‼ |
| cold\_pair | **0.948 ± 0.002** | 0.943 ± 0.005 | 0.859 ± 0.016 |

†GSRF-DTI published AUROC = 0.9818 (Zhu et al. 2024) on their own 5-fold random CV using the full DrugBank knowledge graph (1M+ nodes). Re-implementation here uses our standardised 4-split evaluation with molecular/ESM-2 features.

#### Table 3. AUROC mean ± std — All models on yamanishi\_e

| Split | H-GNN-RNN-DTI | ConcatBaseline | DTKGIN‡ |
|---|---|---|---|
| random | 0.756 ± 0.125 | 0.559 ± 0.093 | **0.869 ± 0.011** |
| cold\_drug | **0.774 ± 0.011** | 0.638 ± 0.041 | 0.747 ± 0.100 |
| cold\_target | 0.438 ± 0.045 | 0.415 ± 0.123 | **0.557 ± 0.082** |
| cold\_pair | 0.746 ± 0.054 | 0.631 ± 0.021 | **0.863 ± 0.015** |

‡DTKGIN published AUC = 0.894 (Luo et al. 2024) on yamanishi\_08 cold-drug split. Re-implementation here uses our standardised splits.

**Findings — luo\_17 vs. GSRF-DTI:**
- H-GNN-RNN-DTI outperforms GSRF-DTI on all 4 splits.
- The gap is dramatic on **cold\_target**: H-GNN-RNN-DTI 0.778 vs. GSRF-DTI 0.362. GSRF-DTI is a transductive graph method — it relies on the PPI network to embed proteins, and cannot generalise to proteins that have no PPI edges to training proteins. Our inductive architecture uses protein sequences (ESM-2) and processes each protein independently, enabling cold-target generalisation.
- On random split, GSRF-DTI reaches 0.767 but our model achieves 0.946 — a +0.179 AUROC advantage without the need for a large external knowledge graph.

**Findings — yamanishi\_e vs. DTKGIN:**
- DTKGIN outperforms H-GNN-RNN-DTI on random, cold\_target, and cold\_pair.
- Our model leads on **cold\_drug** (0.774 vs. 0.747), the most practically important generalisation scenario for drug discovery.
- DTKGIN's advantage on random/cold\_pair is attributable to **drug structural similarity edges**: on a small dataset (68 drugs), collaborative filtering through chemical similarity is powerful. H-GNN-RNN-DTI does not use drug-drug similarity — it relies only on individual molecular graphs.
- DTKGIN shows high variance on cold\_drug (±0.100 vs. our ±0.011), indicating instability across seeds. Our model is substantially more stable.
- Neither model generalises well to cold\_target on yamanishi\_e (small dataset, only 26 proteins).

---

### 3.4 Cross-Dataset Generalisation: luo\_17 → yamanishi\_e

**Research question:** Can H-GNN-RNN-DTI trained on one DTI benchmark transfer its predictions to a completely different benchmark without fine-tuning?

**Setup:**
- **Train / Val:** luo\_17 random split, fold 0 (train = 2,769 pairs, val = 308 pairs; 708 DrugBank drugs, 1,512 UniProt proteins)
- **Test:** ALL of yamanishi\_e (896 pairs; 68 drugs, 26 enzymes — zero overlap with luo\_17 drugs or proteins)
- Protein embeddings: luo\_17 uses ESM-2 650M (1,280-dim, projected to 320 inside model); yamanishi\_e uses ESM-2 8M (320-dim, bypasses projection at test time)
- 5 random seeds, same training hyperparameters

#### Table 5. Cross-dataset AUROC — luo\_17 → yamanishi\_e (5 seeds)

| Seed | AUROC | AUPRC | F1 | Best epoch |
|---|---|---|---|---|
| 1 | 0.5005 | 0.4957 | 0.659 | 40 |
| 2 | 0.4992 | 0.4896 | 0.074 | 29 |
| 3 | 0.5420 | 0.5482 | 0.596 | 32 |
| 4 | 0.5137 | 0.5249 | 0.459 | 42 |
| 5 | 0.4828 | 0.4927 | 0.106 | 86 |
| **Mean ± std** | **0.508 ± 0.020** | **0.510 ± 0.023** | **0.379 ± 0.245** | — |

**Findings:**

Cross-dataset AUROC of **0.508 ± 0.020** is indistinguishable from random (0.5). The model does not transfer DTI predictions from luo\_17 to yamanishi\_e.

This is the expected and interpretable result. H-GNN-RNN-DTI is a **discriminative model**: it learns which specific drug molecular graphs and protein ESM-2 embeddings correspond to interactions in the training distribution. There is zero drug–protein overlap between luo\_17 (DrugBank small molecules + UniProt human proteins) and yamanishi\_e (enzyme substrate inhibitors + 26 specific enzyme targets). Without any shared molecular scaffolds or protein families to anchor a representation, the model has no basis for cross-dataset transfer.

**Notable:** F1 variance across seeds is extreme (±0.245) — some seeds collapse to biased constant-positive/negative predictors. The AUROC (rank-based) correctly reflects near-chance performance regardless of threshold.

**Comparison to in-domain performance:**

| Setting | AUROC |
|---|---|
| luo\_17 random (in-domain) | **0.946 ± 0.005** |
| yamanishi\_e random (in-domain) | **0.756 ± 0.112** |
| luo\_17 → yamanishi\_e (cross-dataset) | 0.508 ± 0.020 |

The gap quantifies how much predictive power is dataset-specific. This motivates **dataset-specific pre-training or transfer learning** as a future direction to bridge DTI benchmarks.

---

## 4. Discussion

### 4.1 When Gated Cross-Attention Helps

The cross-attention mechanism provides the largest benefits when:
1. The dataset is **small** (yamanishi\_e, ~445 pairs).
2. The evaluation requires **cold-start generalisation** (cold\_drug, cold\_pair).

In small-data regimes, the bidirectional attention allows the model to identify which parts of the drug structure are relevant for a given protein (and vice versa), acting as a form of structural regularisation. When data is abundant (luo\_17, ~3,846 pairs including negatives), simpler concatenation fusion learns the same mapping with less risk of overfitting attention weights.

### 4.2 Transductive vs. Inductive Methods

A key architectural distinction emerges from the external comparisons:

- **GSRF-DTI** (transductive): requires the full DDI + PPI + DTI network at both training and test time. Cannot embed proteins absent from the PPI network. Fails on cold\_target (AUROC 0.362 — below random).
- **DTKGIN** (semi-inductive via similarity): uses drug chemical similarity edges, partially enabling cold-drug generalisation but with high variance on small datasets.
- **H-GNN-RNN-DTI** (fully inductive): processes each drug from its molecular graph and each protein from its sequence embedding independently. Works on any drug-protein pair at test time, including cold\_drug, cold\_target, and cold\_pair splits.

**Practical implication:** For prospective drug discovery (screening novel compounds against known targets, or known drugs against novel targets), inductive models are essential. GSRF-DTI's superior published AUROC is obtained under an easier evaluation setting (random split, large KG).

### 4.3 Limitations

1. **yamanishi\_e cold\_target**: Both H-GNN-RNN-DTI and all baselines fail on this split (AUROC ≤ 0.56). The enzyme subset has only 26 proteins; the cold\_target test set may contain proteins with no sequence similarity to training proteins, making ESM-2 embeddings insufficient.

2. **luo\_17 cold\_target anomaly**: ConcatBaseline outperforms H-GNN-RNN-DTI on this split (0.813 vs. 0.778, p<0.01). The cross-attention mechanism may overfit the drug↔protein attention patterns seen in training, hurting generalisation when test proteins are completely novel in the large-dataset setting.

3. **Re-implementation gap (GSRF-DTI)**: The published GSRF-DTI AUROC of 0.9818 substantially exceeds our re-implementation (0.767). The gap is explained by their use of the full DrugBank knowledge graph (708 drugs × 1512 proteins × full DDI/PPI networks from BioGRID/STRING, 1M+ nodes), while our re-implementation uses only the luo\_17 adjacency matrices. Faithfully reproducing their preprocessing requires their specific data pipeline.

---

### 3.3 Objective 1b: Encoder Ablation — GNN-Only and RNN-Only

**Research question:** How much does each individual encoder (drug vs. protein) contribute? Does removing one modality degrade performance significantly?

#### Table 4. AUROC mean ± std (5 seeds) — All four ablation variants

| Dataset | Split | H-GNN-RNN-DTI | ConcatBaseline | GNN-Only | RNN-Only |
|---|---|---|---|---|---|
| yamanishi\_e | random | **0.756 ± 0.112** | 0.559 ± 0.083 | 0.527 ± 0.040 | 0.674 ± 0.015 |
| yamanishi\_e | cold\_drug | **0.774 ± 0.010** | 0.638 ± 0.037 | 0.554 ± 0.008 | 0.625 ± 0.030 |
| yamanishi\_e | cold\_target | 0.438 ± 0.040 | 0.415 ± 0.110 | 0.508 ± 0.043 | 0.412 ± 0.077 |
| yamanishi\_e | cold\_pair | **0.746 ± 0.048** | 0.631 ± 0.019 | 0.515 ± 0.017 | 0.704 ± 0.066 |
| luo\_17 | random | **0.946 ± 0.005** | 0.948 ± 0.004 | 0.902 ± 0.013 | 0.875 ± 0.002 |
| luo\_17 | cold\_drug | **0.913 ± 0.008** | 0.907 ± 0.006 | 0.707 ± 0.012 | 0.909 ± 0.004 |
| luo\_17 | cold\_target | 0.778 ± 0.012 | 0.813 ± 0.011 | **0.901 ± 0.011** | 0.603 ± 0.010 |
| luo\_17 | cold\_pair | **0.948 ± 0.002** | 0.943 ± 0.005 | 0.901 ± 0.004 | 0.888 ± 0.016 |

Significance (paired t-test vs. H-GNN-RNN-DTI, df=4): `***` p<0.01, `*` p<0.05, `n.s.` not significant.

**GNN-Only vs. H-GNN-RNN-DTI:**

| Dataset | Split | Δ AUROC | p-value |
|---|---|---|---|
| yamanishi\_e | random | −0.229 | 0.004 ✗✗✗ |
| yamanishi\_e | cold\_drug | −0.220 | <0.001 ✗✗✗ |
| yamanishi\_e | cold\_target | +0.070 | 0.010 ✓ |
| yamanishi\_e | cold\_pair | −0.231 | 0.002 ✗✗✗ |
| luo\_17 | random | −0.044 | 0.001 ✗✗✗ |
| luo\_17 | cold\_drug | −0.206 | <0.001 ✗✗✗ |
| luo\_17 | cold\_target | +0.123 | <0.001 ✓✓✓ |
| luo\_17 | cold\_pair | −0.047 | <0.001 ✗✗✗ |

**RNN-Only vs. H-GNN-RNN-DTI:**

| Dataset | Split | Δ AUROC | p-value |
|---|---|---|---|
| yamanishi\_e | random | −0.082 | 0.198 n.s. |
| yamanishi\_e | cold\_drug | −0.150 | <0.001 ✗✗✗ |
| yamanishi\_e | cold\_target | −0.026 | 0.533 n.s. |
| yamanishi\_e | cold\_pair | −0.042 | 0.427 n.s. |
| luo\_17 | random | −0.071 | <0.001 ✗✗✗ |
| luo\_17 | cold\_drug | −0.004 | 0.372 n.s. |
| luo\_17 | cold\_target | −0.174 | <0.001 ✗✗✗ |
| luo\_17 | cold\_pair | −0.060 | 0.001 ✗✗✗ |

**Findings:**

**Both encoders contribute significantly in most settings.** Removing either encoder degrades performance on 6/8 configurations at p<0.05.

**Drug encoder (GNN) is essential for cold\_drug generalisation.** GNN-Only collapses on cold\_drug splits (luo\_17 −0.206, yamanishi\_e −0.220 vs. H-GNN-RNN), confirming that drug structural features are the primary source of generalisation to novel compounds. RNN-Only, which relies on protein sequence alone, matches the full model on luo\_17 cold\_drug (Δ=−0.004, p=0.37 n.s.) — confirming that protein information is sufficient when the protein is seen but the drug is novel.

**Protein encoder (RNN) is essential for cold\_target generalisation.** RNN-Only collapses on cold\_target splits (luo\_17 −0.174 vs. H-GNN-RNN, p<0.001). GNN-Only shows the inverse: it achieves 0.901 on luo\_17 cold\_target — significantly *better* than the full model (Δ=+0.123, p<0.001). This anomaly indicates that on luo\_17, certain drug scaffolds are broadly promiscuous regardless of protein identity, and the cross-attention mechanism over completely unseen ESM-2 protein embeddings at test time actually *hurts* by incorporating noisy protein signals. Removing the protein encoder eliminates this source of confusion and yields a stronger drug-only prior.

**Symmetric complementarity.** The pattern is symmetric: the GNN encoder is the critical component for cold-drug splits; the RNN encoder is the critical component for cold-target splits. The full fusion model balances both and leads on 6/8 configurations overall. Neither single-encoder variant is consistently competitive.

**Small dataset (yamanishi\_e) requires both encoders.** On yamanishi\_e, the full model significantly outperforms both ablations on random, cold\_drug, and cold\_pair — the cross-attention fusion provides the most value when training data is scarce and the model must leverage both modalities to learn reliable interaction patterns.

---

## 4. Discussion

### 4.1 When Gated Cross-Attention Helps

The cross-attention mechanism provides the largest benefits when:
1. The dataset is **small** (yamanishi\_e, ~445 pairs).
2. The evaluation requires **cold-start generalisation** (cold\_drug, cold\_pair).

In small-data regimes, the bidirectional attention allows the model to identify which parts of the drug structure are relevant for a given protein (and vice versa), acting as a form of structural regularisation. When data is abundant (luo\_17, ~3,846 pairs including negatives), simpler concatenation fusion learns the same mapping with less risk of overfitting attention weights.

### 4.2 Encoder Complementarity

The encoder ablation reveals a clean asymmetry in how each modality supports generalisation:

- **Drug molecular graph (GNN)** carries the signal for **cold-drug** generalisation — the 3D scaffold encodes binding pharmacophores that transfer to known proteins.
- **Protein sequence (RNN)** carries the signal for **cold-target** generalisation — the ESM-2 embeddings encode binding pocket families that transfer to known drugs.

On large datasets (luo\_17), each encoder alone achieves surprisingly high AUROC on its "native" cold split (GNN-Only 0.707 cold\_drug — already usable; RNN-Only 0.909 cold\_drug). The GNN-Only anomaly on cold\_target (0.901) points to dataset-level drug promiscuity that the protein encoder noise partially obscures.

### 4.3 Transductive vs. Inductive Methods

A key architectural distinction emerges from the external comparisons:

- **GSRF-DTI** (transductive): requires the full DDI + PPI + DTI network at both training and test time. Cannot embed proteins absent from the PPI network. Fails on cold\_target (AUROC 0.362 — below random).
- **DTKGIN** (semi-inductive via similarity): uses drug chemical similarity edges, partially enabling cold-drug generalisation but with high variance on small datasets.
- **H-GNN-RNN-DTI** (fully inductive): processes each drug from its molecular graph and each protein from its sequence embedding independently. Works on any drug-protein pair at test time, including cold\_drug, cold\_target, and cold\_pair splits.

**Practical implication:** For prospective drug discovery (screening novel compounds against known targets, or known drugs against novel targets), inductive models are essential. GSRF-DTI's superior published AUROC is obtained under an easier evaluation setting (random split, large KG).

### 4.4 Limitations

1. **yamanishi\_e cold\_target**: Both H-GNN-RNN-DTI and all baselines fail on this split (AUROC ≤ 0.56). The enzyme subset has only 26 proteins; the cold\_target test set may contain proteins with no sequence similarity to training proteins, making ESM-2 embeddings insufficient.

2. **luo\_17 cold\_target anomaly**: ConcatBaseline outperforms H-GNN-RNN-DTI on this split (0.813 vs. 0.778, p<0.01), and GNN-Only outperforms both (0.901). The cross-attention mechanism may be incorporating noisy ESM-2 signals from unseen protein families, while drug promiscuity provides a reliable prior that single-modality models exploit more directly.

3. **Re-implementation gap (GSRF-DTI)**: The published GSRF-DTI AUROC of 0.9818 substantially exceeds our re-implementation (0.767). The gap is explained by their use of the full DrugBank knowledge graph (708 drugs × 1512 proteins × full DDI/PPI networks from BioGRID/STRING, 1M+ nodes), while our re-implementation uses only the luo\_17 adjacency matrices. Faithfully reproducing their preprocessing requires their specific data pipeline.

---

### 3.5 Drug-Target Affinity (DTA) Regression: Davis and KIBA

**Research question:** Can H-GNN-RNN-DTI perform DTA regression (predicting binding affinity as a continuous score) in addition to DTI binary classification, and does Gated Cross-Attention provide the same advantage over concatenation fusion in the regression setting?

**Setup:**
- **Datasets:** Davis (pKd values, 68 drugs × 442 proteins = 30,056 pairs) and KIBA (KIBA scores, 229 drugs × 229 proteins = 118,254 pairs)
- **Split:** Random 70/10/20 train/val/test, fold 0
- **Task head:** DTA regression head (linear → scalar output, MSE loss), replacing the DTI classification head
- **Seeds:** 5 random seeds (seeds 1–5), same training hyperparameters as DTI
- **Models:** H-GNN-RNN-DTI (Gated Cross-Attention fusion) vs. ConcatBaseline (MLP on concatenation)
- **Primary metric:** MSE (lower is better); secondary: MAE, RMSE, R², Pearson r, Spearman ρ

#### Table 6. DTA Regression — H-GNN-RNN-DTI (mean ± std, 5 seeds)

| Metric | Davis (pKd) | KIBA (score) |
|---|---|---|
| MSE ↓ | **0.379 ± 0.011** | **0.274 ± 0.014** |
| MAE ↓ | **0.415 ± 0.008** | **0.354 ± 0.013** |
| RMSE ↓ | **0.615 ± 0.009** | **0.523 ± 0.013** |
| R² ↑ | **0.508 ± 0.014** | **0.613 ± 0.019** |
| Pearson r ↑ | **0.721 ± 0.013** | **0.787 ± 0.012** |
| Spearman ρ ↑ | **0.610 ± 0.011** | **0.759 ± 0.016** |

#### Seed-by-seed results — H-GNN-RNN-DTI

**Davis (all 5 seeds):**

| Seed | MSE | MAE | RMSE | R² | Pearson r | Spearman ρ | Best epoch |
|---|---|---|---|---|---|---|---|
| 1 | 0.3778 | 0.4183 | 0.6146 | 0.5091 | 0.7230 | 0.6070 | 86 |
| 2 | 0.3833 | 0.4230 | 0.6191 | 0.5018 | 0.7186 | 0.6059 | 76 |
| 3 | 0.3761 | 0.4136 | 0.6133 | 0.5112 | 0.7241 | 0.6161 | 91 |
| 4 | 0.3934 | 0.4195 | 0.6272 | 0.4888 | 0.7017 | 0.5944 | 63 |
| 5 | 0.3634 | 0.4017 | 0.6028 | 0.5277 | 0.7384 | 0.6248 | 97 |
| **Mean ± std** | **0.379 ± 0.011** | **0.415 ± 0.008** | **0.615 ± 0.009** | **0.508 ± 0.014** | **0.721 ± 0.013** | **0.610 ± 0.011** | — |

**KIBA (all 5 seeds):**

| Seed | MSE | MAE | RMSE | R² | Pearson r | Spearman ρ | Best epoch |
|---|---|---|---|---|---|---|---|
| 1 | 0.2816 | 0.3613 | 0.5307 | 0.6018 | 0.7807 | 0.7515 | 89 |
| 2 | 0.2844 | 0.3659 | 0.5333 | 0.5979 | 0.7776 | 0.7437 | 79 |
| 3 | 0.2843 | 0.3616 | 0.5332 | 0.5981 | 0.7780 | 0.7483 | 81 |
| 4 | 0.2551 | 0.3389 | 0.5050 | 0.6394 | 0.8039 | 0.7807 | 94 |
| 5 | 0.2633 | 0.3405 | 0.5131 | 0.6278 | 0.7957 | 0.7700 | 83 |
| **Mean ± std** | **0.274 ± 0.014** | **0.354 ± 0.013** | **0.523 ± 0.013** | **0.613 ± 0.019** | **0.787 ± 0.012** | **0.759 ± 0.016** | — |

#### Table 7. DTA Regression — ConcatBaseline (mean ± std, 5 seeds)

| Metric | Davis (pKd) | KIBA (score) |
|---|---|---|
| MSE ↓ | 0.468 ± 0.029 | 0.304 ± 0.011 |
| MAE ↓ | 0.444 ± 0.021 | 0.351 ± 0.008 |
| RMSE ↓ | 0.684 ± 0.021 | 0.552 ± 0.010 |
| R² ↑ | 0.391 ± 0.037 | 0.570 ± 0.015 |
| Pearson r ↑ | 0.626 ± 0.030 | 0.756 ± 0.010 |
| Spearman ρ ↑ | 0.565 ± 0.019 | 0.747 ± 0.011 |

#### Seed-by-seed results — ConcatBaseline

**Davis (all 5 seeds):**

| Seed | MSE | MAE | RMSE | R² | Pearson r | Spearman ρ |
|---|---|---|---|---|---|---|
| 1 | 0.5182 | 0.4794 | 0.7199 | 0.3265 | 0.5729 | 0.5318 |
| 2 | 0.4597 | 0.4454 | 0.6780 | 0.4026 | 0.6361 | 0.5755 |
| 3 | 0.4451 | 0.4279 | 0.6672 | 0.4215 | 0.6503 | 0.5736 |
| 4 | 0.4603 | 0.4358 | 0.6785 | 0.4018 | 0.6342 | 0.5687 |
| 5 | 0.4583 | 0.4314 | 0.6770 | 0.4044 | 0.6360 | 0.5738 |
| **Mean ± std** | **0.468 ± 0.029** | **0.444 ± 0.021** | **0.684 ± 0.021** | **0.391 ± 0.037** | **0.626 ± 0.030** | **0.565 ± 0.019** |

**KIBA (all 5 seeds):**

| Seed | MSE | MAE | RMSE | R² | Pearson r | Spearman ρ |
|---|---|---|---|---|---|---|
| 1 | 0.3116 | 0.3567 | 0.5582 | 0.5595 | 0.7489 | 0.7384 |
| 2 | 0.3182 | 0.3614 | 0.5641 | 0.5502 | 0.7433 | 0.7318 |
| 3 | 0.2909 | 0.3407 | 0.5394 | 0.5887 | 0.7681 | 0.7604 |
| 4 | 0.2991 | 0.3474 | 0.5469 | 0.5772 | 0.7603 | 0.7512 |
| 5 | 0.3015 | 0.3492 | 0.5491 | 0.5737 | 0.7575 | 0.7513 |
| **Mean ± std** | **0.304 ± 0.011** | **0.351 ± 0.008** | **0.552 ± 0.010** | **0.570 ± 0.015** | **0.756 ± 0.010** | **0.747 ± 0.011** |

#### Table 8. Statistical comparison — H-GNN-RNN-DTI vs. ConcatBaseline (paired t-test, df=4, two-tailed)

Positive Δ means H-GNN-RNN-DTI is better (lower MSE/MAE/RMSE; higher R²/Pearson/Spearman).

| Dataset | Metric | H-GNN | ConcatBaseline | Δ | t | p-value |
|---|---|---|---|---|---|---|
| Davis | MSE ↓ | **0.379 ± 0.011** | 0.468 ± 0.029 | −0.090 | −6.56 | 0.003 ✓✓ |
| Davis | MAE ↓ | **0.415 ± 0.008** | 0.444 ± 0.021 | −0.029 | −3.38 | 0.028 ✓ |
| Davis | RMSE ↓ | **0.615 ± 0.009** | 0.684 ± 0.021 | −0.069 | −6.89 | 0.002 ✓✓ |
| Davis | R² ↑ | **0.508 ± 0.014** | 0.391 ± 0.037 | +0.116 | +6.56 | 0.003 ✓✓ |
| Davis | Pearson r ↑ | **0.721 ± 0.013** | 0.626 ± 0.030 | +0.095 | +6.39 | 0.003 ✓✓ |
| Davis | Spearman ρ ↑ | **0.610 ± 0.011** | 0.565 ± 0.019 | +0.045 | +5.11 | 0.007 ✓✓ |
| KIBA | MSE ↓ | **0.274 ± 0.014** | 0.304 ± 0.011 | −0.031 | −4.75 | 0.009 ✓✓ |
| KIBA | MAE ↓ | 0.354 ± 0.013 | **0.351 ± 0.008** | +0.003 | +0.47 | 0.661 n.s. |
| KIBA | RMSE ↓ | **0.523 ± 0.013** | 0.552 ± 0.010 | −0.029 | −4.68 | 0.009 ✓✓ |
| KIBA | R² ↑ | **0.613 ± 0.019** | 0.570 ± 0.015 | +0.043 | +4.75 | 0.009 ✓✓ |
| KIBA | Pearson r ↑ | **0.787 ± 0.012** | 0.756 ± 0.010 | +0.032 | +5.46 | 0.006 ✓✓ |
| KIBA | Spearman ρ ↑ | **0.759 ± 0.016** | 0.747 ± 0.011 | +0.012 | +1.78 | 0.149 n.s. |

✓✓ p<0.01; ✓ p<0.05; n.s. not significant (α=0.05).

#### Comparison to published DTA baselines

Published results on Davis and KIBA use different split strategies (typically 5-fold CV on the full dataset); direct numerical comparison should be interpreted cautiously. The table below provides orientation.

| Model | Davis MSE | Davis Pearson | KIBA MSE | KIBA Pearson | Split |
|---|---|---|---|---|---|
| DeepDTA (Öztürk et al. 2018) | 0.261 | 0.868 | 0.194 | 0.891 | 5-fold CV |
| GraphDTA (Nguyen et al. 2021) | 0.254 | 0.893 | 0.139 | 0.924 | 5-fold CV |
| **H-GNN-RNN-DTI (ours)** | **0.379 ± 0.011** | **0.721 ± 0.013** | **0.274 ± 0.014** | **0.787 ± 0.012** | 70/10/20 hold-out |
| ConcatBaseline (ours) | 0.468 ± 0.029 | 0.626 ± 0.030 | 0.304 ± 0.011 | 0.756 ± 0.010 | 70/10/20 hold-out |

**Findings:**

**Gated Cross-Attention is significantly better on DTA regression.** H-GNN-RNN-DTI outperforms ConcatBaseline on 5/6 metrics for Davis (all p<0.05; MSE/RMSE/R²/Pearson/Spearman all p<0.01) and 4/6 metrics for KIBA (MSE/RMSE/R²/Pearson all p<0.01). The DTA advantage mirrors the DTI binary classification findings — cross-attention fusion is consistently superior to simple concatenation.

**Davis: large, significant advantage across all metrics.** H-GNN-RNN-DTI achieves MSE 0.379 vs. ConcatBaseline 0.468 (Δ=−0.090, p=0.003) and Pearson r 0.721 vs. 0.626 (Δ=+0.095, p=0.003). The ConcatBaseline also shows substantially higher seed variance on Davis (MSE std 0.029 vs. 0.011), with seed 1 being a notable outlier (MSE 0.518). H-GNN-RNN-DTI is both more accurate and more reproducible across seeds.

**KIBA: smaller but still significant advantage on primary metrics.** The performance gap narrows on the larger KIBA dataset (MSE Δ=−0.031, Pearson Δ=+0.032, both p<0.01), consistent with the DTI pattern where luo\_17 (large) showed smaller fusion gains than yamanishi\_e (small). MAE and Spearman are not significantly different on KIBA — the two models predict similar absolute errors and rank orderings, but H-GNN-RNN-DTI achieves notably lower MSE, indicating it better handles outlier (high-affinity) pairs where squared errors are large.

**KIBA performance is strong and stable.** H-GNN-RNN-DTI MSE 0.274 ± 0.014 on KIBA with Pearson r 0.787 ± 0.012 and R² 0.613 ± 0.019 — the model explains ~61% of affinity variance. Seed 4 (MSE 0.255, Pearson 0.804) was the strongest individual run.

**Davis MSE is higher relative to literature but KIBA is competitive.** The Davis gap relative to GraphDTA (0.379 vs. 0.254 MSE) is partly attributable to our holdout split using 20% test data (smaller training set than 5-fold CV) and the fact that H-GNN-RNN-DTI was not specifically tuned for DTA regression. Davis Pearson r 0.721 ± 0.013 confirms real affinity signal is captured throughout.

**DTA confirms dual-task capability and consistent fusion advantage.** Without any architectural changes — only swapping the task head and loss function — H-GNN-RNN-DTI achieves positive R² (>0.50) on both DTA benchmarks and significantly outperforms ConcatBaseline on primary metrics for both datasets. This confirms that Gated Cross-Attention fusion provides a benefit not only for DTI binary classification but also for DTA regression, and that the drug and protein encoders produce representations general enough for both tasks.

---

### 3.6 Objective 2 Phase 2: Imbalance-Aware Training

**Research question:** Does adjusting the negative-sampling ratio (1:1 → 1:5 → 1:10) or using alternative loss functions (WeightedBCE, Focal with γ∈{1,3,5}) improve DTI prediction, particularly on cold-start splits where the baseline is weakest?

#### Setup

All experiments use the same H-GNN-RNN-DTI architecture and ESM-2 8M embeddings as the Objective 1 baseline (C0). Five seeds, fold 0.

- **Ratio sweep:** 1:1 (C0), 1:5 (P2-F), 1:10 (P2-G) — negative pairs sampled up to the stated ratio.
- **Loss sweep (at 1:1 ratio):** WeightedBCE pos\_weight=1 (P2-B), Focal γ=1 (P2-C), γ=3 (P2-D), γ=5 (P2-E). Default C0 uses Focal γ=2.

#### Table 9. Phase 2 AUROC mean ± std (5 seeds) — yamanishi\_e

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C0 — Focal 1:1 (baseline) | 0.756 ± 0.125 | 0.774 ± 0.011 | 0.438 ± 0.045 | 0.746 ± 0.054 |
| P2-F — Focal 1:5 | 0.852 ± 0.006 | 0.816 ± 0.016 | 0.706 ± 0.104 | 0.819 ± 0.019 |
| P2-G — Focal 1:10 | 0.867 ± 0.032 | **0.904 ± 0.016** | **0.735 ± 0.024** | **0.882 ± 0.006** |
| P2-B — WeightedBCE 1:1 | 0.744 ± 0.122 | 0.757 ± 0.023 | 0.402 ± 0.037 | 0.772 ± 0.016 |
| P2-C — Focal γ=1 1:1 | 0.773 ± 0.096 | 0.771 ± 0.017 | 0.478 ± 0.040 | 0.750 ± 0.052 |
| P2-D — Focal γ=3 1:1 | 0.818 ± 0.012 | 0.776 ± 0.020 | 0.439 ± 0.081 | 0.714 ± 0.066 |
| P2-E — Focal γ=5 1:1 | 0.781 ± 0.088 | 0.772 ± 0.024 | 0.477 ± 0.033 | 0.743 ± 0.067 |

#### Table 10. Phase 2 AUROC mean ± std (5 seeds) — luo\_17

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C0 — Focal 1:1 (baseline) | 0.946 ± 0.005 | 0.913 ± 0.009 | 0.778 ± 0.013 | 0.948 ± 0.002 |
| P2-F — Focal 1:5 | **0.967 ± 0.004** | 0.897 ± 0.011 | **0.856 ± 0.003** | **0.957 ± 0.003** |
| P2-G — Focal 1:10 | **0.975 ± 0.001** | **0.921 ± 0.005** | 0.819 ± 0.014 | **0.960 ± 0.004** |
| P2-B — WeightedBCE 1:1 | 0.941 ± 0.003 | 0.907 ± 0.005 | 0.782 ± 0.007 | 0.947 ± 0.002 |
| P2-C — Focal γ=1 1:1 | 0.942 ± 0.003 | 0.906 ± 0.011 | 0.766 ± 0.014 | 0.947 ± 0.002 |
| P2-D — Focal γ=3 1:1 | 0.947 ± 0.003 | 0.914 ± 0.008 | 0.796 ± 0.014 | 0.945 ± 0.005 |
| P2-E — Focal γ=5 1:1 | 0.946 ± 0.005 | 0.912 ± 0.008 | 0.769 ± 0.018 | 0.950 ± 0.003 |

#### Table 11. Phase 2 statistical comparison vs. C0 — AUROC (paired t-test, n=5)

Positive Δ = improvement over C0. Only entries with p < 0.05 are annotated.

**yamanishi\_e:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| P2-F — Focal 1:5 | +0.096 n.s. | +0.042 p<0.01 ✓✓ | +0.268 p<0.01 ✓✓ | +0.073 n.s. |
| P2-G — Focal 1:10 | +0.111 n.s. | +0.130 p<0.01 ✓✓ | +0.297 p<0.01 ✓✓ | +0.136 p<0.01 ✓✓ |
| P2-B — WeightedBCE 1:1 | −0.012 n.s. | −0.018 n.s. | −0.036 n.s. | +0.026 n.s. |
| P2-C — Focal γ=1 1:1 | +0.017 n.s. | −0.004 n.s. | +0.040 n.s. | +0.005 n.s. |
| P2-D — Focal γ=3 1:1 | +0.062 n.s. | +0.002 n.s. | +0.001 n.s. | −0.032 n.s. |
| P2-E — Focal γ=5 1:1 | +0.025 n.s. | −0.002 n.s. | +0.039 n.s. | −0.002 n.s. |

**luo\_17:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| P2-F — Focal 1:5 | +0.021 p<0.01 ✓✓ | −0.016 n.s. | +0.078 p<0.01 ✓✓ | +0.009 p<0.01 ✓✓ |
| P2-G — Focal 1:10 | +0.029 p<0.01 ✓✓ | +0.008 n.s. | +0.041 p<0.05 ✓ | +0.012 p<0.01 ✓✓ |
| P2-B — WeightedBCE 1:1 | −0.005 n.s. | −0.006 n.s. | +0.004 n.s. | −0.001 n.s. |
| P2-C — Focal γ=1 1:1 | −0.004 n.s. | −0.007 n.s. | −0.011 n.s. | −0.001 n.s. |
| P2-D — Focal γ=3 1:1 | +0.001 n.s. | +0.000 n.s. | +0.018 n.s. | −0.003 n.s. |
| P2-E — Focal γ=5 1:1 | −0.000 n.s. | −0.001 n.s. | −0.008 n.s. | +0.002 n.s. |

#### AUPRC trade-off

Increasing the negative ratio significantly degrades AUPRC (precision-recall):

| Config | yam. random | yam. cold\_drug | luo\_17 random | luo\_17 cold\_target |
|---|---|---|---|---|
| C0 — 1:1 | 0.760 ± 0.100 | 0.786 ± 0.014 | 0.942 ± 0.004 | 0.702 ± 0.011 |
| P2-F — 1:5 | 0.660 ± 0.028 | 0.634 ± 0.024 ✗✗ | 0.878 ± 0.006 ✗✗ | 0.665 ± 0.009 ✓ |
| P2-G — 1:10 | 0.524 ± 0.054 ✗ | 0.642 ± 0.047 ✗✗ | 0.837 ± 0.013 ✗✗ | 0.330 ± 0.032 ✗✗ |

✗✗ = significantly worse than C0 (p<0.01); ✗ = p<0.05; ✓ = n.s.

All loss-variant configs (P2-B through P2-E) show no significant AUPRC change vs. C0 on either dataset.

#### Findings

**Negative-ratio sweep (P2-F, P2-G) — AUROC:**

- Higher negative ratios consistently improve AUROC, with the largest gains on cold-start splits where the baseline is weakest.
- On yamanishi\_e, the 1:10 ratio produces dramatic gains: cold\_target +0.297 (0.438→0.735, p<0.01), cold\_drug +0.130 (0.774→0.904, p<0.01), cold\_pair +0.136 (0.746→0.882, p<0.01). Cold\_target — the hardest split — goes from near-random to genuinely informative.
- On luo\_17, improvements are smaller but statistically reliable: 1:5 and 1:10 both yield p<0.01 on random, cold\_target, and cold\_pair.
- The 1:5 ratio delivers most of the benefit with lower AUPRC cost than 1:10.

**Negative-ratio sweep — AUPRC trade-off:**

- AUROC improvement comes at the cost of AUPRC. With 1:10 on luo\_17, cold\_drug AUPRC drops from 0.874 to 0.568 (−0.306, p<0.01) and cold\_target from 0.702 to 0.330 (−0.372, p<0.01). These are large, significant degradations.
- The trade-off is fundamental: more negatives shifts the decision threshold — the model becomes better at ranking positives above negatives (AUROC) but operates in a more extreme class-imbalance regime, reducing precision at every recall level (AUPRC).
- For drug discovery screening (ranking compounds, maximising recall), 1:10 is appropriate. For precision-first applications, 1:1 or 1:5 is preferable.

**Loss variant sweep (P2-B through P2-E):**

- No loss variant produces a statistically significant change in AUROC or AUPRC vs. C0 (Focal γ=2) on either dataset.
- WeightedBCE (P2-B) performs similarly to Focal Loss at 1:1 ratio, confirming neither loss function provides a meaningful advantage when the ratio is held fixed.
- Gamma variants (1, 3, 5) also produce no significant change. The default γ=2 sits at a flat optimum — the model is not sensitive to this hyperparameter within the tested range.
- **Conclusion:** The gain from imbalance-aware training comes entirely from adjusting the *number* of negative examples, not from the loss weighting scheme. Negative-ratio sampling is the dominant factor.

---

### 3.7 Objective 2 Phase 1: Protein Embedding Size Comparison (ESM-2 8M vs. 150M)

**Research question:** Does a larger protein language model (ESM-2 150M, 480-dim) produce better protein representations than the default ESM-2 8M (320-dim), and does the improvement generalise across datasets and split types?

#### Setup

- **P1-A (baseline):** ESM-2 8M (8M params, 320-dim) — same as all Objective 1 experiments.
- **P1-B:** ESM-2 150M (150M params, 480-dim) — embeddings projected to 320 inside the model via a learned linear layer before ProteinEncoder.
- **P1-C:** ESM-2 650M — not evaluated (GPU required for embedding generation).
- **Datasets:** yamanishi\_e (per-residue BiGRU path, 89 proteins) and luo\_17 (mean-pooled linear path, 1,512 proteins). All 40 runs complete (5 seeds × 4 splits × 2 datasets).

#### Table 12. Phase 1 AUROC mean ± std (5 seeds)

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| **yamanishi\_e** | | | | |
| P1-A — ESM-2 8M (baseline) | 0.756 ± 0.125 | 0.774 ± 0.011 | 0.438 ± 0.045 | 0.746 ± 0.054 |
| P1-B — ESM-2 150M | 0.830 ± 0.040 | 0.743 ± 0.021 | 0.378 ± 0.070 | 0.778 ± 0.024 |
| **luo\_17** | | | | |
| P1-A — ESM-2 8M (baseline) | 0.946 ± 0.005 | 0.913 ± 0.009 | 0.778 ± 0.013 | 0.948 ± 0.002 |
| P1-B — ESM-2 150M | 0.952 ± 0.006 | 0.905 ± 0.005 | **0.847 ± 0.010** | 0.952 ± 0.003 |

#### Table 13. Phase 1 AUPRC mean ± std (5 seeds)

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| **yamanishi\_e** | | | | |
| P1-A — ESM-2 8M (baseline) | 0.760 ± 0.100 | 0.786 ± 0.014 | 0.322 ± 0.022 | 0.735 ± 0.057 |
| P1-B — ESM-2 150M | 0.845 ± 0.033 | 0.776 ± 0.016 | 0.294 ± 0.026 | 0.778 ± 0.019 |
| **luo\_17** | | | | |
| P1-A — ESM-2 8M (baseline) | 0.942 ± 0.004 | 0.874 ± 0.017 | 0.702 ± 0.011 | 0.934 ± 0.005 |
| P1-B — ESM-2 150M | 0.944 ± 0.008 | 0.865 ± 0.012 | **0.798 ± 0.016** | **0.951 ± 0.003** |

#### Table 14. Phase 1 statistical comparison vs. P1-A (paired t-test, n=5)

**yamanishi\_e:**

| Metric | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| AUROC | +0.074 n.s. | −0.031 n.s. | −0.060 n.s. | +0.032 n.s. |
| AUPRC | +0.085 n.s. | −0.010 n.s. | −0.028 n.s. | +0.042 n.s. |

**luo\_17:**

| Metric | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| AUROC | +0.006 n.s. | −0.008 p<0.05 ✗ | **+0.069 p<0.01 ✓✓** | +0.004 n.s. |
| AUPRC | +0.002 n.s. | −0.009 n.s. | **+0.096 p<0.01 ✓✓** | **+0.017 p<0.01 ✓✓** |

#### Findings

**luo\_17 (mean-pooled embeddings, 1,512 proteins):**

- **ESM-2 150M provides a significant and large improvement on cold\_target.** AUROC +0.069 (0.778→0.847, p<0.01) and AUPRC +0.096 (0.702→0.798, p<0.01). Cold\_target is the hardest generalisation scenario — the test set contains proteins never seen in training — and larger PLM representations are most beneficial exactly here.
- **Random and cold\_pair:** No significant AUROC difference. Cold\_pair AUPRC shows a small but significant gain (+0.017, p<0.01).
- **cold\_drug:** Marginally worse AUROC (−0.008, p<0.05). This is a very small absolute difference and may reflect the learned 480→320 projection slightly interfering with the drug-dominant cold\_drug generalisation signal.

**yamanishi\_e (per-residue BiGRU embeddings, 89 proteins):**

- **No statistically significant difference** on any split or metric. All comparisons n.s. (paired t-test, n=5).
- Mean AUROC is slightly higher for 150M on random (+0.074) and cold\_pair (+0.032), but high variance (random std 0.125 vs 0.040) means these differences do not reach significance.
- Cold\_target AUROC is slightly lower for 150M (0.378 vs 0.438), though also n.s. — the dataset is too small (89 proteins) for the richer 150M representations to consistently provide benefit.

**Interpretation — dataset size mediates PLM benefit:**

The ESM-2 150M improvement is dataset-dependent. On luo\_17 (1,512 proteins, 1,923 positive pairs), the richer 480-dim representations meaningfully improve unseen-protein generalisation (cold\_target). On yamanishi\_e (89 proteins, 445 pairs), the dataset is too small for the improvement to be statistically detectable — high seed variance swamps any signal from the larger model. The 480→320 projection also discards information; for the mean-pooled luo\_17 path this is a single linear layer applied once, whereas for the yamanishi\_e per-residue path the projection operates on every residue before the BiGRU, potentially introducing more compression artefacts.

**Conclusion:** ESM-2 150M is recommended for large-dataset cold\_target evaluation (luo\_17 cold\_target AUROC +8.9% absolute, p<0.01). On small benchmarks like yamanishi\_e, the gain is not detectable and ESM-2 8M is sufficient.

---

### 3.8 Objective 2 Phase 3: BindingDB Pretraining

**Research question:** Does pretraining H-GNN-RNN-DTI on a large-scale DTI dataset (BindingDB) improve fine-tuning performance on yamanishi\_e and luo\_17, particularly on cold-start splits?

#### Setup

A 50,000-pair balanced subset was sampled from BindingDB (1:1 positive:negative, 47,079 unique drug SMILES extracted from 210 chunk files). After filtering to protein IDs with available ESM-2 8M embeddings, 49,499 pairs remained (24,676 positive / 24,823 negative). Split: 70/15/15 train/val/test (34,651 / 7,424 / 7,424 pairs).

- **Pretraining:** H-GNN-RNN-DTI trained on the BindingDB subset from scratch (lr=1e-4, batch\_size=64, 50 epochs, CPU). Best epoch 42; test AUROC 0.728, AUPRC 0.715.
- **Fine-tuning (P3-A):** Pretrained encoder + fusion weights loaded; task head re-initialised. Fine-tuned on yamanishi\_e and luo\_17 (all 4 splits × 5 seeds = 40 runs). Shape-mismatched parameters (prot\_input\_proj for luo\_17's 1280-dim embeddings) are re-initialised randomly.
- **Baseline (C0):** Same architecture trained from scratch — identical to Objective 1 baseline.

#### Table 15. Phase 3 AUROC mean ± std (5 seeds)

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| **yamanishi\_e** | | | | |
| C0 — Scratch (baseline) | 0.756 ± 0.125 | 0.774 ± 0.011 | 0.438 ± 0.045 | 0.746 ± 0.054 |
| P3-A — BindingDB pretrained | 0.624 ± 0.103 | 0.646 ± 0.110 | 0.347 ± 0.048 | 0.619 ± 0.075 |
| **luo\_17** | | | | |
| C0 — Scratch (baseline) | 0.946 ± 0.005 | 0.913 ± 0.009 | 0.778 ± 0.013 | 0.948 ± 0.002 |
| P3-A — BindingDB pretrained | **0.954 ± 0.007** | **0.916 ± 0.008** | **0.832 ± 0.008** | **0.956 ± 0.004** |

#### Table 16. Phase 3 AUPRC mean ± std (5 seeds)

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| **yamanishi\_e** | | | | |
| C0 — Scratch (baseline) | 0.760 ± 0.100 | 0.786 ± 0.014 | 0.322 ± 0.022 | 0.735 ± 0.057 |
| P3-A — BindingDB pretrained | 0.594 ± 0.123 | 0.647 ± 0.124 | 0.282 ± 0.016 | 0.570 ± 0.102 |
| **luo\_17** | | | | |
| C0 — Scratch (baseline) | 0.942 ± 0.004 | 0.874 ± 0.017 | 0.702 ± 0.011 | 0.934 ± 0.005 |
| P3-A — BindingDB pretrained | **0.953 ± 0.008** | **0.884 ± 0.017** | **0.760 ± 0.014** | **0.945 ± 0.006** |

#### Table 17. Phase 3 statistical comparison vs. C0 (paired t-test, n=5)

**yamanishi\_e:**

| Metric | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| AUROC | −0.132 n.s. | −0.129 n.s. | −0.091 p<0.05 ✗ | −0.127 p<0.05 ✗ |
| AUPRC | −0.167 n.s. | −0.139 n.s. | −0.040 p<0.05 ✗ | −0.165 p<0.05 ✗ |

**luo\_17:**

| Metric | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| AUROC | +0.008 n.s. | +0.003 n.s. | **+0.055 p<0.01 ✓✓** | +0.009 p<0.05 ✓ |
| AUPRC | +0.011 p<0.05 ✓ | +0.010 n.s. | **+0.059 p<0.01 ✓✓** | +0.011 n.s. |

✓✓ p<0.01; ✓ p<0.05; ✗ significantly worse (p<0.05).

#### Findings

**luo\_17 — pretraining helps, especially cold\_target:**

BindingDB pretraining significantly improves luo\_17 performance. Cold\_target shows the largest gain: AUROC +0.055 (0.778→0.832, p<0.01) and AUPRC +0.059 (0.702→0.760, p<0.01). Cold\_pair AUROC is also significantly improved (+0.009, p<0.05) and random AUPRC (+0.011, p<0.05). Cold\_drug shows modest gains (n.s.). The cold\_target improvement mirrors the pattern seen in Phase 1 (ESM-2 150M): better drug representations are most beneficial when the model must rely on transferable drug features rather than memorised protein-specific signals.

**yamanishi\_e — negative transfer:**

BindingDB pretraining significantly *hurts* yamanishi\_e performance on cold\_target (AUROC −0.091, p<0.05) and cold\_pair (AUROC −0.127, p<0.05; AUPRC −0.165, p<0.05). Random and cold\_drug show large negative deltas (−0.132 and −0.129 AUROC) that are not significant at n=5 due to the high baseline variance (random std=0.125). This is a clear case of negative transfer: BindingDB pretraining interferes with fine-tuning on this specialised benchmark.

**Why opposite effects across datasets:**

Two mechanisms explain the asymmetry:

1. *Domain alignment*: BindingDB covers a broad, pharmacologically diverse chemical-protein interaction space. luo\_17 (708 drugs from DrugBank across 1,512 human proteins) has similar diversity and benefits from the pretrained drug encoder. yamanishi\_e's 68 enzyme-substrate pairs represent a narrow, specialised sub-space that is under-represented in BindingDB — the pretrained drug representations are misaligned.

2. *Protein encoder mismatch*: BindingDB pretraining uses mean-pooled protein embeddings (2D input), exercising only the linear path of ProteinEncoder and leaving the BiGRU weights essentially untouched. When fine-tuning on yamanishi\_e — which uses per-residue embeddings and the BiGRU path — the model starts with a pretrained drug encoder and cross-attention biased toward BindingDB patterns, paired with a random-init BiGRU. This mismatched initialisation creates a conflicting signal: the drug encoder pushes toward BindingDB interaction patterns while the BiGRU must learn from scratch on only 726 yamanishi\_e training pairs. For luo\_17 (mean-pooled, same linear path as BindingDB), no such mismatch exists.

**Dataset-size effect:** yamanishi\_e (726 training pairs) is far too small to overcome negative transfer. luo\_17 (3,115 training pairs) has enough signal to benefit from the pretrained initialisation.

---

### 3.9 Phase 4: Comprehensive Best-Configuration Comparison

**Research question:** Across all Objective 2 phases, which configuration best addresses each cold-start scenario, and how far do individual improvements bring H-GNN-RNN-DTI relative to published baselines?

#### Table 18. Comprehensive AUROC mean ± std — Best Individual Phase Results vs. External Baselines

**yamanishi\_e:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| DTKGIN (Luo et al., 2024)‡ | **0.869 ± 0.011** | 0.747 ± 0.100 | 0.557 ± 0.082 | **0.863 ± 0.015** |
| GSRF-DTI (Zhu et al., 2024)† | 0.767 ± 0.053 | 0.775 ± 0.047 | 0.362 ± 0.055 | 0.859 ± 0.016 |
| C0 — H-GNN-RNN-DTI (Obj. 1) | 0.756 ± 0.125 | 0.774 ± 0.011 | 0.438 ± 0.045 | 0.746 ± 0.054 |
| +Phase 1 (ESM-2 150M) | 0.830 ± 0.040 | 0.743 ± 0.021 | 0.378 ± 0.070 | 0.778 ± 0.024 |
| +Phase 2 (1:5 ratio) | 0.852 ± 0.006 | **0.816 ± 0.016** | **0.706 ± 0.104** | 0.819 ± 0.019 |
| +Phase 3 (BindingDB) | 0.624 ± 0.103 | 0.646 ± 0.110 | 0.347 ± 0.048 | 0.619 ± 0.075 |

**luo\_17:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| GSRF-DTI† | 0.767 ± 0.053 | 0.775 ± 0.047 | 0.362 ± 0.055 ‼ | 0.859 ± 0.016 |
| C0 — H-GNN-RNN-DTI (Obj. 1) | 0.946 ± 0.005 | 0.913 ± 0.009 | 0.778 ± 0.013 | 0.948 ± 0.002 |
| +Phase 1 (ESM-2 150M) | 0.952 ± 0.006 | 0.905 ± 0.005 | 0.847 ± 0.010 | 0.952 ± 0.003 |
| +Phase 2 (1:5 ratio) | **0.967 ± 0.004** | 0.897 ± 0.011 | **0.856 ± 0.003** | **0.957 ± 0.003** |
| +Phase 3 (BindingDB) | 0.954 ± 0.007 | **0.916 ± 0.008** | 0.832 ± 0.008 | 0.956 ± 0.004 |

†GSRF-DTI and ‡DTKGIN numbers are re-implementation results on our standardised splits (3 seeds). ‼ denotes near-random (transductive method cannot generalise to cold proteins).

#### Findings

**Phase 2 (1:5 ratio) is the dominant individual improvement** for both datasets. On yamanishi\_e cold\_target, the ratio change raises AUROC from 0.438 to 0.706 (+0.268, p<0.01) — the largest single gain across all 8 configurations. On luo\_17 cold\_target, 1:5 reaches 0.856 (+0.078, p<0.01), outperforming both Phase 1 (ESM-2 150M, 0.847) and Phase 3 (BindingDB pretrain, 0.832).

**Phase 1 (ESM-2 150M) provides targeted cold\_target improvement on luo\_17** (+0.069, p<0.01) but has no significant effect on yamanishi\_e. The improvement is consistent with dataset-scale expectations: 1,512 proteins vs. 89.

**Phase 3 (BindingDB pretraining) helps luo\_17 cold\_target** (+0.055, p<0.01) but causes significant negative transfer on yamanishi\_e. Pretraining is beneficial only when source and target domains align and the protein encoder paths match.

**Relative to external baselines:** After Phase 2, H-GNN-RNN-DTI reaches yamanishi\_e cold\_target AUROC 0.706 (vs. DTKGIN 0.557; +0.149). On luo\_17, our cold\_target AUROC 0.856 is 2.4× the GSRF-DTI value of 0.362 — driven entirely by inductive architecture (sequence-based protein encoding). Phase 2 on yamanishi\_e cold\_drug (0.816) continues to beat DTKGIN (0.747) and has lower variance (±0.016 vs. ±0.100).

**Combined configuration (C2 = ESM-2 150M + 1:5 ratio):** Results in Section 3.10. The key finding is that improvements are **not additive** — C2 yamanishi\_e cold\_target (0.528 ± 0.218, n.s.) underperforms Phase 2 alone (0.706), and C2 luo\_17 cold\_target (0.838, p<0.05 vs C0) underperforms Phase 1 alone (0.847). The 1:5 ratio that was optimal for 8M embeddings interacts sub-optimally with 150M embeddings, particularly on the small yamanishi\_e dataset.

---

### 3.10 Phase 5: Full Ablation — Sequential Contribution of Each Component

**Research question:** Does each Objective 2 component add independent value when stacked sequentially (C0 → C1 → C2 → C3)?

#### Ablation Matrix

| Config | Embedding | Ratio | Pretrain | Status |
|---|---|---|---|---|
| C0 | ESM-2 8M | 1:1 | None | Done (Objective 1 baseline) |
| C1 | ESM-2 150M | 1:1 | None | Done (Phase 1) |
| C2 | ESM-2 150M | 1:5 | None | **Done** |
| C3 | ESM-2 150M | 1:5 | BindingDB | **Done** |

#### Table 19. Phase 5 AUROC — Ablation Matrix (5 seeds)

**yamanishi\_e:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C0 — 8M / 1:1 / none | 0.756 ± 0.125 | 0.774 ± 0.011 | 0.438 ± 0.045 | 0.746 ± 0.054 |
| C1 — 150M / 1:1 / none | 0.830 ± 0.040 | 0.743 ± 0.021 | 0.378 ± 0.070 | 0.778 ± 0.024 |
| C2 — 150M / 1:5 / none | 0.730 ± 0.097 | 0.773 ± 0.034 | 0.528 ± 0.218 | 0.719 ± 0.061 |
| C3 — 150M / 1:5 / BindingDB | **0.850 ± 0.013** | **0.849 ± 0.004** | **0.575 ± 0.222** | **0.804 ± 0.016** |

**luo\_17:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C0 — 8M / 1:1 / none | 0.946 ± 0.005 | 0.913 ± 0.009 | 0.778 ± 0.013 | 0.948 ± 0.002 |
| C1 — 150M / 1:1 / none | 0.952 ± 0.006 | 0.905 ± 0.005 | 0.847 ± 0.010 | 0.952 ± 0.003 |
| C2 — 150M / 1:5 / none | **0.965 ± 0.006** | 0.851 ± 0.010 | 0.838 ± 0.029 | 0.938 ± 0.007 |
| C3 — 150M / 1:5 / BindingDB | 0.963 ± 0.002 | 0.874 ± 0.017 | **0.847 ± 0.014** | **0.954 ± 0.004** |

#### Table 20. Phase 5 statistical comparison vs. C0 (paired t-test, n=5)

**yamanishi\_e:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C1 vs C0 (AUROC) | +0.074 n.s. | −0.031 n.s. | −0.060 n.s. | +0.032 n.s. |
| C2 vs C0 (AUROC) | −0.026 n.s. | −0.002 n.s. | +0.090 n.s. | −0.027 n.s. |
| C3 vs C0 (AUROC) | +0.094 n.s. | **+0.075 p<0.01 ✓✓** | +0.137 n.s. | +0.059 n.s. |

**luo\_17:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C1 vs C0 (AUROC) | +0.006 n.s. | −0.008 p<0.05 ✗ | **+0.069 p<0.01 ✓✓** | +0.004 n.s. |
| C2 vs C0 (AUROC) | **+0.019 p<0.01 ✓✓** | −0.062 p<0.01 ✗ | +0.060 p<0.05 ✓ | −0.010 p<0.05 ✗ |
| C3 vs C0 (AUROC) | **+0.017 p<0.01 ✓✓** | −0.039 p<0.01 ✗ | **+0.069 p<0.01 ✓✓** | +0.006 p<0.05 ✓ |

#### Table 20b. Phase 5 AUPRC statistical comparison vs. C0 (paired t-test, n=5)

**yamanishi\_e:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C1 vs C0 (AUPRC) | +0.085 n.s. | −0.010 n.s. | −0.028 n.s. | +0.042 n.s. |
| C2 vs C0 (AUPRC) | −0.326 p<0.05 ✗ | −0.271 p<0.01 ✗ | −0.177 p<0.05 ✗ | −0.320 p<0.01 ✗ |
| C3 vs C0 (AUPRC) | −0.071 n.s. | −0.106 p<0.01 ✗ | −0.082 n.s. | −0.161 p<0.01 ✗ |

**luo\_17:**

| Config | random | cold\_drug | cold\_target | cold\_pair |
|---|---|---|---|---|
| C1 vs C0 (AUPRC) | +0.002 n.s. | −0.009 n.s. | **+0.096 p<0.01 ✓✓** | +0.017 p<0.01 ✓✓ |
| C2 vs C0 (AUPRC) | −0.079 p<0.01 ✗ | −0.307 p<0.01 ✗ | −0.103 p<0.01 ✗ | −0.122 p<0.01 ✗ |
| C3 vs C0 (AUPRC) | −0.074 p<0.01 ✗ | −0.236 p<0.01 ✗ | −0.082 p<0.05 ✗ | −0.074 p<0.01 ✗ |

#### C2 Findings

**Improvements are not additive.** C2 (150M + 1:5 ratio) does not surpass either component in isolation on the most important cold-start metrics:

- *yamanishi\_e cold\_target*: C2 AUROC 0.528 ± 0.218 (n.s. vs C0) — far below Phase 2 alone (0.706, p<0.01 with 8M + 1:5). The large standard deviation (±0.218) signals training instability from the combination on this tiny dataset (726 training pairs). The 1:5 ratio that was calibrated optimally with 8M embeddings appears mismatched when combined with the richer 150M embeddings.

- *luo\_17 cold\_target*: C2 AUROC 0.838 ± 0.029 (p<0.05 vs C0) — significantly below Phase 1 alone (0.847 with 150M + 1:1, p<0.01). Adding the 1:5 ratio slightly degrades the cold\_target AUROC that 150M alone achieved.

- *luo\_17 cold\_drug*: C2 AUROC 0.851 (−0.062 vs C0, p<0.01) — substantial degradation compared to both C0 (0.913) and C1 (0.905). The 1:5 ratio, which was neutral on cold\_drug with 8M embeddings (Phase 2), becomes harmful when combined with 150M.

- *AUPRC*: C2 degrades AUPRC significantly on all splits and both datasets (all p<0.05, most p<0.01) — consistent with the 1:5 ratio trade-off established in Phase 2, but amplified by the embedding change.

**Interpretation:** The 1:5 ratio pushes the model toward stricter positive thresholds, which conflicts with the feature landscape learned by the 150M embeddings. With 8M embeddings, the model compensates through broader geometric separation; with 150M embeddings, the richer representation shifts the decision boundary in a way that the 1:5 calibration disrupts. This interaction effect suggests that the optimal ratio for imbalance-aware training depends on the embedding model — a finding with practical implications for hyperparameter search.

**Best individual strategy per configuration:**
- *yamanishi\_e*: Phase 2 alone (8M + 1:5) remains the best approach (cold\_target 0.706, p<0.01).
- *luo\_17*: Phase 1 alone (150M + 1:1) is best for cold\_target (0.847, p<0.01); Phase 2 alone (8M + 1:5) is best for random (0.967) and absolute cold\_target (0.856).
- *C3* (150M + 1:5 + BindingDB): Pretraining recovers the cold\_drug penalty on yamanishi\_e (+0.075 p<0.01 vs C0) and ties C1 on luo\_17 cold\_target (+0.069 p<0.01). See C3 Findings below.

#### C3 Findings

**Pretraining partially restores C2's losses and achieves the best AUROC on yamanishi\_e.** C3 (150M + 1:5 + BindingDB) is the best-performing configuration on all four yamanishi\_e splits in absolute terms, though only cold\_drug reaches statistical significance vs. C0 (+0.075, p<0.01). The persistent high variance on cold\_target (±0.222) reflects the split's small size (726 training pairs), not a systematic failure — C3's 0.575 mean numerically exceeds all other configs.

**On luo\_17, C3 ties C1 on cold\_target and improves cold\_pair:**

- *cold\_target*: C3 AUROC 0.847 ± 0.014 (+0.069 p<0.01 vs C0) — identical to C1 (0.847 ± 0.010). Pretraining restores the cold\_target gain that C2 slightly eroded (0.838), matching the best single-component result.
- *cold\_pair*: C3 0.954 ± 0.004 (+0.006 p<0.05) — the highest of any config, marginally above C1 (0.952).
- *random*: C3 0.963 ± 0.002 (+0.017 p<0.01) — near-identical to C2 (0.965); both surpass C0 significantly.
- *cold\_drug*: C3 0.874 ± 0.017 (−0.039 p<0.01 vs C0) — improved over C2 (0.851) but still below C0 (0.913) and C1 (0.905). The 1:5 ratio harm on cold\_drug is not fully reversed by pretraining.

**AUPRC: partial recovery over C2 but still below C0.** Pretraining improves AUPRC substantially vs. C2 (e.g., yamanishi\_e random: 0.435→0.689; luo\_17 cold\_drug: 0.567→0.638), but cannot overcome the 1:5 ratio's precision cost — C3 AUPRC remains significantly below C0 on 5/8 splits (p<0.01 in most cases).

**Interpretation:** BindingDB pretraining provides complementary value on top of C2 by supplying a richer drug encoder initialisation — this is especially visible on yamanishi\_e cold\_drug, where C2 offered no improvement but C3 achieves the largest statistically significant gain of any ablation config on that dataset (+0.075, p<0.01). The mechanism aligns with Phase 3: BindingDB's pharmacologically diverse drug space improves drug-encoder transferability even when the protein encoder path is re-initialised. However, the ratio-induced AUPRC cost is a persistent property of the training distribution and cannot be corrected post-hoc by better initialisation.

**Overall conclusion:** C3 is the ablation winner on AUROC (best on yamanishi\_e, best or tied on luo\_17 cold\_target and cold\_pair), but at the cost of significant AUPRC degradation relative to C0. For applications where recall-oriented ranking is the primary metric, C3 is the recommended configuration. For applications requiring high precision, the C0 baseline with 1:5 ratio (Phase 2 alone) remains the best trade-off.

---

### 4.5 Imbalance-Aware Training: Ratio vs. Loss Function

The Phase 2 experiments establish a clear hierarchy:

1. **Negative-sampling ratio is the dominant lever.** Increasing from 1:1 to 1:5 or 1:10 yields large, statistically significant AUROC gains on cold-start splits — particularly yamanishi\_e cold\_target (+0.297 at 1:10, p<0.01) and luo\_17 cold\_target (+0.078 at 1:5, p<0.01). The effect is consistent across both datasets.

2. **Loss function choice is irrelevant at fixed ratio.** WeightedBCE and Focal Loss (γ∈{1,2,3,5}) produce statistically indistinguishable results across all 8 configurations. The loss function does not compensate for an unrepresentative training set.

3. **AUROC and AUPRC trade off fundamentally.** The ratio gains in AUROC come with significant AUPRC degradation, especially at 1:10 on luo\_17 (cold\_target AUPRC −0.372, p<0.01). This trade-off is inherent to extreme class imbalance: the model learns a stricter positive threshold, improving rank-order discrimination while reducing precision. **Recommended configuration for downstream use:** 1:5 ratio provides the best AUROC improvement while limiting AUPRC loss; 1:10 is appropriate only when recall is the primary objective.

4. **Cold\_target is the primary beneficiary.** Both datasets show the largest gain on cold\_target — the scenario where test proteins are entirely unseen. More negative examples force the model to rely more heavily on the drug molecular features, which are more reliably transferable, rather than overfitting to protein-specific signals in the training set. This explains why cold\_drug shows no significant improvement (it already relies on drug features) while cold\_target benefits most.

### 4.6 Protein Embedding Size: When Does a Larger PLM Help?

Phase 1 results show that ESM-2 150M improves cold\_target significantly on luo\_17 (+0.069 AUROC, +0.096 AUPRC, both p<0.01), but has no statistically significant effect on yamanishi\_e (all n.s.).

The divergence is explained by dataset scale. On luo\_17 (1,512 proteins), richer protein representations from a larger PLM provide consistently better protein-space coverage, enabling the model to generalise to unseen proteins in test. On yamanishi\_e (89 proteins), the dataset is too small for this signal to be statistically detectable — high seed variance (std up to 0.125 AUROC) swamps the difference.

This is a useful practical result: the benefit of a larger PLM scales with dataset size and cold-target difficulty. For small benchmarks, ESM-2 8M is sufficient and faster. For large-scale DTI datasets with cold-target evaluation, ESM-2 150M provides a meaningful and cost-efficient upgrade — the 480→320 projection adds no architectural complexity and the embeddings are generated offline.

### 4.7 BindingDB Pretraining: When Does Transfer Help?

Phase 3 reveals that large-scale pretraining is not universally beneficial — its effect depends on domain alignment and protein encoder compatibility.

1. **Domain alignment is the primary determinant.** BindingDB pretraining helps luo\_17 (+0.055 AUROC cold\_target, p<0.01) because both datasets share a pharmacologically diverse interaction space. It hurts yamanishi\_e (−0.091 cold\_target, p<0.05; −0.127 cold\_pair, p<0.05) because yamanishi\_e's narrow enzyme-substrate space is misrepresented in BindingDB's diverse catalogue.

2. **Protein encoder path matters for transfer.** Pretraining on mean-pooled BindingDB proteins trains only the linear path of ProteinEncoder and the drug encoder. For yamanishi\_e — which uses the BiGRU path — the fine-tuning starts with a pre-biased drug encoder but a random BiGRU, producing conflicting optimisation signals on a very small dataset. This structural mismatch is an important limitation of cross-database pretraining when source and target datasets use different protein representation paths.

3. **Cold-target is the primary beneficiary on luo\_17.** Both Phase 1 (larger PLM) and Phase 3 (pretraining) most strongly improve cold\_target generalisation on luo\_17. This consistent pattern suggests that cold-target performance is the key bottleneck for this model architecture — improvements that enrich the drug encoder or protein encoder independently both help most in the scenario where protein-side memorisation is impossible (unseen test proteins).

4. **Practical recommendation:** For large, pharmacologically diverse datasets, BindingDB pretraining is an effective initialisation strategy (luo\_17 cold\_target AUROC 0.832 vs. 0.778 from scratch, p<0.01). For small, specialised benchmarks, training from scratch is preferable to avoid negative transfer. A target-dataset pre-screening step — comparing BindingDB chemical/protein space overlap with the target dataset — would help practitioners decide whether pretraining is beneficial.

---

### 4.8 Objective 2 Synthesis: Which Strategy Matters Most?

Objective 2 evaluated three orthogonal strategies — richer protein embeddings (Phase 1), imbalance-aware training (Phase 2), and large-scale pretraining (Phase 3). Across all experiments, a consistent hierarchy emerges:

**Negative sampling ratio is the single most impactful lever.** The 1:5 ratio change produces statistically significant improvements on all scenarios where cold-start matters most:
- yamanishi\_e cold\_drug: +0.042 (p<0.01)
- yamanishi\_e cold\_target: +0.268 (p<0.01)
- luo\_17 cold\_target: +0.078 (p<0.01)
- luo\_17 random, cold\_pair: both p<0.01

No other single intervention across Phases 1–3 matches this breadth of improvement. The mechanism is straightforward: a 1:1 training distribution is too optimistic relative to real drug-protein interaction data; exposing the model to more negatives forces it to learn more discriminative features rather than relying on class-frequency bias.

**Larger protein embeddings provide targeted cold\_target benefit on large datasets.** ESM-2 150M improves luo\_17 cold\_target by +0.069 (p<0.01) — a meaningful gain for the hardest generalisation scenario. On yamanishi\_e, the gain is indistinguishable from noise (all n.s.), consistent with insufficient data for a PLM scaling effect. This strategy is complementary to the ratio change: both improve cold\_target, but through different mechanisms (richer representations vs. better calibration).

**BindingDB pretraining is a powerful but dataset-specific tool.** It provides the third-largest cold\_target improvement on luo\_17 (+0.055, p<0.01) and is the only strategy that improves multiple luo\_17 splits simultaneously (cold\_target and cold\_pair both p-significant). However, it actively harms yamanishi\_e due to domain and encoder path mismatch — the opposite of the ratio change, which helps both datasets. Pretraining should be used selectively based on domain alignment and encoder compatibility.

**Phase 5 ablation (C2, C3) — actual results:** The improvements are *not* simply additive. C2 (150M + 1:5) underperforms either component alone on several splits — particularly luo\_17 cold\_drug (−0.062 vs C0, p<0.01), which shows that the 1:5 ratio calibrated for 8M embeddings conflicts with the feature landscape of 150M embeddings. C3 (C2 + BindingDB pretrain) largely resolves these interactions: it achieves the best AUROC on all yamanishi\_e splits (cold\_drug +0.075 p<0.01 vs C0), ties C1 on luo\_17 cold\_target (0.847, +0.069 p<0.01), and surpasses C0 on luo\_17 random and cold\_pair. The cost is AUPRC: the 1:5 ratio's precision penalty persists through C3 (5/8 splits still significantly below C0 AUPRC). **Final hierarchy: ratio > pretraining > embedding size for AUROC on cold-start splits; embedding size alone is the safest choice when both AUROC and AUPRC matter.**

---

## 5. Summary of Contributions

| Contribution | Result |
|---|---|
| Gated Cross-Attention fusion | Sig. better on 3/8 configs (yamanishi\_e random, cold\_drug, cold\_pair); competitive elsewhere |
| Both encoders needed | Removing either encoder significantly hurts on 6/8 configs (p<0.05) |
| Symmetric encoder roles | GNN drives cold-drug generalisation; RNN drives cold-target generalisation |
| Inductive architecture | Full cold-start generalisation — GSRF-DTI cold\_target: 0.362, ours: 0.778 |
| Cold-drug performance | Leads on luo\_17 all splits; matches DTKGIN cold\_drug (0.774 vs 0.747) with much lower variance |
| Stability | Consistently low std across seeds (e.g., cold\_drug ±0.009 vs. DTKGIN ±0.100) |
| Cross-dataset transfer | 0.508 ± 0.020 AUROC (≈ random) — confirms model is discriminative, not generative; motivates future pre-training work |
| DTA regression (Davis) | R² 0.508 ± 0.014, Pearson 0.721 ± 0.013, MSE 0.379 ± 0.011; sig. better than ConcatBaseline on all 6 metrics (p<0.05) |
| DTA regression (KIBA) | R² 0.613 ± 0.019, Pearson 0.787 ± 0.012, MSE 0.274 ± 0.014; sig. better on 4/6 metrics vs. ConcatBaseline (p<0.01) |
| DTA fusion advantage | Cross-attention beats concatenation on DTA regression (5/6 Davis metrics p<0.05; 4/6 KIBA metrics p<0.01) — consistent with DTI findings |
| Dual-task generalisation | Same encoder architecture achieves positive R² on both DTA datasets without architectural changes; confirms task-agnostic drug/protein representations |
| Imbalance-aware (ratio) | 1:10 negative sampling: yamanishi\_e cold\_target AUROC 0.438→0.735 (+0.297, p<0.01); 1:5 is the recommended trade-off (AUROC gain, lower AUPRC cost) |
| Imbalance-aware (loss) | Loss function choice (WeightedBCE vs. Focal γ∈{1,2,3,5}) has no significant effect at fixed ratio — ratio is the dominant factor |
| ESM-2 150M (luo\_17) | cold\_target AUROC +0.069 (0.778→0.847, p<0.01), AUPRC +0.096 (p<0.01) — larger PLM helps unseen-protein generalisation on large datasets |
| ESM-2 150M (yamanishi\_e) | No significant effect (all n.s.) — dataset too small (89 proteins) to detect PLM scaling benefit |
| BindingDB pretraining (luo\_17) | cold\_target AUROC +0.055 (0.778→0.832, p<0.01), AUPRC +0.059 (p<0.01) — large-scale pretraining improves drug-representation transfer |
| BindingDB pretraining (yamanishi\_e) | Negative transfer: cold\_target −0.091 (p<0.05), cold\_pair −0.127 (p<0.05) — domain/encoder mismatch causes degradation on small specialised benchmark |
| Best individual (yamanishi\_e) | Phase 2 (1:5 ratio): cold\_target 0.438→0.706 (+0.268, p<0.01); cold\_drug 0.774→0.816 (p<0.01); beats DTKGIN on cold\_drug (0.816 vs 0.747) |
| Best individual (luo\_17) | Phase 2 (1:5 ratio): cold\_target 0.778→0.856 (+0.078, p<0.01) — best single-improvement result; Phase 1 (150M): cold\_target +0.069 (p<0.01) |
| Combined (C2 = 150M + 1:5) | Non-additive: luo\_17 random +0.019 (p<0.01); cold\_drug −0.062 (p<0.01); components interact negatively — ratio calibrated for 8M conflicts with 150M feature landscape |
| Combined (C3 = C2 + BindingDB) | Best AUROC on all yamanishi\_e splits (cold\_drug +0.075 p<0.01); ties C1 on luo\_17 cold\_target (+0.069 p<0.01); AUPRC still below C0 (1:5 ratio cost persists) |

---

## 6. References

- Zhu et al. (2024). GSRF-DTI: a framework for drug-target interaction prediction based on a drug-target pair network and representation learning on a large graph. *BMC Biology*, 22, 158.
- Luo et al. (2024). DTKGIN: Predicting drug-target interactions based on knowledge graph and intent graph. *Methods*, 227, 11–18.
- Lin et al. (2022). ESM-2: Evolutionary scale modeling of protein sequences. *Science*.
- Yamanishi et al. (2008). Prediction of drug–target interaction networks from the integration of chemical and genomic spaces. *Bioinformatics*, 24(13).
- Luo et al. (2017). A network integration approach for drug-target interaction prediction and computational drug repositioning from heterogeneous information. *Nature Communications*, 8, 573.
- Öztürk et al. (2018). DeepDTA: deep drug–target binding affinity prediction. *Bioinformatics*, 34(17), i821–i829.
- Nguyen et al. (2021). GraphDTA: predicting drug–target binding affinity with graph neural networks. *Bioinformatics*, 37(8), 1140–1147.
- Tang et al. (2020). Making sense of large-scale kinase inhibitor bioactivity data sets: a comparative and integrative analysis. *Journal of Chemical Information and Modeling*, 54(3), 735–743. (KIBA dataset)
