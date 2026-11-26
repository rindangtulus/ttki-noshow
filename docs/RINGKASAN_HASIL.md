# Ringkasan hasil untuk orang awam

Semua angka di bawah dibaca dari berkas CSV di `results/full/` dan `results/no_proxy/`. Angka dibulatkan dari nilai asli; path dan kolom sumbernya ditulis di setiap baris atau tabel. Angka `RF` di `metrics_primary.csv` berasal dari seed 42 saja; hasil lima seed `RF` (rata-rata dan simpangan) ada di `results/full/metrics_seed_summary.csv` dan `results/no_proxy/metrics_seed_summary.csv`.

## Apa yang diuji

Repo ini menguji apakah pengaturan ambang keputusan (threshold) dan perbaikan probabilitas (kalibrasi) membantu memilih pasien yang berisiko tidak datang, ketika pengingat hanya cukup untuk sebagian kecil janji temu. Dua set fitur diuji: `full` dan `no_proxy`; keduanya namanya terlihat pada folder `results/full/` dan `results/no_proxy/`. Di dalam tiap hasil ada dua model, `LR` dan `RF`, dengan tiga varian skor, `raw`, `platt`, dan `isotonic` (kolom `model` dan `variant` di `results/full/metrics_primary.csv` dan `results/no_proxy/metrics_primary.csv`).

Data dibagi menurut tanggal janji temu, bukan diacak:

| Blok | n_rows | share | date_min | date_max | no_show_rate | Sumber |
|---|---|---|---|---|---|---|
| train | 67357 | 0.609 | 2016-04-29 | 2016-05-20 | 0.211 | `results/full/split_summary.csv` |
| calibration | 12431 | 0.112 | 2016-05-24 | 2016-05-30 | 0.198 | `results/full/split_summary.csv` |
| validation | 17142 | 0.155 | 2016-05-31 | 2016-06-03 | 0.186 | `results/full/split_summary.csv` |
| test | 13586 | 0.123 | 2016-06-06 | 2016-06-08 | 0.181 | `results/full/split_summary.csv` |

Nilai pada `results/no_proxy/split_summary.csv` sama dengan tabel di atas, jadi pembagian datanya tidak berubah pada skenario `no_proxy`.

## Hasil pemilihan sepuluh persen teratas

Yang dimaksud "sepuluh persen teratas" adalah janji temu dengan skor risiko tertinggi sebanyak porsi yang tertera pada nama metrik `precision@10`, `recall@10`, dan `lift@10`. Berikut hasil untuk skor `raw` (tanpa kalibrasi):

| Skenario | Model | precision@10 | recall@10 | lift@10 | Sumber |
|---|---|---|---|---|---|
| full | LR | 0.334 | 0.184 | 1.843 | `results/full/metrics_primary.csv` (model=LR, variant=raw) |
| full | RF | 0.372 | 0.205 | 2.050 | `results/full/metrics_primary.csv` (model=RF, variant=raw) |
| no_proxy | LR | 0.316 | 0.175 | 1.745 | `results/no_proxy/metrics_primary.csv` (model=LR, variant=raw) |
| no_proxy | RF | 0.361 | 0.199 | 1.993 | `results/no_proxy/metrics_primary.csv` (model=RF, variant=raw) |

Artinya, pada data uji `full`, sekitar 0.334 dari pasien yang dipilih LR benar-benar no-show, dan sekitar 0.372 untuk RF (`results/full/metrics_primary.csv`, kolom `precision@10`). Tingkat no-show pada seluruh data uji adalah 0.181 (`results/full/metrics_primary.csv`, kolom `prevalence`), sehingga `lift@10` RF sebesar 2.050 berarti kelompok teratas itu memiliki konsentrasi no-show lebih tinggi daripada pemilihan acak (`results/full/metrics_primary.csv`, kolom `lift@10`). Pada `no_proxy`, angka yang sama adalah 0.316 dan 0.361 (`results/no_proxy/metrics_primary.csv`, kolom `precision@10`).

