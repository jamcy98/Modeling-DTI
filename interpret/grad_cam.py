"""
Phase 2 — Graph Grad-CAM

Gradient-weighted Class Activation Mapping for H-GNN-RNN-DTI:
  - Drug atoms    : hooks on the last ResidualGATBlock output
  - Protein residues: hooks on the BiGRU sequence output (requires sequence-mode embeddings)

Grad-CAM score per node j:
    cam[j] = ReLU( mean_c( grad_h[j,c] * h[j,c] ) )

where h is the captured activation and grad_h is the gradient of the
prediction score w.r.t. that activation.

Usage:
    from interpret.grad_cam import compute_all_grad_cam, ensemble_attribution

    result = compute_all_grad_cam(
        model, drug_batch, protein_emb, task='dti',
        protein_emb_seq=protein_emb_seq,  # optional, (1,L,D) — enables protein Grad-CAM
        layer_idx=-1,                      # which GAT layer to hook
    )
    print(result['drug_cam'])          # (N_atoms,) normalised Grad-CAM scores
    print(result['protein_cam'])       # (L,) or None
    print(result['drug_cam_raw'])      # before normalisation
"""

import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')  # avoid OpenMP conflict on Windows
import torch
import torch.nn.functional as F


# ── Hook helpers ──────────────────────────────────────────────────────────────

class _HookStore:
    """Collects forward activations and backward gradient signals via module hooks."""

    def __init__(self):
        self.activations = {}
        self.gradients   = {}
        self._handles    = []

    def register_forward(self, module, key):
        def hook(m, inp, out):
            tensor = out[0] if isinstance(out, tuple) else out
            self.activations[key] = tensor
        h = module.register_forward_hook(hook)
        self._handles.append(h)

    def register_backward(self, module, key):
        def hook(m, grad_in, grad_out):
            g = grad_out[0] if isinstance(grad_out, tuple) else grad_out
            if g is not None:
                self.gradients[key] = g.detach()
        h = module.register_full_backward_hook(hook)
        self._handles.append(h)

    def remove_all(self):
        for h in self._handles:
            h.remove()
        self._handles.clear()


# ── Drug Grad-CAM ─────────────────────────────────────────────────────────────

def drug_grad_cam(model, drug_batch, protein_emb, task, layer_idx=-1):
    """
    Grad-CAM for drug atoms using the specified GAT layer.

    Args:
        model        : HGNN_RNN_DTI in eval mode
        drug_batch   : batched PyG graph (single molecule)
        protein_emb  : (1, D) or (1, L, D) protein embedding tensor
        task         : 'dti' or 'dta'
        layer_idx    : which GAT layer to hook (-1 = last)

    Returns:
        cam_norm   (N_atoms,)  — Grad-CAM scores normalised to [0,1]
        cam_raw    (N_atoms,)  — unnormalised scores
    """
    target_layer = model.drug_encoder.gat_layers[layer_idx]
    store = _HookStore()
    store.register_forward(target_layer, 'drug')
    store.register_backward(target_layer, 'drug')

    try:
        model.eval()
        model.zero_grad()
        with torch.enable_grad():
            prot = protein_emb.detach().clone()
            if prot.shape[-1] != 320:
                prot = model.prot_input_proj(prot)

            drug_repr = model.drug_encoder(drug_batch)
            prot_repr = model.protein_encoder(prot)
            fused     = model.fusion(drug_repr, prot_repr)
            logits    = model.head(fused)

            score = logits[0, 1] if task == 'dti' else logits[0, 0]
            score.backward()

        act  = store.activations.get('drug')   # (N, H)
        grad = store.gradients.get('drug')      # (N, H)

        if act is None or grad is None:
            n = drug_batch.num_nodes
            return torch.zeros(n), torch.zeros(n)

        cam = F.relu((grad * act.detach()).mean(dim=-1))  # (N,)
        return _normalise(cam), cam

    finally:
        store.remove_all()
        model.zero_grad()


# ── Protein Grad-CAM ──────────────────────────────────────────────────────────

