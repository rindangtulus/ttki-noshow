"""Uji otomatis: split kronologis, anti-leakage, kalibrator, metrik, dan smoke test end-to-end.

Jalankan: pytest -q
"""
import numpy as np
import pandas as pd
import pytest

from src import config as C
from src.data import clean
from src.features import FORBIDDEN, add_features, feature_lists
from src.metrics import capacity_threshold, expected_calibration_error, topk_metrics
from src.models import IsotonicCalibrator, PlattCalibrator
from src.run_experiments import parse_args, run
from src.splits import ORDER, chronological_date_split
from tests.synthetic_fixture import make_fake_kaggle


@pytest.fixture(scope="module")
def prepared():
    df, _ = clean(make_fake_kaggle())
    df = add_features(df)
    df["split"] = chronological_date_split(df, C.SPLIT_FRACTIONS)
    return df


def test_split_is_chronological_and_disjoint(prepared):
    ranges = [(prepared[prepared.split == s].appt_date.min(), prepared[prepared.split == s].appt_date.max()) for s in ORDER]
    for (_, prev_max), (nxt_min, _) in zip(ranges, ranges[1:]):
        assert prev_max < nxt_min  # tidak ada tanggal yang terbagi/tumpang tindih
    assert prepared.split.notna().all() and set(prepared.split) == set(ORDER)


def test_no_forbidden_features():
    for fs in ("full", "no_proxy"):
        used = set(sum(feature_lists(fs), []))
        assert not (used & FORBIDDEN)
    assert "neighbourhood" not in sum(feature_lists("no_proxy"), [])


def test_cleaning_rules():
    raw = make_fake_kaggle(500)
    raw.loc[0, "Age"] = -1
    raw.loc[1, "ScheduledDay"] = "2016-12-31T10:00:00Z"  # setelah AppointmentDay -> waiting negatif
    df, log = clean(raw)
    assert log["dropped_invalid_age"] >= 1 and log["dropped_negative_waiting"] >= 1
    assert (df.waiting_days >= 0).all() and df.age.between(0, 110).all()


def test_calibrators_monotone_and_in_range():
    rng = np.random.default_rng(0)
    p = rng.random(2000) * 0.6
    y = (rng.random(2000) < p * 0.5).astype(int)
    for cal in (PlattCalibrator(), IsotonicCalibrator()):
        q = cal.fit(p, y).predict(np.sort(p))
        assert np.all(np.diff(q) >= -1e-12) and q.min() >= 0 and q.max() <= 1


def test_topk_and_ece_basics():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    s = np.array([0.9, 0.8, 0.7, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    m = topk_metrics(y, s, np.arange(10) / 10, 0.2)
    assert m["precision@20"] == 1.0 and m["recall@20"] == 1.0 and m["lift@20"] == pytest.approx(5.0)
    assert expected_calibration_error(y, np.full(10, 0.2), 5) == pytest.approx(0.0, abs=1e-9)
    assert capacity_threshold(np.arange(100) / 100, 0.10) == pytest.approx(0.8999, abs=2e-2)


def test_end_to_end_smoke(tmp_path):
    csv = tmp_path / "fake.csv"
    make_fake_kaggle(3000).to_csv(csv, index=False)
    out = run(parse_args(["--data", str(csv), "--out", str(tmp_path / "res"), "--n-boot", "5", "--rf-seeds", "1"]))
    for f in ["data_audit.json", "split_summary.csv", "metrics_primary.csv", "paired_deltas.csv", "test_predictions.csv",
              "run_config.json", "thresholds.csv"]:
        assert (out / f).exists(), f
    m = pd.read_csv(out / "metrics_primary.csv")
    assert {"LR", "RF"} == set(m.model) and {"raw", "platt", "isotonic"} == set(m.variant)
    d = pd.read_csv(out / "paired_deltas.csv")
    assert d["comparison"].str.contains("F1-tuned threshold - 0.5").any()  # skenario A vs baseline tersedia
    assert d[["delta", "ci_lo", "ci_hi"]].notna().all().all()
    # Platt bersifat monoton ketat -> precision@10% identik dengan raw (selain ties)
    g = m[m.metric == "precision@10"].pivot(index="model", columns="variant", values="value")
    assert np.allclose(g["raw"], g["platt"], atol=2e-3)
