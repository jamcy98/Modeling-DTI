# Objective 1 — Thesis Methods & Results (draft paragraphs)

Ready-to-use prose for the thesis. The **Methods** paragraph is final (it
describes the clean, uniform "up to 50 epochs" protocol). The **Results**
numbers below are from the mixed-budget sweep (completed 2026-10-22); they will
be refreshed from the clean `--fresh` equal-budget re-run once it finishes. The
qualitative conclusion is not expected to change. Full data and caveats:
[`objective1_ablation_results.md`](objective1_ablation_results.md).

---

## Methods

> **Dataset and task.** The fusion mechanisms were evaluated on the DAVIS
> kinase–inhibitor dataset obtained via the Therapeutics Data Commons (25,772
> drug–target pairs; 68 drugs, 379 targets). Continuous dissociation constants
> were binarized using a threshold of Kd ≤ 30 nM, yielding a highly imbalanced
> binary classification task (~4% positive). Pairs were divided under an S1
> warm-start protocol (80/10/10 train/validation/test), with candidate negatives
> constructed only after splitting to prevent leakage.
>
> **Representations and encoders.** To isolate the fusion mechanism, all inputs
> were held fixed at a light reference configuration: each drug as an
> RDKit-derived molecular graph (atom/bond features) and each protein as a
> learned embedding over amino-acid tokens (maximum length 1,000 residues);
> pretrained language-model features were excluded. Drugs were encoded by a
> three-layer hierarchical graph-attention network (H-GAT, four heads) and
> proteins by a two-layer bidirectional LSTM (hidden size 128), both projecting
> to a common 128-dimensional latent space.
>
> **Fusion ablation.** Four interchangeable fusion mechanisms were compared —
> static concatenation, flat gating, ungated cross-attention, and the proposed
> bidirectional gated cross-attention (GCA, attention dimension 128) — with all
> other components held identical, so that differences are attributable solely
> to the fusion strategy. Fused representations were pooled by masked mean and
> passed to a multilayer-perceptron head ([256, 128], dropout 0.2) producing the
> interaction logit.
>
> **Training and evaluation.** All models were trained with the focal loss
> (γ = 2.0, α = 0.25) using Adam (learning rate 1 × 10⁻³, weight decay
> 1 × 10⁻⁵), batch size 32 and gradient clipping at 1.0, for a maximum of 50
> epochs with early stopping (patience 15) on validation AUPR. Each
> configuration was run with three random seeds (42, 43, 44). Given the class
> imbalance, AUPR was adopted as the primary metric and AUROC as secondary;
> results are reported as mean ± standard deviation across seeds, and GCA was
> compared with each baseline using a two-tailed paired t-test on the per-seed
> AUPR values.

---

## Results

> Contrary to the hypothesis underlying RQ1, bidirectional gated cross-attention
> did not improve cross-modal integration. The two simplest mechanisms attained
> the best and most consistent performance — static concatenation
> (AUPR 0.460 ± 0.008) and flat gating (AUPR 0.460 ± 0.021) — while the proposed
> GCA reached only 0.322 ± 0.020 and ungated cross-attention the lowest at
> 0.276 ± 0.036; AUROC followed the same ordering (0.887, 0.890, 0.839, 0.804
> respectively). Paired t-tests confirmed that GCA was significantly
> outperformed by both concatenation (ΔAUPR = −0.139, t = −7.01, p = 0.020) and
> flat gating (ΔAUPR = −0.139, t = −4.88, p = 0.040), and exceeded only ungated
> cross-attention, non-significantly (ΔAUPR = +0.045, t = 3.01, p = 0.095). These
> results indicate that, on DAVIS under the S1 split, cross-modal attention
> between the graph and sequence encoders degrades rather than enhances
> predictive performance, and that a simple concatenation of the independently
> learned embeddings is a strong, stable baseline — suggesting the encoders
> already capture most of the predictive signal, with attention-based fusion
> adding variance and overfitting rather than useful interaction.

---

## Results table (for reference)

| Fusion | AUPR (mean ± std) | AUROC (mean ± std) |
|---|---|---|
| concat | **0.460 ± 0.008** | 0.887 ± 0.008 |
| flat_gate | **0.460 ± 0.021** | 0.890 ± 0.002 |
| gca (proposed) | 0.322 ± 0.020 | 0.839 ± 0.020 |
| ungated_xattn | 0.276 ± 0.036 | 0.804 ± 0.010 |

GCA vs baselines (paired t-test, AUPR, n = 3): vs concat ΔAUPR −0.139, p = 0.020\*;
vs flat_gate −0.139, p = 0.040\*; vs ungated_xattn +0.045, p = 0.095.
(\* significant at α = 0.05.)

> **Status:** numbers above are the mixed-budget sweep; to be replaced with the
> uniform 50-epoch `--fresh` re-run results when available.
