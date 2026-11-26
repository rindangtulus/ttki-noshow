# Peta angka: bagian paper ke berkas hasil

Nama bagian dan judul Tabel/Gambar di bawah dibaca dari naskah `paper/TTKI_Kelompok05_TopikP5.docx`. Kolom yang disebut benar-benar ada pada header CSV di `results/`; cara gambar dibuat dapat dicek di `src/make_figures.py`. Berkas gambar yang disebut tersedia di `figures/`.

| Bagian pada paper | File hasil sumber | Nama kolom / nilai pada hasil |
|---|---|---|
| 3.1 Data dan pembagian — **Tabel 1** "Pembagian data menurut tanggal janji temu (sumber: `results/full/split_summary.csv`)" | `results/full/split_summary.csv` | `split`, `date_min`, `date_max`, `n_rows`, `share`, `no_show_rate` |
| 3.2 Threshold keputusan (skenario A) — **Tabel 2** "Hasil tiga aturan keputusan pada blok uji (sumber: `results/full/metrics_primary.csv`, `test_predictions.csv`)" | `results/full/metrics_primary.csv`; `results/full/test_predictions.csv` | `metrics_primary.csv`: `model`, `variant`, `metric` dengan nilai `thr0.5:precision`, `thr0.5:recall`, `thr0.5:f1`, `thr0.5:outreach_rate`, `thr0.5:tp`, `thr0.5:fp`, `thr0.5:fn`, `thr0.5:tn`, `thrF1:precision`, `thrF1:recall`, `thrF1:f1`, `thrF1:outreach_rate`, `thrF1:tp`, `thrF1:fp`, `thrF1:fn`, `thrF1:tn`, `precision@10`, `recall@10`; kolom `value`. `test_predictions.csv`: `y`, `LR_raw`, `LR_platt`, `LR_isotonic`, `RF_raw`, `RF_platt`, `RF_isotonic` |
| 3.3 Kalibrasi probabilitas (skenario B) — **Tabel 3** "Kemampuan mengurutkan dan kesesuaian probabilitas pada blok uji (sumber: `results/full/metrics_primary.csv`)" | `results/full/metrics_primary.csv` | `model`, `variant`, `metric` dengan nilai `pr_auc`, `brier`, `ece`, `precision@10`; `value`, `ci_lo`, `ci_hi` |
| 3.3 Kalibrasi probabilitas (skenario B) — **Gambar 2** "Kurva kesesuaian probabilitas pada blok uji" | `results/full/test_predictions.csv` → `figures/fig_reliability.png` | `y`, `LR_raw`, `LR_platt`, `LR_isotonic`, `RF_raw`, `RF_platt`, `RF_isotonic` (`src/make_figures.py:28-47`, `src/make_figures.py:99`) |
| 3.4 Pemilihan pada kapasitas 10% (skenario C) — **Gambar 3** "Persentase janji temu uji yang ditandai ketika persentil ke-90 skor validasi dipakai sebagai threshold" | `results/full/metrics_primary.csv` → `figures/fig_capacity_deviation.png` | `model`, `variant`, `metric` dengan nilai `thrCap:outreach_rate`, `value` (`src/make_figures.py:71-80`, `src/make_figures.py:100`) |

Catatan:

- `figures/fig_reliability.png` dan `figures/fig_capacity_deviation.png` benar-benar ada di folder `figures/`; daftar gambar lain di `README.md:39` dan `README.md:88`.
- Nilai `metric` bukan nama kolom tersendiri di Gambar 3; Gambar 3 menyaring baris dengan `metric == "thrCap:outreach_rate"` lalu memakai kolom `value` untuk tinggi batang (`src/make_figures.py:72-77`).
- Tabel di atas memetakan naskah yang ada di repo; isi angka naskah tidak disalin ke sini. Untuk nilai aktual, buka berkas hasil yang tercantum di kolom "File hasil sumber".
- Terjemahan kolom: `n_rows` = jumlah janji temu, `share` = porsi data, `no_show_rate` = tingkat tidak hadir, `value` = nilai metrik, `ci_lo`/`ci_hi` = batas bawah/atas rentang kepercayaan, `outreach_rate` = persentase janji temu yang ditandai.
