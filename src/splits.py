"""Pembagian data kronologis berdasarkan tanggal (satu tanggal tidak pernah terpecah antar blok)."""
from __future__ import annotations

import pandas as pd

ORDER = ["train", "calibration", "validation", "test"]


def chronological_date_split(df: pd.DataFrame, fractions: dict[str, float], date_col: str = "appt_date") -> pd.Series:
    """Tetapkan label blok untuk tiap baris. Batas blok jatuh pada tanggal utuh.

    Blok k berakhir pada tanggal pertama yang membuat proporsi kumulatif >= target kumulatif k.
    """
    if abs(sum(fractions.values()) - 1) > 1e-9:
        raise ValueError("Proporsi split harus berjumlah 1")
    counts = df.groupby(date_col).size().sort_index()
    cum = counts.cumsum() / counts.sum()

    ends, running = [], 0.0
    for name in ORDER[:-1]:
        running += fractions[name]
        ends.append(cum.index[(cum >= running - 1e-12).to_numpy().argmax()])
    if len(set(ends)) < len(ends) or (ends and ends[-1] == cum.index[-1]):
        raise ValueError("Jumlah tanggal terlalu sedikit untuk pembagian 4 blok; ubah SPLIT_FRACTIONS.")

    label = pd.Series("test", index=df.index, dtype="object")
    start = None
    for name, end in zip(ORDER[:-1], ends):
        mask = (df[date_col] <= end) if start is None else ((df[date_col] > start) & (df[date_col] <= end))
        label[mask] = name
        start = end
    return label


def split_summary(df: pd.DataFrame, label: pd.Series, date_col: str = "appt_date") -> pd.DataFrame:
    rows = []
    for name in ORDER:
        part = df[label == name]
        rows.append(
            {
                "split": name,
                "n_rows": len(part),
                "share": len(part) / len(df),
                "date_min": part[date_col].min().date(),
                "date_max": part[date_col].max().date(),
                "n_dates": part[date_col].nunique(),
                "n_positive": int(part["y"].sum()),
                "no_show_rate": float(part["y"].mean()),
                "n_patients": part["patient_id"].nunique(),
            }
        )
    return pd.DataFrame(rows)
