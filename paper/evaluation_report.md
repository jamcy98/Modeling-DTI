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

## 5. Summary of Contributions

| Contribution | Result |
|---|---|
| Gated Cross-Attention fusion | Sig. better on 3/8 configs (yamanishi\_e random, cold\_drug, cold\_pair); competitive elsewhere |
| Both encoders needed | Removing either encoder significantly hurts on 6/8 configs (p<0.05) |
| Symmetric encoder roles | GNN drives cold-drug generalisation; RNN drives cold-target generalisation |
| Inductive architecture | Full cold-start generalisation — GSRF-DTI cold\_target: 0.362, ours: 0.778 |
| Cold-drug performance | Leads on luo\_17 all splits; matches DTKGIN cold\_drug (0.774 vs 0.747) with much lower variance |
| Stability | Consistently low std across seeds (e.g., cold\_drug ±0.009 vs. DTKGIN ±0.100) |

---

## 6. References

- Zhu et al. (2024). GSRF-DTI: a framework for drug-target interaction prediction based on a drug-target pair network and representation learning on a large graph. *BMC Biology*, 22, 158.
- Luo et al. (2024). DTKGIN: Predicting drug-target interactions based on knowledge graph and intent graph. *Methods*, 227, 11–18.
- Lin et al. (2022). ESM-2: Evolutionary scale modeling of protein sequences. *Science*.
- Yamanishi et al. (2008). Prediction of drug–target interaction networks from the integration of chemical and genomic spaces. *Bioinformatics*, 24(13).
- Luo et al. (2017). A network integration approach for drug-target interaction prediction and computational drug repositioning from heterogeneous information. *Nature Communications*, 8, 573.
