"""Rekayasa fitur yang HANYA memakai informasi yang diketahui saat janji temu dijadwalkan.

Dilarang sebagai fitur: patient_id, appointment_id (identitas / proxy waktu pencatatan).
"""
from __future__ import annotations

import pandas as pd

NUMERIC = ["age", "waiting_days", "scheduled_hour"]
BINARY = ["scholarship", "hypertension", "diabetes", "alcoholism", "sms_received"]
CATEGORICAL = ["gender", "neighbourhood", "appt_weekday", "handicap_level"]

FORBIDDEN = {"patient_id", "appointment_id", "y", "no_show"}

# Atribut yang berpotensi menjadi proxy sosial-ekonomi/geografis (untuk analisis ablation etika)
SENSITIVE_PROXY = ["gender", "neighbourhood", "scholarship"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["scheduled_hour"] = out["scheduled_ts"].dt.hour
    out["appt_weekday"] = out["appt_date"].dt.day_name().str[:3]
    out["handicap_level"] = out["handicap"].clip(upper=2).astype(int).astype(str)  # 0 / 1 / 2+
    for c in BINARY:
        out[c] = out[c].astype(int)
    return out


def feature_lists(feature_set: str = "full") -> tuple[list[str], list[str], list[str]]:
    """feature_set: 'full' atau 'no_proxy' (tanpa gender, neighbourhood, scholarship)."""
    num, binary, cat = list(NUMERIC), list(BINARY), list(CATEGORICAL)
    if feature_set == "no_proxy":
        binary = [c for c in binary if c not in SENSITIVE_PROXY]
        cat = [c for c in cat if c not in SENSITIVE_PROXY]
    elif feature_set != "full":
        raise ValueError(feature_set)
    used = set(num) | set(binary) | set(cat)
    assert not (used & FORBIDDEN), f"Fitur terlarang terdeteksi: {used & FORBIDDEN}"
    return num, binary, cat