## Efek kalibrasi

Kalibrasi mengubah angka probabilitas; tabel ini memperlihatkan apakah perkiraan menjadi lebih dekat (ECE dan Brier lebih kecil) dan apakah kemampuan mengurutkan pasien (PR-AUC) berubah.

| Skenario | Model | Varian | ECE | Brier | PR-AUC | Sumber |
|---|---|---|---|---|---|---|
| full | LR | raw | 0.048 | 0.143 | 0.294 | `results/full/metrics_primary.csv` |
| full | LR | platt | 0.021 | 0.141 | 0.294 | `results/full/metrics_primary.csv` |
| full | LR | isotonic | 0.019 | 0.141 | 0.284 | `results/full/metrics_primary.csv` |
| full | RF | raw | 0.029 | 0.135 | 0.325 | `results/full/metrics_primary.csv` |
| full | RF | platt | 0.017 | 0.135 | 0.325 | `results/full/metrics_primary.csv` |
| full | RF | isotonic | 0.017 | 0.135 | 0.319 | `results/full/metrics_primary.csv` |
| no_proxy | LR | raw | 0.054 | 0.144 | 0.287 | `results/no_proxy/metrics_primary.csv` |
| no_proxy | LR | platt | 0.038 | 0.142 | 0.287 | `results/no_proxy/metrics_primary.csv` |
| no_proxy | LR | isotonic | 0.024 | 0.141 | 0.278 | `results/no_proxy/metrics_primary.csv` |
| no_proxy | RF | raw | 0.027 | 0.135 | 0.326 | `results/no_proxy/metrics_primary.csv` |
| no_proxy | RF | platt | 0.019 | 0.135 | 0.326 | `results/no_proxy/metrics_primary.csv` |
| no_proxy | RF | isotonic | 0.019 | 0.135 | 0.315 | `results/no_proxy/metrics_primary.csv` |

Pada data ini, Platt menurunkan ECE LR `full` dari 0.048 menjadi 0.021 dan ECE RF `full` dari 0.029 menjadi 0.017, tetapi PR-AUC dan `precision@10` tidak berubah (`results/full/metrics_primary.csv`, kolom `ece`, `pr_auc`, `precision@10`). Hal yang sama terlihat pada `no_proxy`: ECE LR turun dari 0.054 menjadi 0.038 dan ECE RF dari 0.027 menjadi 0.019, dengan PR-AUC tetap (`results/no_proxy/metrics_primary.csv`, kolom `ece` dan `pr_auc`).

Selisih berpasangan (kolom `delta`, `ci_lo`, `ci_hi`) menunjukkan arah yang sama:

| Skenario | Perbandingan | Metrik | delta | ci_lo | ci_hi | Sumber |
|---|---|---|---|---|---|---|
| full | LR: platt - raw | ece | -0.026 | -0.034 | -0.017 | `results/full/paired_deltas.csv` |
| full | RF: platt - raw | ece | -0.012 | -0.015 | -0.006 | `results/full/paired_deltas.csv` |
| full | LR: isotonic - raw | pr_auc | -0.010 | -0.015 | -0.007 | `results/full/paired_deltas.csv` |
| full | RF: isotonic - raw | pr_auc | -0.005 | -0.008 | -0.003 | `results/full/paired_deltas.csv` |
| no_proxy | LR: platt - raw | ece | -0.017 | -0.024 | -0.010 | `results/no_proxy/paired_deltas.csv` |
| no_proxy | RF: platt - raw | ece | -0.009 | -0.012 | -0.004 | `results/no_proxy/paired_deltas.csv` |
| no_proxy | LR: isotonic - raw | pr_auc | -0.009 | -0.015 | -0.005 | `results/no_proxy/paired_deltas.csv` |
| no_proxy | RF: isotonic - raw | pr_auc | -0.011 | -0.015 | -0.007 | `results/no_proxy/paired_deltas.csv` |