def protein_grad_cam(model, drug_batch, protein_emb_seq, task):
    """
    Grad-CAM for protein residues using BiGRU hidden state gradients.

    Args:
        protein_emb_seq : (1, L, D) — FULL SEQUENCE embeddings (not mean-pooled).
                          If mean-pooled (dim==2), returns None.

    Returns:
        cam_norm   (L,)   — per-residue Grad-CAM, normalised to [0,1]
        cam_raw    (L,)   — unnormalised
        grad_norm  (L,)   — pure gradient norm per residue (alternative signal)
    """
    if protein_emb_seq.dim() == 2:
        return None, None, None  # mean-pooled: no per-residue attribution

    store = _HookStore()
    store.register_forward(model.protein_encoder.bigru, 'prot')
    store.register_backward(model.protein_encoder.bigru, 'prot')

    try:
        model.eval()
        model.zero_grad()
        with torch.enable_grad():
            prot = protein_emb_seq.detach().clone()
            if prot.shape[-1] != 320:
                prot = model.prot_input_proj(prot)

            drug_repr = model.drug_encoder(drug_batch)
            prot_repr = model.protein_encoder(prot)
            fused     = model.fusion(drug_repr, prot_repr)
            logits    = model.head(fused)

            score = logits[0, 1] if task == 'dti' else logits[0, 0]
            score.backward()

        act  = store.activations.get('prot')   # (1, L, 2H)
        grad = store.gradients.get('prot')      # (1, L, 2H)

        if act is None or grad is None:
            return None, None, None

        act  = act.squeeze(0)   # (L, 2H)
        grad = grad.squeeze(0)  # (L, 2H)

        cam      = F.relu((grad * act.detach()).mean(dim=-1))  # (L,)
        grad_norm = grad.norm(dim=-1)                           # (L,) — alternative signal

        return _normalise(cam), cam, _normalise(grad_norm)

    finally:
        store.remove_all()
        model.zero_grad()


# ── Combined single-pass ──────────────────────────────────────────────────────

def compute_all_grad_cam(
    model,
    drug_batch,
    protein_emb,
    task,
    protein_emb_seq=None,
    layer_idx=-1,
):
    """
    Compute drug Grad-CAM and (optionally) protein Grad-CAM.

    When protein_emb_seq is provided and is sequence-mode (dim==3), both drug
    and protein Grad-CAM are computed in a single forward+backward pass.
    Otherwise only drug Grad-CAM is computed.

    Args:
        model           : HGNN_RNN_DTI in eval mode
        drug_batch      : batched PyG graph (single molecule)
        protein_emb     : (1, D) or (1, L, D) — used for the model forward pass
        task            : 'dti' or 'dta'
        protein_emb_seq : (1, L, D) — full-sequence embeddings for protein Grad-CAM.
                          Can be the same tensor as protein_emb if it's sequence-mode.
                          Pass None to skip protein Grad-CAM.
        layer_idx       : which GAT layer to hook for drug (-1 = last)

    Returns dict with:
        drug_cam        (N,)   — drug atom Grad-CAM, normalised [0,1]
        drug_cam_raw    (N,)   — unnormalised
        protein_cam     (L,) or None
        protein_cam_raw (L,) or None
        protein_grad_norm (L,) or None  — pure gradient norm per residue
        logits          tensor
        prediction      float
        prediction_prob float
    """
    target_layer    = model.drug_encoder.gat_layers[layer_idx]
    use_prot_cam    = (protein_emb_seq is not None and protein_emb_seq.dim() == 3)

    store = _HookStore()
    store.register_forward(target_layer, 'drug')
    store.register_backward(target_layer, 'drug')
    if use_prot_cam:
        store.register_forward(model.protein_encoder.bigru, 'prot')
        store.register_backward(model.protein_encoder.bigru, 'prot')

    try:
        model.eval()
        model.zero_grad()
        with torch.enable_grad():
            # Use sequence embeddings for the protein if available (enables protein Grad-CAM)
            prot = (protein_emb_seq if use_prot_cam else protein_emb).detach().clone()
            if prot.shape[-1] != 320:
                prot = model.prot_input_proj(prot)

            drug_repr = model.drug_encoder(drug_batch)
            prot_repr = model.protein_encoder(prot)
            fused     = model.fusion(drug_repr, prot_repr)
            logits    = model.head(fused)

            score = logits[0, 1] if task == 'dti' else logits[0, 0]
            score.backward()

        # ── Drug Grad-CAM ────────────────────────────────────────────────────
        act_d  = store.activations.get('drug')
        grad_d = store.gradients.get('drug')
        if act_d is not None and grad_d is not None:
            drug_cam_raw = F.relu((grad_d * act_d.detach()).mean(dim=-1))
            drug_cam     = _normalise(drug_cam_raw)
        else:
            n = drug_batch.num_nodes
            drug_cam_raw = torch.zeros(n)
            drug_cam     = torch.zeros(n)

        # ── Protein Grad-CAM ─────────────────────────────────────────────────
        prot_cam = prot_cam_raw = prot_grad_norm = None
        if use_prot_cam:
            act_p  = store.activations.get('prot')
            grad_p = store.gradients.get('prot')
            if act_p is not None and grad_p is not None:
                act_p  = act_p.squeeze(0)    # (L, 2H)
                grad_p = grad_p.squeeze(0)   # (L, 2H)
                prot_cam_raw  = F.relu((grad_p * act_p.detach()).mean(dim=-1))
                prot_cam      = _normalise(prot_cam_raw)
                prot_grad_norm = _normalise(grad_p.norm(dim=-1))

        # Prediction
        if task == 'dti':
            prob = torch.softmax(logits.detach(), dim=-1)[0, 1].item()
            pred = logits.detach()[0, 1].item()
        else:
            prob = logits.detach()[0, 0].item()
            pred = logits.detach()[0, 0].item()

        return {
            'drug_cam':           drug_cam.detach(),
            'drug_cam_raw':       drug_cam_raw.detach(),
            'protein_cam':        prot_cam.detach()       if prot_cam is not None else None,
            'protein_cam_raw':    prot_cam_raw.detach()   if prot_cam_raw is not None else None,
            'protein_grad_norm':  prot_grad_norm.detach() if prot_grad_norm is not None else None,
            'logits':             logits.detach(),
            'prediction':         pred,
            'prediction_prob':    prob,
        }

    finally:
        store.remove_all()
        model.zero_grad()


