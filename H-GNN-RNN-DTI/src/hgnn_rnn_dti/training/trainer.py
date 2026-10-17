"""Training loop (roadmap step 7).

AdamW + focal loss (config-driven), gradient clipping, early stopping on the
validation primary metric (AUPR for classification, RMSE for regression), and
best-checkpoint restore. `max_batches` caps batches/epoch for fast smoke runs.
"""
from __future__ import annotations

import copy

import numpy as np
import torch

from ..evaluation.metrics import compute_metrics
from .losses import build_loss


class Trainer:
    def __init__(self, model, cfg: dict, device: str = "cpu"):
        self.cfg = cfg
        self.device = device
        self.model = model.to(device)
        self.task = cfg.get("task", "classification")
        t = cfg["train"]
        self.loss_fn = build_loss(cfg)
        self.opt = torch.optim.AdamW(
            model.parameters(), lr=t["lr"], weight_decay=t.get("weight_decay", 0.0)
        )
        self.max_epochs = t["epochs"]
        self.patience = t.get("early_stopping_patience", 15)
        self.grad_clip = t.get("grad_clip")
        # model selection: maximize AUPR (classification) / minimize RMSE (regression)
        self.primary = "aupr" if self.task == "classification" else "rmse"
        self.maximize = self.task == "classification"

    def _move(self, batch):
        drug_batch, prot_pad, lengths, labels = batch
        return drug_batch.to(self.device), prot_pad.to(self.device), lengths, labels.to(self.device)

    def _epoch(self, loader, train: bool, max_batches=None):
        self.model.train(train)
        losses, preds, ys = [], [], []
        ctx = torch.enable_grad() if train else torch.no_grad()
        with ctx:
            for i, batch in enumerate(loader):
                if max_batches is not None and i >= max_batches:
                    break
                drug_batch, prot_pad, lengths, labels = self._move(batch)
                out = self.model(drug_batch, prot_pad, lengths)
                loss = self.loss_fn(out, labels)
                if train:
                    self.opt.zero_grad()
                    loss.backward()
                    if self.grad_clip:
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                    self.opt.step()
                losses.append(float(loss.item()))
                score = torch.sigmoid(out) if self.task == "classification" else out
                preds.append(score.detach().cpu().numpy())
                ys.append(labels.detach().cpu().numpy())
        return float(np.mean(losses)), np.concatenate(preds), np.concatenate(ys)

    def _improved(self, cur, best) -> bool:
        if isinstance(cur, float) and np.isnan(cur):
            return False
        if best is None:
            return True
        return cur > best if self.maximize else cur < best

    def fit(self, train_loader, val_loader, max_batches=None, verbose=True) -> dict:
        best, best_state, no_improve, history = None, None, 0, []
        for epoch in range(1, self.max_epochs + 1):
            tr_loss, _, _ = self._epoch(train_loader, True, max_batches)
            va_loss, vp, vy = self._epoch(val_loader, False, max_batches)
            vm = compute_metrics(vy, vp, self.task)
            vm.update(train_loss=tr_loss, val_loss=va_loss, epoch=epoch)
            history.append(vm)
            cur = vm[self.primary]
            if self._improved(cur, best):
                best, best_state, no_improve = cur, copy.deepcopy(self.model.state_dict()), 0
            else:
                no_improve += 1
            if verbose:
                cur_str = f"{cur:.4f}" if cur is not None and not (isinstance(cur, float) and np.isnan(cur)) else "nan"
                best_str = f"{best:.4f}" if best is not None else "n/a"
                print(f"epoch {epoch:3d} | train {tr_loss:.4f} | val {va_loss:.4f} "
                      f"| {self.primary} {cur_str} | best {best_str}")
            if no_improve >= self.patience:
                if verbose:
                    print(f"early stopping at epoch {epoch} (no {self.primary} improvement in {self.patience})")
                break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        return {"history": history, f"best_val_{self.primary}": best}

    def evaluate(self, loader, max_batches=None) -> dict:
        loss, preds, ys = self._epoch(loader, False, max_batches)
        metrics = compute_metrics(ys, preds, self.task)
        metrics["loss"] = loss
        return metrics