Jadi kalibrasi membuat angka probabilitas lebih rapi, tetapi tidak otomatis membuat daftar prioritas pasien lebih baik. Isotonik justru menurunkan PR-AUC pada keempat baris isotonic dikurangi raw di atas (`results/full/paired_deltas.csv` dan `results/no_proxy/paired_deltas.csv`, kolom `delta` untuk `isotonic - raw` dan metrik `pr_auc`).

## Efek threshold F1

Threshold 0,5 hampir tidak menandai pasien, sedangkan threshold yang dipilih dengan F1 pada data validation menandai jauh lebih banyak.

| Skenario | Model | F1 pada thr0.5 | F1 pada thrF1 | recall pada thr0.5 | recall pada thrF1 | outreach_rate pada thrF1 | Sumber |
|---|---|---|---|---|---|---|---|
| full | LR | 0.077 | 0.378 | 0.043 | 0.697 | 0.487 | `results/full/metrics_primary.csv` (variant=raw) |
| full | RF | 0.001 | 0.417 | 0.000 | 0.796 | 0.511 | `results/full/metrics_primary.csv` (variant=raw) |
| no_proxy | LR | 0.069 | 0.394 | 0.038 | 0.689 | 0.454 | `results/no_proxy/metrics_primary.csv` (variant=raw) |
| no_proxy | RF | 0.000 | 0.408 | 0.000 | 0.884 | 0.605 | `results/no_proxy/metrics_primary.csv` (variant=raw) |

Nilai ambang yang dipilih untuk skor `raw` adalah: LR `full` 0.206, RF `full` 0.226, LR `no_proxy` 0.212, dan RF `no_proxy` 0.182 (`results/full/thresholds.csv` dan `results/no_proxy/thresholds.csv`, kolom `threshold`, baris `rule=thrF1`). Sementara itu, `outreach_rate` pada ambang kapasitas (`thrCap`) adalah 0.106 dan 0.119 untuk LR dan RF `full`, serta 0.103 dan 0.132 untuk LR dan RF `no_proxy` (`results/full/metrics_primary.csv` dan `results/no_proxy/metrics_primary.csv`, kolom `thrCap:outreach_rate`). Artinya aturan F1 menaikkan recall, tetapi jumlah janji temu yang ditandai tidak sesuai dengan kapasitas pengingat yang diuji; aturan yang mengikuti kapasitas menandai sekitar 10 sampai 13% janji temu (0.103 sampai 0.132 pada `thrCap:outreach_rate`), mendekati target 10% pada nama metrik `precision@10` tetapi tidak persis.

## Batasan yang perlu diingat

- Data hanya mencakup tanggal 2016-04-29 sampai 2016-06-08, dengan jumlah baris harian sebanyak 27 di `results/full/daily_summary.csv` (kolom `appt_date`). Hasil ini tidak diketahui berlaku untuk periode lain.
- Datanya berasal dari satu wilayah, yaitu rumah sakit publik di Vitória, Espírito Santo, Brasil (`data/README.md:13`). Ini bukan gambaran semua rumah sakit atau semua wilayah.
- Tingkat no-show berubah dari 0.211 pada blok `train` menjadi 0.181 pada blok `test` (`results/full/split_summary.csv`, kolom `no_show_rate`), jadi kondisi data uji tidak sama persis dengan data latih.
- Hasil ini tidak membuktikan sebab-akibat. `SMS_received` tercatat sebagai informasi observasional, bukan bukti efek kausal (`README.md:110`, `data/README.md:39`); berkas `results/full/test_predictions.csv` hanya memuat tanggal, label `y`, dan skor model, sehingga tidak ada bukti di sana tentang apa yang terjadi setelah pengingat dikirim.
- Selisih antar skenario fitur tidak dibaca sebagai kebenaran umum: angka `full` dan `no_proxy` berasal dari dua folder hasil yang berbeda (`results/full/metrics_primary.csv`, `results/no_proxy/metrics_primary.csv`).
