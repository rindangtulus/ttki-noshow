# TTKI P5 — Threshold, Kalibrasi, dan Prioritisasi Pasien Berisiko No-Show

Repositori eksperimen untuk tugas TTKI (PENS, Semester 5, Topik **P5 — Health Information System: no-show**).

> **Pertanyaan penelitian.** Apakah optimasi threshold dan kalibrasi probabilitas meningkatkan kualitas prioritisasi pasien berisiko no-show pada kapasitas pengingat 10%?

Seluruh angka pada paper wajib berasal dari berkas di `results/` yang dihasilkan skrip repo ini dari **CSV Kaggle asli**.
Berkas di `results/` dan `figures/` dihasilkan dengan menjalankan skrip pada CSV Kaggle asli (lihat "Environment" dan `results/*/run_config.json`).

## Status
- [x] CSV Kaggle diunduh (2026-11-19) dan checksum dicatat di `data/README.md`
- [x] `pytest -q` lulus (6 tes)
- [x] `python -m src.run_experiments ...` dijalankan pada CSV asli (`full` dan `no_proxy`)
- [x] Gambar dibuat (`figures/`)
- [x] Draf naskah tersedia di `paper/` (DOCX/PDF); angka di naskah harus dicocokkan ulang dengan `results/`
- [ ] Revisi sesuai review: belum ada reviewer; `RESPONSE_TO_REVIEW.md` baru diisi jika ada komentar
- [ ] Verifikasi manual referensi: lihat `references/TODO_verifikasi.md` (L1, L4, L13, L14)
- [ ] Pembagian kontribusi diisi: lihat `CONTRIBUTIONS.md`

## Sumber data
- Dataset: *Medical Appointment No Shows*, pemilik Kaggle `joniarroba`: https://www.kaggle.com/datasets/joniarroba/noshowappointments
- Berkas: `KaggleV2-May-2016.csv` (10.739.535 byte, SHA-256 `9132d3e7d0246617df9041d3764f20ad6f08e7b0d9f0997fa254fc5e52eda27d`), diunduh 2026-11-19.
- CSV **tidak** di-commit. Cara unduh, kamus kolom, dan lisensi: lihat `data/README.md`.

## Environment
Run yang dicatat di `results/*/run_config.json` memakai:
- OS: Windows 11 (10.0.26200)
- Python 3.13.9
- Versi paket persisnya ada di `environment-freeze.txt` (mis. numpy 2.5.5, pandas 3.1.1, scikit-learn 1.9.1, matplotlib 3.11.2). Batas minimum ada di `requirements.txt`. Berkas ini adalah freeze dari run yang dipakai; **jangan ditimpa** ulang.

### Catatan tentang `git_commit` di `run_config.json`
Field `git_commit` di `results/*/run_config.json` (`b7a2e9cfaf165ee462d9c9a4b99dc953bc0ab4c0`) **tidak ada di riwayat branch repo ini** (bukan leluhur HEAD; `git log --all` hanya menampilkan `911190c` dan `9083bfe`). Hash itu karenanya **bukan bukti reprodusibilitas persis**. Rujukan reprodusibilitas yang dipakai adalah `src/config.py`, `environment-freeze.txt`, checksum CSV di `data/README.md`, dan isi `run_config.json` lainnya. Berkas `run_config.json` sengaja tidak diedit.

## Seed dan split
- Seed utama `SEED = 42`; Random Forest diulang pada seed `42, 43, 44, 45, 46`; cluster bootstrap 500 kali (semuanya di `src/config.py`).
- Split kronologis menurut tanggal janji temu: train 60% / calibration 10% / validation 15% / test 15%. Persentase aktual ada di `results/<fs>/split_summary.csv`.

## Output yang diharapkan
Setelah menjalankan perintah di bagian "Menjalankan", `results/full/` dan `results/no_proxy/` berisi berkas yang tercantum di bagian "Struktur", dan `figures/` berisi empat gambar (`fig_reliability`, `fig_precision_at_k`, `fig_capacity_deviation`, `fig_daily_no_show_rate`). Angka bisa berbeda sangat kecil antar platform atau versi paket; bandingkan dengan `run_config.json`.

## Menjalankan
```bash
git clone <URL_REPO_KELOMPOK>
cd ttki-noshow
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

pytest -q                                            # uji anti-leakage + smoke test (data dummy)

# 1) letakkan CSV Kaggle di data/raw/ (lihat data/README.md), lalu:
python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv                       # skenario utama
python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv --feature-set no_proxy # ablation etika
python -m src.make_figures --results results/full --out figures
```
Waktu jalan ± beberapa menit pada laptop biasa (RF 5 seed + 500 bootstrap). Untuk uji cepat: `--n-boot 50 --rf-seeds 1`.