# ── Ensemble attribution ──────────────────────────────────────────────────────

def ensemble_attribution(phase1_scores, phase2_scores, alpha=0.5):
    """
    Combine Phase 1 (input-gradient saliency) and Phase 2 (Grad-CAM) scores.

    Both inputs must be numpy arrays or tensors, normalised to [0,1].
    Returns a numpy array normalised to [0,1].

    alpha : weight on phase1; (1-alpha) on phase2. Default 0.5.
    """
    import numpy as np
    p1 = _to_numpy(phase1_scores)
    p2 = _to_numpy(phase2_scores)
    assert len(p1) == len(p2), f"Length mismatch: {len(p1)} vs {len(p2)}"
    combined = alpha * p1 + (1 - alpha) * p2
    lo, hi = combined.min(), combined.max()
    if hi > lo:
        combined = (combined - lo) / (hi - lo)
    return combined


# ── Comparison table ──────────────────────────────────────────────────────────

def compare_drug_attributions(
    phase1_atom_imp,
    drug_cam,
    mol=None,
    top_k=10,
):
    """
    Print a ranked comparison table of atom importances.

    Args:
        phase1_atom_imp : (N,) input-gradient scores (Phase 1)
        drug_cam        : (N,) Grad-CAM scores (Phase 2)
        mol             : rdkit Mol object (optional — adds element labels)
        top_k           : number of atoms to show in ranking
    """
    import numpy as np

    p1 = _to_numpy(phase1_atom_imp)
    p2 = _to_numpy(drug_cam)
    ens = ensemble_attribution(p1, p2)

    n = len(p1)
    labels = [f"A{i}" for i in range(n)]
    if mol is not None:
        try:
            labels = [f"{a.GetSymbol()}{i}" for i, a in enumerate(mol.GetAtoms())]
        except Exception:
            pass

    # Rank by ensemble
    order = np.argsort(ens)[::-1][:top_k]

    print(f"\n{'Rank':<5} {'Atom':<8} {'InputGrad':<12} {'GradCAM':<12} {'Ensemble':<12}")
    print("-" * 50)
    for rank, idx in enumerate(order, 1):
        print(f"{rank:<5} {labels[idx]:<8} {p1[idx]:<12.4f} {p2[idx]:<12.4f} {ens[idx]:<12.4f}")
    print()

    return {
        'phase1':   p1,
        'grad_cam': p2,
        'ensemble': ens,
        'top_k_indices': order.tolist(),
    }


