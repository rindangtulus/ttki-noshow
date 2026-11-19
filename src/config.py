"""Konfigurasi eksperimen. Semua keputusan desain DIBEKUKAN di sini sebelum test set dilihat.

Jangan ubah nilai di file ini setelah melihat hasil test; jika harus mengubah, catat
alasannya di README (bagian "Perubahan protokol") dan jalankan ulang seluruh pipeline.
"""
from __future__ import annotations

SEED = 42  # seed utama (LR deterministik; RF memakai SEEDS di bawah)
RF_SEEDS = [42, 43, 44, 45, 46]  # pengulangan untuk Random Forest (mean ± sd)

# Pembagian kronologis berdasarkan TANGGAL JANJI TEMU (AppointmentDay), tidak memotong satu hari.
# train -> calibration -> validation -> test, berurutan menurut waktu.
SPLIT_FRACTIONS = {"train": 0.60, "calibration": 0.10, "validation": 0.15, "test": 0.15}

CAPACITY = 0.10  # kapasitas outreach/pengingat: 10% dari janji temu
THRESHOLD_DEFAULT = 0.5  # threshold baseline
N_BOOTSTRAP = 500  # cluster bootstrap per PatientId pada test set
ECE_BINS = 10

# Aturan pembersihan (dibekukan sebelum melihat hasil)
AGE_MIN, AGE_MAX = 0, 110

# Hyperparameter tetap (tidak di-tuning pada test)
LR_PARAMS = dict(C=1.0, max_iter=1000, solver="lbfgs")  # TANPA class_weight agar probabilitas tidak terdistorsi
RF_PARAMS = dict(n_estimators=300, min_samples_leaf=20, max_features="sqrt", n_jobs=-1)

# Nama kolom pada CSV Kaggle (ejaan asli, termasuk 'Hipertension' dan 'Handcap')
RAW_RENAME = {
    "PatientId": "patient_id",
    "AppointmentID": "appointment_id",
    "Gender": "gender",
    "ScheduledDay": "scheduled_day",
    "AppointmentDay": "appointment_day",
    "Age": "age",
    "Neighbourhood": "neighbourhood",
    "Scholarship": "scholarship",
    "Hipertension": "hypertension",
    "Diabetes": "diabetes",
    "Alcoholism": "alcoholism",
    "Handcap": "handicap",
    "SMS_received": "sms_received",
    "No-show": "no_show",
}
