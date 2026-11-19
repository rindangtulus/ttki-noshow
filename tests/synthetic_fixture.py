"""Generator data DUMMY berskema Kaggle -- HANYA untuk uji otomatis (smoke test).

Data ini acak. JANGAN dipakai untuk hasil paper. Hasil paper wajib dari CSV Kaggle asli.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_fake_kaggle(n: int = 4000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    appt = pd.Timestamp("2016-04-29") + pd.to_timedelta(rng.integers(0, 40, n), unit="D")
    wait = rng.choice([0, 0, 1, 2, 5, 9, 15, 30], n)
    sched = appt - pd.to_timedelta(wait, unit="D") + pd.to_timedelta(rng.integers(7 * 60, 18 * 60, n), unit="m")
    age = rng.integers(0, 90, n)
    sms = rng.binomial(1, 0.3, n)
    logit = -1.8 + 0.03 * wait - 0.01 * age + 0.2 * sms
    y = rng.random(n) < 1 / (1 + np.exp(-logit))
    return pd.DataFrame(
        {
            "PatientId": rng.integers(1, n // 2, n).astype(float),
            "AppointmentID": np.arange(5_000_000, 5_000_000 + n),
            "Gender": rng.choice(["F", "M"], n),
            "ScheduledDay": sched.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "AppointmentDay": appt.strftime("%Y-%m-%dT00:00:00Z"),
            "Age": age,
            "Neighbourhood": rng.choice([f"N{i}" for i in range(12)], n),
            "Scholarship": rng.binomial(1, 0.1, n),
            "Hipertension": rng.binomial(1, 0.2, n),
            "Diabetes": rng.binomial(1, 0.07, n),
            "Alcoholism": rng.binomial(1, 0.03, n),
            "Handcap": rng.choice([0, 1, 2, 3], n, p=[0.97, 0.02, 0.008, 0.002]),
            "SMS_received": sms,
            "No-show": np.where(y, "Yes", "No"),
        }
    )
