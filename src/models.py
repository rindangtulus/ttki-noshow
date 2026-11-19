"""Model baseline (Logistic Regression, Random Forest) dan kalibrator probabilitas."""
from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import LR_PARAMS, RF_PARAMS


def build_model(name: str, numeric, binary, categorical, seed: int) -> Pipeline:
    """Semua transformasi (scaler, encoder) ada di dalam Pipeline -> hanya di-fit pada train."""
    onehot = OneHotEncoder(handle_unknown="ignore", min_frequency=30, sparse_output=False)
    if name == "LR":
        pre = ColumnTransformer(
            [("num", StandardScaler(), numeric), ("bin", "passthrough", binary), ("cat", onehot, categorical)]
        )
        clf = LogisticRegression(random_state=seed, **LR_PARAMS)
    elif name == "RF":
        pre = ColumnTransformer(
            [("num", "passthrough", numeric), ("bin", "passthrough", binary), ("cat", onehot, categorical)]
        )
        clf = RandomForestClassifier(random_state=seed, **RF_PARAMS)
    else:
        raise ValueError(name)
    return Pipeline([("pre", pre), ("clf", clf)])


def _logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


class PlattCalibrator:
    """Kalibrasi sigmoid (Platt): p' = sigmoid(a * logit(p) + b). Monoton jika a > 0."""

    def fit(self, p, y):
        self.lr_ = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(_logit(p).reshape(-1, 1), y)
        return self

    def predict(self, p):
        return self.lr_.predict_proba(_logit(p).reshape(-1, 1))[:, 1]


class IsotonicCalibrator:
    """Kalibrasi isotonik (non-parametrik, monoton tidak-menurun; dapat menghasilkan nilai sama/ties)."""

    def fit(self, p, y):
        self.iso_ = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(p, y)
        return self

    def predict(self, p):
        return self.iso_.predict(p)


def make_calibrator(kind: str):
    return {"platt": PlattCalibrator, "isotonic": IsotonicCalibrator}[kind]()
