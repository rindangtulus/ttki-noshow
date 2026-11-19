"""Metrik evaluasi: diskriminasi, kalibrasi, dan metrik berbasis kapasitas outreach."""
from __future__ import annotations

import math

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def rank_order(score: np.ndarray, tiebreak: np.ndarray) -> np.ndarray:
    """Urutan menurun menurut skor; ties diputus dengan bilangan acak tetap (reproducible)."""
    return np.lexsort((tiebreak, -score))


def topk_metrics(y: np.ndarray, score: np.ndarray, tiebreak: np.ndarray, frac: float) -> dict:
    n = len(y)
    k = max(1, math.ceil(frac * n))
    idx = rank_order(score, tiebreak)[:k]
    tp = float(y[idx].sum())
    pos = float(y.sum())
    prevalence = pos / n
    precision = tp / k
    return {
        f"precision@{int(frac*100)}": precision,
        f"recall@{int(frac*100)}": tp / pos if pos else float("nan"),
        f"lift@{int(frac*100)}": precision / prevalence if prevalence else float("nan"),
    }


def threshold_metrics(y: np.ndarray, score: np.ndarray, thr: float) -> dict:
    pred = score >= thr
    tp = float(((pred == 1) & (y == 1)).sum())
    fp = float(((pred == 1) & (y == 0)).sum())
    fn = float(((pred == 0) & (y == 1)).sum())
    tn = float(((pred == 0) & (y == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "outreach_rate": float(pred.mean()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def best_f1_threshold(y: np.ndarray, score: np.ndarray, n_grid: int = 400) -> float:
    """Threshold yang memaksimalkan F1 pada validation (grid kuantil skor)."""
    grid = np.unique(np.quantile(score, np.linspace(0.01, 0.99, n_grid)))
    best_t, best_f = grid[0], -1.0
    for t in grid:
        f = threshold_metrics(y, score, t)["f1"]
        if f > best_f:
            best_t, best_f = float(t), f
    return best_t


def capacity_threshold(score_valid: np.ndarray, frac: float) -> float:
    """Threshold dari validation sehingga ~frac janji temu ditandai (dipakai apa adanya pada test)."""
    return float(np.quantile(score_valid, 1 - frac))


def quantile_bin_stats(y: np.ndarray, p: np.ndarray, bins: int = 10):
    """Statistik per bin kuantil. Skor yang sama (ties, mis. isotonik) selalu masuk bin yang sama.

    Mengembalikan (rata-rata prediksi, rata-rata observasi, jumlah) per bin tak kosong.
    """
    edges = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return np.array([p.mean()]), np.array([y.mean()]), np.array([len(y)])
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    mp, fo, cnt = [], [], []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.any():
            mp.append(p[m].mean()); fo.append(y[m].mean()); cnt.append(int(m.sum()))
    return np.array(mp), np.array(fo), np.array(cnt)


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """ECE dengan bin kuantil (frekuensi ~sama), ties tidak dipecah; bin kosong diabaikan."""
    mp, fo, cnt = quantile_bin_stats(y, p, bins)
    return float((cnt / cnt.sum() * np.abs(fo - mp)).sum())


def calibration_slope_intercept(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """Slope & intercept kalibrasi (regresi logistik y ~ logit(p)); ideal: slope=1, intercept=0."""
    z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6))).reshape(-1, 1)
    lr = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(z, y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def evaluate_scores(
    y: np.ndarray,
    score: np.ndarray,
    tiebreak: np.ndarray,
    thresholds: dict[str, float],
    capacity: float,
    ece_bins: int = 10,
    with_slope: bool = True,
) -> dict:
    """Seluruh metrik untuk satu (model, varian). `thresholds` dibekukan dari validation."""
    out = {
        "pr_auc": average_precision_score(y, score),
        "roc_auc": roc_auc_score(y, score),
        "brier": brier_score_loss(y, score),
        "log_loss": log_loss(y, np.clip(score, 1e-6, 1 - 1e-6)),
        "ece": expected_calibration_error(y, score, ece_bins),
        "mean_pred": float(score.mean()),
        "prevalence": float(y.mean()),
    }
    if with_slope:
        s, i = calibration_slope_intercept(y, score)
        out["cal_slope"], out["cal_intercept"] = s, i
    out.update(topk_metrics(y, score, tiebreak, capacity))
    for rule, thr in thresholds.items():
        for k, v in threshold_metrics(y, score, thr).items():
            out[f"{rule}:{k}"] = v
    return out