def compare_protein_attributions(
    attn_weights,
    protein_cam,
    protein_grad_norm=None,
    sequence=None,
    top_k=15,
):
    """
    Print a ranked comparison of residue attribution methods.

    Args:
        attn_weights     : (L,) AttentionPooling weights (Phase 1, or None)
        protein_cam      : (L,) BiGRU Grad-CAM scores (Phase 2)
        protein_grad_norm: (L,) pure gradient norm per residue (Phase 2 alternative)
        sequence         : amino-acid sequence string (optional — adds residue labels)
        top_k            : residues to show
    """
    import numpy as np

    p2 = _to_numpy(protein_cam)
    L  = len(p2)

    aa_labels = list(sequence)[:L] if sequence else [f"R{i}" for i in range(L)]

    if attn_weights is not None:
        p1 = _to_numpy(attn_weights)[:L]
        ens = ensemble_attribution(p1, p2)
        has_attn = True
    else:
        p1  = None
        ens = p2
        has_attn = False

    order = np.argsort(ens)[::-1][:top_k]

    header = f"{'Rank':<5} {'Res':<8} {'Pos':<6}"
    if has_attn:
        header += f" {'AttnPool':<12}"
    header += f" {'GradCAM':<12}"
    if protein_grad_norm is not None:
        header += f" {'GradNorm':<12}"
    if has_attn:
        header += f" {'Ensemble':<12}"

    print(f"\n{header}")
    print("-" * len(header))

    for rank, idx in enumerate(order, 1):
        row = f"{rank:<5} {aa_labels[idx]:<8} {idx:<6}"
        if has_attn:
            row += f" {p1[idx]:<12.4f}"
        row += f" {p2[idx]:<12.4f}"
        if protein_grad_norm is not None:
            pn = _to_numpy(protein_grad_norm)
            row += f" {pn[idx]:<12.4f}"
        if has_attn:
            row += f" {ens[idx]:<12.4f}"
        print(row)
    print()

    return {
        'attn_pool':  p1,
        'grad_cam':   p2,
        'ensemble':   ens,
        'top_k_indices': order.tolist(),
    }


# ── Sanity checks for Grad-CAM ────────────────────────────────────────────────

def sanity_check_gradcam(drug_cam, protein_cam=None, phase1_atom_imp=None):
    """
    Run Phase 2 sanity checks and print a report.
    """
    import numpy as np
    from scipy import stats as sp_stats

    print("\n-- Phase 2 Sanity Checks -------------------------------------------")

    # 1. Drug Grad-CAM non-uniformity
    dc = _to_numpy(drug_cam)
    nonzero = (dc > 0.01).mean()
    flag = "PASS" if nonzero > 0.1 else "WARN"
    print(f"  [Drug GradCAM] fraction of atoms with cam > 0.01: {nonzero:.2f}  [{flag}]")

    # 2. Agreement with Phase 1 (if provided)
    if phase1_atom_imp is not None:
        p1 = _to_numpy(phase1_atom_imp)
        if len(p1) == len(dc):
            rho, pval = sp_stats.spearmanr(p1, dc)
            flag = "PASS" if rho > 0.3 else "WARN"
            print(f"  [Phase1 vs GradCAM] Spearman rho={rho:.3f}, p={pval:.3f}  [{flag}]")

    # 3. Protein Grad-CAM non-uniformity (if available)
    if protein_cam is not None:
        pc = _to_numpy(protein_cam)
        nonzero_p = (pc > 0.01).mean()
        flag = "PASS" if nonzero_p > 0.1 else "WARN"
        print(f"  [Prot GradCAM] fraction of residues with cam > 0.01: {nonzero_p:.2f}  [{flag}]")

    print("--------------------------------------------------------------------")


# ── Utilities ─────────────────────────────────────────────────────────────────

def _normalise(t):
    """Min-max normalise tensor to [0, 1]."""
    lo, hi = t.min(), t.max()
    if hi > lo:
        return (t - lo) / (hi - lo)
    return t.clone()


def _to_numpy(x):
    import numpy as np
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x, dtype=np.float32)
