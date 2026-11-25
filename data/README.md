# Data card — Medical Appointment No Shows (Kaggle)

CSV **tidak** di-commit ke repo. Unduh sendiri, lalu isi tabel provenance di bawah.

| Item | Isian |
|---|---|
| Nama dataset | Medical Appointment No Shows |
| Pemilik di Kaggle | `joniarroba` |
| URL | https://www.kaggle.com/datasets/joniarroba/noshowappointments |
| Tanggal unduh | 2026-11-19 |
| Versi/berkas | `KaggleV2-May-2016.csv`, 10.739.535 byte, SHA-256 `9132d3e7d0246617df9041d3764f20ad6f08e7b0d9f0997fa254fc5e52eda27d` (diverifikasi 2026-11-19) |
| Lisensi di halaman Kaggle | CC BY-NC-SA 4.0 (dicek di halaman Kaggle pada 2026-11-25) |
| Asal data primer | Janji temu rumah sakit publik di Vitória, Espírito Santo, Brasil (menurut deskripsi dataset dan Salazar et al., 2022) |
| Unit observasi | 1 baris = 1 janji temu |
| Target | `No-show`: `Yes` = pasien **TIDAK hadir** (kelas positif = no-show) |

## Cara mengunduh
```bash
# Opsi 1: Kaggle CLI (butuh ~/.kaggle/kaggle.json -- JANGAN commit)
pip install kaggle
kaggle datasets download -d joniarroba/noshowappointments -p data/raw --unzip
# Opsi 2: unduh manual dari browser lalu taruh di data/raw/
sha256sum data/raw/*.csv        # catat di tabel di atas
```

## Kamus kolom (ejaan asli Kaggle dipertahankan)
| Kolom | Arti | Dipakai sebagai fitur? |
|---|---|---|
| PatientId | ID pasien | Tidak (identitas; hanya untuk cluster bootstrap) |
| AppointmentID | ID janji temu | Tidak (identitas/proxy waktu pencatatan) |
| Gender | F/M | Ya (ablation `no_proxy` menghapusnya) |
| ScheduledDay | Waktu janji dijadwalkan | Ya (jam; dan untuk `waiting_days`) |
| AppointmentDay | Tanggal janji temu | Ya (hari-dalam-minggu) + **dasar split kronologis** |
| Age | Umur | Ya |
| Neighbourhood | Lingkungan/lokasi | Ya (ablation `no_proxy` menghapusnya) |
| Scholarship | Penerima bantuan sosial (Bolsa Família) | Ya (ablation `no_proxy` menghapusnya) |
| Hipertension / Diabetes / Alcoholism | Kondisi kronis (0/1) | Ya |
| Handcap | Tingkat disabilitas (0–4) | Ya (dikelompokkan 0/1/2+) |
| SMS_received | Menerima SMS pengingat (0/1) | Ya — **observasional, bukan efek kausal** |
| No-show | Yes/No | **Target** |

## Isu kualitas yang wajib dicek dan dilaporkan
Jumlah angka-angka berikut **diisi dari `results/full/data_audit.json`**, bukan dari ingatan atau README repo lain:
umur negatif / sangat besar, `waiting_days` negatif, nilai `Handcap` > 1, duplikasi `AppointmentID`, pasien dengan banyak janji temu, rentang tanggal janji temu, jumlah tanggal unik.


## Catatan asal data untuk run yang dipakai di paper

- File: `KaggleV2-May-2016.csv` (10.739.535 byte), 110.527 baris, 14 kolom
- SHA-256: `9132d3e7d0246617df9041d3764f20ad6f08e7b0d9f0997fa254fc5e52eda27d`
- Sumber: https://www.kaggle.com/datasets/joniarroba/noshowappointments
- Tanggal unduh: 2026-11-19  |  Lisensi : CC BY-NC-SA 4.0
- File ini tidak di-commit (`data/raw/` ada di `.gitignore`); jalankan `python -m src.run_experiments --data data/raw/KaggleV2-May-2016.csv`.
