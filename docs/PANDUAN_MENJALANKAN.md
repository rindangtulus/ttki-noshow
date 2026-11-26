# Panduan menjalankan repo dari nol

Panduan ini disusun hanya dari `README.md`, `data/README.md`, dan kode di `src/`. Perintah di bawah sama untuk Windows dan Linux/macOS, kecuali cara mengaktifkan virtual environment dan pengecekan checksum.

## 1. Siapkan Python dan clone repo

Run yang dicatat di repo memakai Python 3.13.9 (`README.md:28`). Batas minimum paket ada di `requirements.txt`, sedangkan versi persis hasil run ada di `environment-freeze.txt`; keduanya disebut di `README.md:29`.

```bash
git clone <URL_REPO_KELOMPOK>
cd ttki-noshow
```

`<URL_REPO_KELOMPOK>` adalah tempat penanda dari `README.md:43`; ganti dengan URL repo kelompok Anda.

## 2. Buat dan aktifkan virtual environment

```bash
python -m venv .venv
```

Aktifkan:

- Windows: `.venv\Scripts\activate` (`README.md:46`)
- Linux/macOS: `source .venv/bin/activate` (`README.md:46`)

## 3. Pasang paket

```bash
pip install -r requirements.txt
```

Perintah ini berasal dari `README.md:47`.

> **Peringatan:** jangan menjalankan `pip freeze > environment-freeze.txt`. Berkas `environment-freeze.txt` adalah freeze dari run yang dipakai dan dinyatakan "jangan ditimpa" di `README.md:29`. Perintah `pip install -r requirements.txt` sudah cukup untuk menyiapkan lingkungan.

## 4. Jalankan tes tanpa data Kaggle

```bash
pytest -q
```

Ini menguji anti-leakage, split, kalibrator, metrik, dan smoke test memakai data dummy (`README.md:49`, `README.md:82-83`). Jadi tes ini **tidak memerlukan** CSV Kaggle dan angkanya tidak dipakai untuk paper.

## 5. Unduh CSV Kaggle

Dataset dan cara unduhnya ada di `data/README.md:1-24` dan `README.md:20-23`:

```bash
pip install kaggle
kaggle datasets download -d joniarroba/noshowappointments -p data/raw --unzip
```

Opsi lain: unduh dari browser lalu letakkan berkas di `data/raw/` (`data/README.md:22`). Kaggle CLI memakai `~/.kaggle/kaggle.json`, dan berkas itu **jangan pernah di-commit** (`data/README.md:19`, `README.md:111`).

Nama berkas yang dipakai perintah di bawah adalah `KaggleV2-May-2016.csv` (`README.md:22`, `data/README.md:49`). Nilai ukuran dan SHA-256 yang diharapkan tercatat di `data/README.md:11` dan `data/README.md:50`. Di Linux/macOS, `data/README.md:23` memberi contoh `sha256sum data/raw/*.csv`; di Windows gunakan alat checksum yang tersedia, lalu bandingkan dengan nilai di `data/README.md` tanpa mengubah berkas itu.

## 6. Jalankan eksperimen

Dari folder repo, jalankan dua skenario:

```bash
python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv
python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv --feature-set no_proxy
```

Keduanya berasal dari `README.md:52-53` dan contoh di `src/run_experiments.py:3-5`. Skrip menulis hasil ke `results/<feature-set>/`, karena folder keluaran dibentuk dari nilai `--feature-set` (`src/run_experiments.py:53`, `src/run_experiments.py:180-187`). Nilai yang diizinkan adalah `full` dan `no_proxy`; default-nya `full` (`src/run_experiments.py:184`).

Untuk uji cepat, `README.md:56` memberi contoh:

```bash
python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv --n-boot 50 --rf-seeds 1
```

Walau demikian, angka yang dipakai di paper harus berasal dari Jalankan penuh seperti di `README.md:7` dan `README.md:13`. Waktu jalan normalnya beberapa menit karena RF lima seed dan bootstrap 500 kali (`README.md:56`, `README.md:70`).

## 7. Buat gambar

```bash
python -m src.make_figures --results results/full --out figures
```

Perintah ini ada di `README.md:54` dan `src/make_figures.py:1-4`. Skrip membaca `test_predictions.csv`, `metrics_primary.csv`, dan `daily_summary.csv` dari folder hasil yang dipilih (`src/make_figures.py:99-102`), lalu menulis `fig_reliability.png`, `fig_precision_at_k.png`, `fig_capacity_deviation.png`, dan `fig_daily_no_show_rate.png` (`src/make_figures.py:47`, `src/make_figures.py:68`, `src/make_figures.py:80`, `src/make_figures.py:89`, `README.md:39`).

Hasil yang diharapkan setelah langkah 6 dan 7: `results/full/` dan `results/no_proxy/` berisi berkas yang tercantum di bagian "Struktur" `README.md:75-92`, dan `figures/` berisi empat gambar tersebut (`README.md:39`).

## Masalah umum

- **Belum ada CSV di `data/raw/`.** `src/data.py:12-13` membaca path yang diberikan lewat `--data`; jika berkas belum ada, unduh dulu seperti langkah 5 (`data/README.md:17-24`). Path yang dipakai di contoh adalah `data/raw/KaggleV2-May-2016.csv` (`README.md:52`).
- **CSV bukan berkas Kaggle asli atau kolomnya kurang.** `src/data.py:14-19` akan berhenti dengan pesan `Kolom wajib tidak ada: [...]` dan meminta CSV asli `joniarroba/noshowappointments`; daftar kolom yang diharapkan ada di `data/README.md:26-40`.
- **Versi Python tidak sama dengan run yang dicatat.** Run memakai Python 3.13.9 (`README.md:28`), dan `README.md:39` memperingatkan angka bisa berbeda sangat kecil antar platform atau versi paket. Bandingkan dengan `environment-freeze.txt` seperti yang disarankan di `README.md:29` dan `README.md:39`, tetapi jangan menimpa berkas itu.
- **pytest mengira butuh data Kaggle.** Tidak; `README.md:49` menyebut tes memakai data dummy, dan `README.md:83` menegaskan `tests/synthetic_fixture.py` adalah data dummy, bukan untuk paper.
- **Gagal membuat gambar.** `src/make_figures.py:99-102` membaca tiga CSV dari folder `--results`; jalankan langkah 6 lebih dulu dan pastikan folder yang dipilih berisi berkas-berkas itu.
- **Split gagal dengan pesan jumlah tanggal terlalu sedikit.** `src/splits.py:23-24` menolak data yang tidak memiliki cukup tanggal unik untuk empat blok; ini bisa terjadi bila memakai data dummy, bukan CSV Kaggle asli yang dipakai di `README.md:13`.
