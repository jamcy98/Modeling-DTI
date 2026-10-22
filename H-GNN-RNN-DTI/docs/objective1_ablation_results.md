# Objective 1 — Fusion Ablation Results (RQ1)

**Dataset:** DAVIS · **Split:** S1 (warm-start) · **Label:** Kd ≤ 30 nM (~4% positive)
**Primary metric:** AUPR · **Seeds:** 42, 43, 44 · **Run:** Colab GPU, completed 2026-10-22
**Source:** `MyDrive/HGNN_RNN_DTI/ablation_results/ablation_davis_S1.json`

Reference feature config C1 (light: RDKit graph + basic protein tokens) held fixed;
only `fusion.type` varied (the Obj1 isolation design). Training: focal loss,
early stopping on validation AUPR (patience 15); most runs capped at 50 epochs
(see caveat 2).

## Results (mean ± std over 3 seeds)

| Fusion | AUPR (mean ± std) | AUROC (mean ± std) | epochs/run |
|---|---|---|---|
| **concat** | **0.4604 ± 0.0079** | 0.8869 ± 0.0084 | 50, 50, 50 |
| **flat_gate** | **0.4603 ± 0.0207** | 0.8902 ± 0.0024 | 58, 50, 50 |
| gca | 0.3218 ± 0.0204 | 0.8387 ± 0.0202 | 34, 38, 25 |
| ungated_xattn | 0.2763 ± 0.0364 | 0.8042 ± 0.0097 | 27, 73, 26 |

### Per-run AUPR
| Fusion | seed 42 | seed 43 | seed 44 |
|---|---|---|---|
| gca | 0.3503 | 0.3039 | 0.3111 |
| ungated_xattn | 0.3241 | 0.2689 | 0.2358 |
| flat_gate | 0.4322 | 0.4675 | 0.4813 |
| concat | 0.4495 | 0.4639 | 0.4677 |

## Significance — GCA vs each baseline (paired t-test on AUPR, n=3)

| Comparison | ΔAUPR (gca − baseline) | t | p-value | Verdict |
|---|---|---|---|---|
| gca vs ungated_xattn | +0.0455 | 3.01 | 0.095 | gca better, **not** significant |
| gca vs flat_gate | −0.1386 | −4.88 | **0.040** | gca **significantly worse** |
| gca vs concat | −0.1386 | −7.01 | **0.020** | gca **significantly worse** |

## RQ1 verdict: NOT supported (contradicted)

RQ1 asked whether bidirectional Gated Cross-Attention (GCA) between H-GAT and
Bi-LSTM improves cross-modal fusion vs simpler mechanisms. On DAVIS/S1 it does
**not**:

- GCA is **significantly worse** than both plain concatenation (p=0.020) and
  flat gating (p=0.040) on AUPR.
- GCA beats only ungated cross-attention, and not significantly (p=0.095).
- Ranking: **concat ≈ flat_gate (~0.460) ≫ gca (0.322) > ungated_xattn (0.276).**

**Headline:** the simplest fusion (concatenate the two modality embeddings) ties
for best *and* is the most stable (std 0.008), while adding cross-modal attention
actively hurts. The two attention-based fusions (gca, ungated_xattn) are the two
worst. This matches "Risk R1" in `objective1_analysis.md`: cross-modal attention
is not guaranteed to help, and here it does not.

This is a legitimate, reportable negative result. It reframes Objective 1 from
"GCA is better" to "does fusion complexity help? — on DAVIS, no; simple
concatenation is a strong, stable baseline and attention underperforms it."

## Caveats / threats to validity

1. **Low power:** n=3 seeds. Still, the two negative results for GCA clear
   p<0.05. The positive gca>ungated gap does not (p=0.095).
2. **Non-uniform training budget:** the `--epochs 50` cap was added mid-campaign,
   so the final JSON mixes capped and uncapped runs (ungated seed 43 ran 73
   epochs; flat_gate seed 42 ran 58). gca/concat are effectively uniform. The
   conclusion is robust to this — flat_gate still beats gca even with 2/3 of its
   runs capped at 50 — but for publication, **re-run all 12 under an identical
   50-epoch cap (`--fresh`)** for a clean equal-budget table.
3. **Single dataset / split:** DAVIS, S1 warm-start only. Before firm claims,
   replicate on KIBA and BindingDB and on cold splits (S2/S3). Attention may
   help more on larger/colder regimes.
4. **Encoder signal vs fusion noise:** concat's dominance + low variance suggests
   the H-GAT and Bi-LSTM embeddings already carry the predictive signal, and the
   extra fusion parameters mostly add variance/overfitting on a small (~4%
   positive) dataset.

## Recommended next steps

- Re-run the full sweep under a uniform 50-epoch cap (`--fresh`) to remove
  caveat 2, then lock these as the final RQ1 numbers.
- Extend to KIBA + BindingDB and cold-start splits (ties into Obj2).
- Add external published baselines (DeepDTA, GraphDTA, etc.) for context.
- Given concat ≈ flat_gate at top, consider whether Obj2/Obj3 should build on the
  simpler fusion, and investigate *why* cross-attention hurts (over-parameterisation,
  attention collapse, limited positives) — that mechanism is itself a contribution.
