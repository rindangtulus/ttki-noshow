"""Pipeline utama: audit -> bersih -> fitur -> split kronologis -> model -> kalibrasi -> evaluasi.

Contoh:
    python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv
    python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv --feature-set no_proxy

Semua angka di paper HARUS berasal dari berkas yang dihasilkan skrip ini (folder results/).
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from . import config as C
from .data import audit_raw, clean, load_raw, save_json
from .features import add_features, feature_lists
from .metrics import best_f1_threshold, capacity_threshold, evaluate_scores
from .models import build_model, make_calibrator
from .splits import ORDER, chronological_date_split, split_summary

VARIANTS = ["raw", "platt", "isotonic"]
DELTA_METRICS = ["pr_auc", "brier", "ece", f"precision@{int(C.CAPACITY*100)}", f"recall@{int(C.CAPACITY*100)}",
                 f"lift@{int(C.CAPACITY*100)}", "thrCap:outreach_rate", "thrF1:f1"]


def cluster_bootstrap_indices(groups: np.ndarray, n_boot: int, rng: np.random.Generator) -> list[np.ndarray]:
    """Bootstrap per kluster (PatientId): pasien yang sama selalu ikut/keluar bersama."""
    codes, uniq = pd.factorize(groups)
    out = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        counts = np.bincount(pick, minlength=len(uniq))
        out.append(np.repeat(np.arange(len(codes)), counts[codes]))
    return out


def variant_scores(pipe, calibrators: dict, frame: pd.DataFrame, cols: list[str]) -> dict[str, np.ndarray]:
    raw = pipe.predict_proba(frame[cols])[:, 1]
    out = {"raw": raw}
    for name, cal in calibrators.items():
        out[name] = cal.predict(raw)
    return out


def run(args) -> Path:
    out_dir = Path(args.out) / args.feature_set
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = load_raw(args.data)
    save_json(audit_raw(raw), out_dir / "data_audit.json")
    df, clean_log = clean(raw)
    save_json(clean_log, out_dir / "cleaning_log.json")
    df = add_features(df)

    label = chronological_date_split(df, C.SPLIT_FRACTIONS)
    df["split"] = label
    summary = split_summary(df, label)
    summary.to_csv(out_dir / "split_summary.csv", index=False)
    (df.groupby(["appt_date", "split"]).agg(n=("y", "size"), no_show_rate=("y", "mean")).reset_index()
       .to_csv(out_dir / "daily_summary.csv", index=False))

    num, binary, cat = feature_lists(args.feature_set)
    cols = num + binary + cat
    parts = {s: df[df["split"] == s].reset_index(drop=True) for s in ORDER}
    test = parts["test"]
    y_test = test["y"].to_numpy()
    rng = np.random.default_rng(C.SEED)
    tiebreak = rng.random(len(test))
    boot_idx = cluster_bootstrap_indices(test["patient_id"].to_numpy(), args.n_boot, rng) if args.n_boot > 0 else []

    models = [("LR", [C.SEED]), ("RF", C.RF_SEEDS[: args.rf_seeds])]
    point_rows, long_rows, delta_store, thr_rows = [], [], {}, []
    pred_cols = {"appt_date": test["appt_date"], "y": y_test}

    for model_name, seeds in models:
        for si, seed in enumerate(seeds):
            pipe = build_model(model_name, num, binary, cat, seed).fit(parts["train"][cols], parts["train"]["y"])
            raw_cal = pipe.predict_proba(parts["calibration"][cols])[:, 1]
            cals = {k: make_calibrator(k).fit(raw_cal, parts["calibration"]["y"].to_numpy()) for k in ("platt", "isotonic")}
            sc = {s: variant_scores(pipe, cals, parts[s], cols) for s in ("validation", "test")}

            boot_vals = {}
            for v in VARIANTS:
                s_val, s_test = sc["validation"][v], sc["test"][v]
                y_val = parts["validation"]["y"].to_numpy()
                thresholds = {
                    "thr0.5": C.THRESHOLD_DEFAULT,
                    "thrF1": best_f1_threshold(y_val, s_val),
                    "thrCap": capacity_threshold(s_val, C.CAPACITY),
                }
                for rule, t in thresholds.items():
                    thr_rows.append({"model": model_name, "seed": seed, "variant": v, "rule": rule, "threshold": t})
                point = evaluate_scores(y_test, s_test, tiebreak, thresholds, C.CAPACITY, C.ECE_BINS, with_slope=True)
                for m, val in point.items():
                    point_rows.append({"model": model_name, "seed": seed, "variant": v, "metric": m, "value": val})

                if si == 0:  # seed utama: CI bootstrap + prediksi test
                    pred_cols[f"{model_name}_{v}"] = s_test
                    if boot_idx:
                        arr = {}
                        for idx in boot_idx:
                            r = evaluate_scores(y_test[idx], s_test[idx], tiebreak[idx], thresholds, C.CAPACITY,
                                                C.ECE_BINS, with_slope=False)
                            for m, val in r.items():
                                arr.setdefault(m, []).append(val)
                        boot_vals[v] = {m: np.asarray(a) for m, a in arr.items()}
                    for m, val in point.items():
                        lo, hi = (np.nan, np.nan)
                        if boot_idx and m in boot_vals[v]:
                            lo, hi = np.nanpercentile(boot_vals[v][m], [2.5, 97.5])
                        long_rows.append({"model": model_name, "seed": seed, "variant": v, "metric": m,
                                          "value": val, "ci_lo": lo, "ci_hi": hi})
            if si == 0:
                delta_store[model_name] = boot_vals

    point_df = pd.DataFrame(point_rows)
    point_df.to_csv(out_dir / "metrics_all_seeds.csv", index=False)
    pd.DataFrame(long_rows).to_csv(out_dir / "metrics_primary.csv", index=False)
    pd.DataFrame(thr_rows).to_csv(out_dir / "thresholds.csv", index=False)
    (point_df.groupby(["model", "variant", "metric"])["value"].agg(["mean", "std", "count"]).reset_index()
        .to_csv(out_dir / "metrics_seed_summary.csv", index=False))
    pd.DataFrame(pred_cols).to_csv(out_dir / "test_predictions.csv", index=False)

    # Selisih berpasangan (paired bootstrap): kalibrasi vs raw, dan RF vs LR
    delta_rows = []
    if boot_idx:
        pairs = []
        for mdl in delta_store:
            pairs += [((mdl, "platt"), (mdl, "raw"), f"{mdl}: platt - raw"),
                      ((mdl, "isotonic"), (mdl, "raw"), f"{mdl}: isotonic - raw")]
        if "LR" in delta_store and "RF" in delta_store:
            pairs += [(("RF", v), ("LR", v), f"RF - LR ({v})") for v in VARIANTS]
        for (m1, v1), (m2, v2), name in pairs:
            for m in DELTA_METRICS:
                a, b = delta_store[m1][v1][m], delta_store[m2][v2][m]
                d = a - b
                p1 = point_df[(point_df.model == m1) & (point_df.variant == v1) & (point_df.metric == m)]
                p2 = point_df[(point_df.model == m2) & (point_df.variant == v2) & (point_df.metric == m)]
                est = float(p1.iloc[0]["value"] - p2.iloc[0]["value"])
                lo, hi = np.nanpercentile(d, [2.5, 97.5])
                delta_rows.append({"comparison": name, "metric": m, "delta": est, "ci_lo": lo, "ci_hi": hi})
        # Skenario A vs baseline: threshold F1-tuned dikurangi threshold 0,5 (varian skor sama)
        for mdl in delta_store:
            for v in VARIANTS:
                for m in ["f1", "precision", "recall", "outreach_rate"]:
                    d = delta_store[mdl][v][f"thrF1:{m}"] - delta_store[mdl][v][f"thr0.5:{m}"]
                    p = point_df[(point_df.model == mdl) & (point_df.variant == v)]
                    est = float(p[p.metric == f"thrF1:{m}"].iloc[0]["value"] - p[p.metric == f"thr0.5:{m}"].iloc[0]["value"])
                    lo, hi = np.nanpercentile(d, [2.5, 97.5])
                    delta_rows.append({"comparison": f"{mdl} ({v}): F1-tuned threshold - 0.5", "metric": m,
                                       "delta": est, "ci_lo": lo, "ci_hi": hi})
    pd.DataFrame(delta_rows).to_csv(out_dir / "paired_deltas.csv", index=False)

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    save_json(
        {
            "python": sys.version, "platform": platform.platform(), "sklearn": sklearn.__version__,
            "pandas": pd.__version__, "numpy": np.__version__, "git_commit": commit,
            "data_file": str(args.data), "feature_set": args.feature_set, "features": cols,
            "split_fractions": C.SPLIT_FRACTIONS, "capacity": C.CAPACITY, "n_bootstrap": args.n_boot,
            "seed": C.SEED, "rf_seeds": C.RF_SEEDS[: args.rf_seeds],
            "lr_params": C.LR_PARAMS, "rf_params": C.RF_PARAMS,
        },
        out_dir / "run_config.json",
    )
    print(f"Selesai. Hasil di {out_dir}")
    return out_dir


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", required=True, help="Path CSV Kaggle asli (KaggleV2-May-2016.csv)")
    p.add_argument("--out", default="results")
    p.add_argument("--feature-set", choices=["full", "no_proxy"], default="full")
    p.add_argument("--n-boot", type=int, default=C.N_BOOTSTRAP)
    p.add_argument("--rf-seeds", type=int, default=len(C.RF_SEEDS), help="jumlah seed RF yang dijalankan")
    return p.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())
