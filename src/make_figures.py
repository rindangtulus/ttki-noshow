"""Membuat gambar paper dari berkas hasil (tanpa menghitung ulang model).

    python -m src.make_figures --results results/full --out figures
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C
from .metrics import quantile_bin_stats

COLORS = {"raw": "#4c78a8", "platt": "#f58518", "isotonic": "#54a24b"}


def _quantile_bins(y, p, bins=10):
    mp, fo, _ = quantile_bin_stats(y, p, bins)
    return mp, fo


def reliability(pred: pd.DataFrame, out: Path):
    y = pred["y"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharex=True, sharey=True)
    hi = 0.0
    for ax, model in zip(axes, ["LR", "RF"]):
        for v, c in COLORS.items():
            col = f"{model}_{v}"
            if col in pred:
                mp, fo = _quantile_bins(y, pred[col].to_numpy())
                hi = max(hi, mp.max(), fo.max())
                ax.plot(mp, fo, "o-", color=c, label=v, ms=4)
        ax.set_title(model)
        ax.set_xlabel("Mean predicted probability")
    hi = min(1.0, hi * 1.1 + 0.01)
    for ax in axes:
        ax.plot([0, hi], [0, hi], "k--", lw=1, label="ideal")
        ax.set_xlim(0, hi); ax.set_ylim(0, hi)
    axes[0].set_ylabel("Observed no-show fraction")
    axes[0].legend()
    fig.tight_layout(); fig.savefig(out / "fig_reliability.png", dpi=200); plt.close(fig)


def precision_at_k(pred: pd.DataFrame, out: Path):
    y = pred["y"].to_numpy()
    rng = np.random.default_rng(C.SEED)
    tb = rng.random(len(y))
    ks = np.linspace(0.01, 0.30, 30)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    for model, ls in [("LR", "-"), ("RF", "--")]:
        for v, c in COLORS.items():
            col = f"{model}_{v}"
            if col not in pred:
                continue
            order = np.lexsort((tb, -pred[col].to_numpy()))
            cum = np.cumsum(y[order])
            vals = [cum[max(1, int(np.ceil(k * len(y)))) - 1] / max(1, int(np.ceil(k * len(y)))) for k in ks]
            ax.plot(ks * 100, vals, ls, color=c, label=f"{model} {v}")
    ax.axhline(y.mean(), color="gray", lw=1, ls=":", label="prevalence")
    ax.axvline(C.CAPACITY * 100, color="k", lw=0.8, ls=":")
    ax.set_xlabel("Outreach capacity (% of appointments)"); ax.set_ylabel("Precision@k")
    ax.legend(fontsize=7, ncol=2); fig.tight_layout(); fig.savefig(out / "fig_precision_at_k.png", dpi=200); plt.close(fig)


def capacity_deviation(metrics: pd.DataFrame, out: Path):
    sub = metrics[metrics.metric == "thrCap:outreach_rate"]
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    labels = [f"{m}\n{v}" for m, v in zip(sub.model, sub.variant)]
    ax.bar(labels, sub["value"] * 100, color=[COLORS[v] for v in sub.variant])
    ax.axhline(C.CAPACITY * 100, color="k", ls="--", lw=1, label="target capacity")
    ax.set_ylabel("Realised outreach rate on test (%)"); ax.legend()
    fig.tight_layout(); fig.savefig(out / "fig_capacity_deviation.png", dpi=200); plt.close(fig)


def daily_rate(daily: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    palette = {"train": "#9ecae1", "calibration": "#fdd0a2", "validation": "#c7e9c0", "test": "#dadaeb"}
    for s, g in daily.groupby("split"):
        ax.bar(pd.to_datetime(g["appt_date"]), g["no_show_rate"] * 100, width=0.9, color=palette[s], label=s)
    ax.set_ylabel("No-show rate per day (%)"); ax.legend(fontsize=7, ncol=4)
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "fig_daily_no_show_rate.png", dpi=200); plt.close(fig)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True)
    p.add_argument("--out", default="figures")
    a = p.parse_args(argv)
    res, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(res / "test_predictions.csv")
    metrics = pd.read_csv(res / "metrics_primary.csv")
    reliability(pred, out); precision_at_k(pred, out); capacity_deviation(metrics, out)
    daily_rate(pd.read_csv(res / "daily_summary.csv"), out)
    print("Gambar tersimpan di", out)


if __name__ == "__main__":
    main()
