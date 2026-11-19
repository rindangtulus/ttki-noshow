"""Memuat, mengaudit, dan membersihkan CSV Kaggle 'Medical Appointment No Shows'."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import AGE_MAX, AGE_MIN, RAW_RENAME


def load_raw(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(RAW_RENAME) - set(df.columns)
    if missing:
        raise ValueError(
            f"Kolom wajib tidak ada: {sorted(missing)}. Pastikan memakai CSV Kaggle asli "
            "(joniarroba/noshowappointments), bukan data sintetis."
        )
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["scheduled_ts"] = pd.to_datetime(out["scheduled_day"], utc=True, errors="coerce").dt.tz_localize(None)
    out["appt_ts"] = pd.to_datetime(out["appointment_day"], utc=True, errors="coerce").dt.tz_localize(None)
    out["scheduled_date"] = out["scheduled_ts"].dt.normalize()
    out["appt_date"] = out["appt_ts"].dt.normalize()
    out["waiting_days"] = (out["appt_date"] - out["scheduled_date"]).dt.days
    return out


def audit_raw(raw: pd.DataFrame) -> dict:
    """Audit dataset SEBELUM pembersihan (dicatat di paper, bagian Dataset)."""
    df = _parse_dates(raw.rename(columns=RAW_RENAME))
    target = df["no_show"].astype(str).str.strip().str.lower()
    return {
        "n_rows": int(len(df)),
        "n_columns": int(raw.shape[1]),
        "missing_cells": int(raw.isna().sum().sum()),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_appointment_id": int(df["appointment_id"].duplicated().sum()),
        "n_unique_patients": int(df["patient_id"].nunique()),
        "no_show_yes_rate": float((target == "yes").mean()),
        "target_values": target.value_counts().to_dict(),
        "age_min": int(df["age"].min()),
        "age_max": int(df["age"].max()),
        "n_age_negative": int((df["age"] < 0).sum()),
        "n_age_above_max": int((df["age"] > AGE_MAX).sum()),
        "handicap_value_counts": {str(k): int(v) for k, v in df["handicap"].value_counts().sort_index().items()},
        "n_negative_waiting_days": int((df["waiting_days"] < 0).sum()),
        "waiting_days_min": int(df["waiting_days"].min()),
        "waiting_days_max": int(df["waiting_days"].max()),
        "n_unparseable_dates": int(df["scheduled_ts"].isna().sum() + df["appt_ts"].isna().sum()),
        "appointment_date_min": str(df["appt_date"].min().date()),
        "appointment_date_max": str(df["appt_date"].max().date()),
        "n_appointment_dates": int(df["appt_date"].nunique()),
        "n_neighbourhoods": int(df["neighbourhood"].nunique()),
        "patients_with_multiple_appointments": int((df.groupby("patient_id").size() > 1).sum()),
    }


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bersihkan data dengan aturan tetap; kembalikan data + log jumlah baris yang dibuang."""
    df = _parse_dates(raw.rename(columns=RAW_RENAME))
    log = {"rows_in": int(len(df))}

    df["y"] = df["no_show"].astype(str).str.strip().str.lower().map({"yes": 1, "no": 0})
    bad_target = int(df["y"].isna().sum())
    df = df.dropna(subset=["y", "scheduled_ts", "appt_ts"])
    log["dropped_bad_target_or_date"] = bad_target

    bad_age = ~df["age"].between(AGE_MIN, AGE_MAX)
    log["dropped_invalid_age"] = int(bad_age.sum())
    df = df[~bad_age]

    bad_wait = df["waiting_days"] < 0
    log["dropped_negative_waiting"] = int(bad_wait.sum())
    df = df[~bad_wait]

    dup = df["appointment_id"].duplicated()
    log["dropped_duplicate_appointment_id"] = int(dup.sum())
    df = df[~dup]

    df["y"] = df["y"].astype(int)
    df = df.sort_values(["appt_date", "scheduled_ts", "appointment_id"]).reset_index(drop=True)
    log["rows_out"] = int(len(df))
    log["no_show_rate_after_cleaning"] = float(df["y"].mean())
    return df, log


def save_json(obj: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
