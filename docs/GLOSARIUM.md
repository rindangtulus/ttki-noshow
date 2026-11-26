# Glosarium istilah yang dipakai di repo TTKI P5

Daftar ini hanya memakai istilah yang memang tertulis di `README.md`, `data/README.md`, atau `src/` pada repo ini. Nomor baris di belakang path menunjukkan letak istilah tersebut saat glosarium ini dibuat.

## no-show
Pasien yang tidak hadir pada janji temu; di repo ini itulah kelas positif (`data/README.md:15`, `README.md:61`). Di kode, `No-show = Yes` diubah menjadi `y = 1` (`src/data.py:68`).
Contoh: baris dengan `No-show` bernilai `Yes` diberi label `y = 1` (`src/data.py:68`).

## threshold
Ambang yang dipakai untuk memutuskan apakah sebuah skor dianggap "positif" atau tidak. Baseline memakai `THRESHOLD_DEFAULT = 0.5`, sedangkan threshold F1 dan threshold kapasitas dipilih hanya pada blok validation (`src/config.py:16`, `README.md:65-68`, `src/metrics.py:49-62`).
Contoh: `thr0.5` menyimpan nilai `0.5` (`src/run_experiments.py:93-99`).

## kalibrasi
Proses menyesuaikan angka probabilitas agar lebih dekat dengan proporsi no-show yang sebenarnya. Kalibrator di repo ini dilatih hanya pada blok calibration, bukan pada data uji (`README.md:67`, `src/run_experiments.py:85-86`).
Contoh: `make_calibrator("platt")` menghasilkan objek kalibrator (`src/models.py:60-61`).

## Platt scaling
Di repo istilah ini ditulis "Kalibrasi Platt" (`README.md:67`) atau "Kalibrasi sigmoid (Platt)" (`src/models.py:39`): probabilitas diubah dengan `sigmoid(a * logit(p) + b)`. Karena bersifat monoton, urutan pasien tidak berubah bila `a > 0` (`README.md:73`, `src/models.py:39`).
Contoh: `p' = sigmoid(a * logit(p) + b)` (`src/models.py:39`).

## isotonic regression
Di repo istilah ini ditulis "kalibrasi isotonik" (`README.md:67`) dan memakai `IsotonicRegression` (`src/models.py:7`): kalibrator monoton tak-menurun yang bisa memberi nilai sama (ties) pada beberapa pasien (`src/models.py:49-57`).
Contoh: `IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")` (`src/models.py:53`).

## ECE
Expected calibration error, yaitu rata-rata berbobot per kelompok skor (bin kuantil, bobot = jumlah janji temu di kelompok itu) dari selisih mutlak antara rata-rata probabilitas prediksi dan proporsi no-show sebenarnya; di repo memakai 10 bin (`src/config.py:18`, `src/metrics.py:82-85`).
Contoh: `expected_calibration_error(y, p, 10)` (`src/metrics.py:82`).

## Brier
Skor yang mengukur rata-rata kuadrat selisih antara probabilitas prediksi dan kejadian sebenarnya; nilai lebih kecil berarti lebih baik (`src/metrics.py:108`, `README.md:69`).
Contoh: `brier_score_loss(y, score)` (`src/metrics.py:108`).

## PR-AUC
Luas di bawah kurva precision-recall yang dihitung dengan `average_precision_score`; di repo ini menjadi metrik utama untuk menilai urutan pasien (`README.md:69`, `src/metrics.py:106`).
Contoh: `pr_auc` adalah salah satu nilai yang ditulis ke `metrics_primary.csv` (`src/metrics.py:106`, `src/run_experiments.py:100-102`).

## ROC-AUC
Luas di bawah kurva ROC yang dihitung dengan `roc_auc_score`; di repo dicantumkan sebagai metrik pembanding (`README.md:69`, `src/metrics.py:107`).
Contoh: `roc_auc_score(y, score)` (`src/metrics.py:107`).

## precision@10%
Dari 10% janji temu dengan skor tertinggi, berapa bagian yang benar-benar no-show; dihitung sebagai `tp / k` dengan `k` = jumlah janji temu pada 10% teratas (`src/config.py:15`, `src/metrics.py:16-24`).
Contoh: `topk_metrics(y, score, tiebreak, 0.10)` menghasilkan kunci `precision@10` (`src/metrics.py:16-28`).

## recall@10%
Dari seluruh no-show yang ada, berapa bagian yang berhasil masuk ke dalam 10% skor tertinggi; dihitung sebagai `tp / pos` (`src/metrics.py:16-27`).
Contoh: kunci `recall@10` pada hasil `topk_metrics(..., 0.10)` (`src/metrics.py:26`).

## lift@10%
Precision@10% dibagi dengan tingkat no-show keseluruhan (`prevalence`), sehingga menunjukkan berapa kali lipat 10% teratas lebih kaya no-show dibanding pemilihan acak (`src/metrics.py:22-27`).
Contoh: `lift@10 = precision@10 / prevalence` (`src/metrics.py:27`).

## bootstrap
Pengambilan sampel ulang secara acak untuk memperkirakan rentang nilai (CI). Di repo ini bootstrap dikelompokkan per `PatientId`, sehingga semua janji temu satu pasien ikut atau keluar bersama, sebanyak `N_BOOTSTRAP = 500` (`src/config.py:17`, `src/run_experiments.py:33-41`, `README.md:70`).
Contoh: `cluster_bootstrap_indices(test["patient_id"].to_numpy(), args.n_boot, rng)` (`src/run_experiments.py:76`).

## seed
Bilangan acak yang dibekukan supaya hasil dapat dijalankan ulang. Di repo, `SEED = 42` untuk seed utama dan `RF_SEEDS = [42, 43, 44, 45, 46]` untuk pengulangan Random Forest (`src/config.py:8-9`, `README.md:35`).
Contoh: `rng = np.random.default_rng(C.SEED)` (`src/run_experiments.py:74`).

## data leakage
Kebocoran data, yaitu ketika informasi yang seharusnya tidak diketahui saat prediksi (misalnya identitas atau hasil di masa depan) ikut masuk ke model. Repo mencegahnya dengan hanya memakai fitur yang diketahui saat penjadwalan, melarang `PatientId`/`AppointmentID` sebagai fitur, memakai split kronologis, dan menguji anti-leakage lewat pytest (`src/features.py:1-3`, `src/features.py:13`, `README.md:49`, `README.md:62-63`).
Contoh: `FORBIDDEN = {"patient_id", "appointment_id", "y", "no_show"}` (`src/features.py:13`).

## split kronologis
Pembagian data berurutan menurut tanggal janji temu: train, calibration, validation, lalu test; satu tanggal tidak pernah dipecah ke dua blok (`src/config.py:11-13`, `src/splits.py:1`, `src/splits.py:9-32`). Di repo porsi yang diminta adalah 60% / 10% / 15% / 15%, sedangkan porsi yang benar-benar terjadi ada di `split_summary.csv` (`README.md:36`, `README.md:62`).
Contoh: `chronological_date_split(df, C.SPLIT_FRACTIONS)` (`src/run_experiments.py:62`).