## Desain eksperimen (dibekukan di `src/config.py`)
| Komponen | Keputusan |
|---|---|
| Unit observasi | 1 janji temu; kelas positif = no-show |
| Split | **Kronologis menurut tanggal janji temu**, tidak memotong satu hari: train ≈60% → calibration ≈10% → validation ≈15% → test ≈15% (persentase aktual dilaporkan di `split_summary.csv`) |
| Fitur | umur, `waiting_days`, jam penjadwalan, hari-dalam-minggu, gender, neighbourhood, scholarship, hipertensi, diabetes, alkoholisme, handicap (0/1/2+), `SMS_received`. **Dilarang:** `PatientId`, `AppointmentID` |
| Model | Logistic Regression (tanpa class weight, deterministik) dan Random Forest (5 seed). **Tanpa** resampling/class weight agar arti probabilitas terjaga |
| Baseline | LR & RF, threshold 0,5 |
| Skenario A | Threshold dioptimalkan (max F1) **hanya pada validation** |
| Skenario B | Kalibrasi Platt dan isotonik, di-fit **hanya pada blok calibration** |
| Skenario C | Pilih **top 10%** skor tertinggi pada test (simulasi kapasitas outreach) + threshold-kapasitas dari validation |
| Metrik | PR-AUC (utama), ROC-AUC, Brier, log loss, ECE, slope/intercept kalibrasi, precision@10%, recall@10%, lift@10%, selisih outreach-rate realisasi vs target 10% |
| Ketidakpastian | Cluster bootstrap per `PatientId` (500×) → CI 95%; selisih berpasangan di `paired_deltas.csv`; RF 5 seed (`metrics_seed_summary.csv`) |
| Ablation etika | `--feature-set no_proxy` menghapus gender, neighbourhood, scholarship |

Catatan teoretis yang perlu dibahas di paper: kalibrasi sigmoid (Platt) bersifat monoton ketat sehingga **tidak mengubah ranking** → PR-AUC dan precision@10% identik; efeknya muncul pada Brier/ECE dan pada perilaku threshold. Isotonik dapat menghasilkan skor kembar (ties) sehingga ranking dapat sedikit berubah (ties diputus acak dengan seed tetap).

## Struktur
```
README.md, LICENSE, requirements.txt
environment-freeze.txt   versi Python dan paket dari run yang dipakai (jangan ditimpa)
RESPONSE_TO_REVIEW.md    tabel tanggapan reviewer (placeholder [ISI: ...])
CONTRIBUTIONS.md         pembagian kontribusi + pernyataan kejujuran akademik (placeholder [ISI: ...])
src/            __init__, config, data (audit+bersih), features, splits, models (+kalibrator), metrics, run_experiments, make_figures
tests/          test_pipeline.py (uji anti-leakage, split, kalibrator, metrik, smoke test);
                synthetic_fixture.py = DATA DUMMY, bukan untuk paper
data/README.md  provenance Kaggle (CSV di data/raw/ tidak di-commit)
results/<fs>/   (fs = full, no_proxy) data_audit.json, cleaning_log.json, split_summary.csv, daily_summary.csv,
                metrics_primary.csv, metrics_all_seeds.csv, metrics_seed_summary.csv, paired_deltas.csv,
                thresholds.csv, test_predictions.csv, run_config.json
figures/        fig_reliability, fig_precision_at_k, fig_capacity_deviation, fig_daily_no_show_rate (.png)
references/     literature_matrix.csv (tidak diubah), TODO_verifikasi.md
paper/          naskah (DOCX/PDF) dan response_to_review.md (templat awal)
notebooks/      kosong; semua analisis dijalankan lewat `src/`
```

## Alur (Mermaid)
```mermaid
flowchart TD
    A[CSV Kaggle asli] --> B[Audit + pembersihan terdokumentasi]
    B --> C[Fitur saat penjadwalan; ID dilarang]
    C --> D[Split kronologis per tanggal: train / calibration / validation / test]
    D --> E[Fit model HANYA di train: LR, RF]
    E --> F[Kalibrasi Platt/Isotonik di blok calibration]
    F --> G[Threshold F1 + threshold-kapasitas dari validation]
    G --> H[Evaluasi SEKALI di test: PR-AUC, Brier, ECE, precision@10%]
    H --> I[Cluster bootstrap CI + paper]
```

## Aturan integritas (dari buku petunjuk)
- Jangan menyalin angka dari README/repo lain. Repo referensi `Rachel-Oyeyemi/Medical-Appointment-No-Shows` memuat **metrik dari data sintetis**; kami hanya memakainya sebagai inspirasi alur kerja (tidak ada kode yang disalin). Perbedaan desain: kami tidak memakai class weight/`scale_pos_weight`, menambah blok kalibrasi terpisah, dan mengevaluasi kapasitas 10%.
- Jangan mengubah `src/config.py` atau aturan setelah melihat hasil test. Jika harus, catat di bagian bawah.
- `SMS_received` bersifat observasional: jangan menyimpulkan efek kausal SMS.
- Jangan commit `kaggle.json`, token, atau CSV.
- Pemakaian bantuan AI untuk kode/naskah wajib dilaporkan sesuai kebijakan kelas dan seluruh hasil diverifikasi sendiri.

## Perubahan protokol (isi jika ada)
| Tanggal | Perubahan | Alasan | Dilakukan sebelum/sesudah melihat test? |
|---|---|---|---|
| | | | |

## Atribusi & lisensi
Kode: MIT (lihat `LICENSE`). Dataset: © pemilik Kaggle sesuai lisensi di halaman dataset (lihat `data/README.md`). Referensi: `references/literature_matrix.csv`.
