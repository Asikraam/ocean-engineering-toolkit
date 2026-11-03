# Ocean Engineering Toolkit

[![Download ZIP](https://img.shields.io/badge/Download-ZIP_Source_Code-2ea44f?style=for-the-badge&logo=github)](https://github.com/Asikraam/ocean-engineering-toolkit/archive/refs/heads/main.zip)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)

Kumpulan skrip dan modul automasi Python praktis untuk menunjang pekerjaan **Ocean, Coastal, and Offshore Engineering**. Didesain untuk mempercepat alur kerja harian: dari konversi gambar grafik teknis resolusi tinggi, penarikan data batimetri/metocean tanpa browser, hingga generator model struktur Bentley SACS dan pemodelan numerik Delft3D / MIKE 21.

> [!TIP]
> **Tidak punya akun GitHub?** Kamu tidak perlu login sama sekali. Cukup klik tombol hijau **[Download ZIP Source Code](https://github.com/Asikraam/ocean-engineering-toolkit/archive/refs/heads/main.zip)** di atas untuk langsung mengunduh seluruh file ke komputermu.

---

## 🗺️ Alur Kerja & Arsitektur Modul

```mermaid
flowchart TD
    subgraph INPUT ["Input Teknis & Koordinat"]
        A["File SACS (.wmf / .emf / .pdf)"]
        B["Koordinat BBox Wilayah (Lon, Lat)"]
        C["Tata Letak Tiang Pancang (X, Y, Dia)"]
        D["Parameter Geometri Jacket"]
    end

    subgraph TOOLKIT ["Ocean Engineering Toolkit"]
        M1["converters/<br>High-DPI Vector Rasterizer"]
        M2["metocean/<br>Headless DEMNAS & ERA5 Fetcher"]
        M3["hydro/<br>Delft3D & MIKE 21 Structure Engine"]
        M4["sacs/<br>80-Column Card Generator & Launcher"]
    end

    subgraph OUTPUT ["Output Siap Pakai"]
        O1["Gambar PNG Tajam 300+ DPI (Word/LaTeX)"]
        O2["Batimetri XYZ & Reanalisis Gelombang .nc"]
        O3["Thin Dam .thd & Pile Resistance MIKE 21"]
        O4["Input Model sacinp.* & SACS Precede 3D"]
    end

    A --> M1 --> O1
    B --> M2 --> O2
    C --> M3 --> O3
    D --> M4 --> O4
```

---

## 📥 Panduan Unduh & Akses (Untuk Semua Orang)

Repositori ini bersifat **100% Publik**. Siapapun di seluruh dunia bisa mengakses dan menyalin kodenya secara bebas tanpa perlu login:

### Cara 1: Unduh Langsung via Browser (Tanpa Akun GitHub)
1. Klik tombol **[Download ZIP](https://github.com/Asikraam/ocean-engineering-toolkit/archive/refs/heads/main.zip)** di bagian atas halaman ini (atau klik tombol hijau `<> Code` di kanan atas lalu pilih **Download ZIP**).
2. Ekstrak file zip di komputermu.
3. Seluruh skrip Python langsung siap dijalankan!

### Cara 2: Clone via Terminal (Untuk Pengguna Git)
```bash
git clone https://github.com/Asikraam/ocean-engineering-toolkit.git
cd ocean-engineering-toolkit
pip install -r requirements.txt
```

---

## ⚡ Quick Start: 4 Perintah Paling Sering Digunakan

Semua fungsi dapat dipanggil langsung melalui antarmuka perintah terpadu `cli.py`:

```bash
# 1. Ubah grafik plot SACS/Precede (.wmf) jadi PNG tajam 300 DPI untuk laporan
python cli.py wmf2png gambar_sacs.wmf --dpi 300

# 2. Download tile batimetri DEMNAS otomatis via koordinat tanpa buka Chrome
python cli.py demnas --bbox 106.6 -6.1 107.0 -5.8

# 3. Hitung susunan tiang pancang & koefisien hambatan Delft3D FLOW
python cli.py delft-pile --nx 4 --ny 6 --dx 5.0 --dy 5.0 --dia 1.2

# 4. Generate kartu SACS 3-Leg Tripod Jacket otomatis
python cli.py sacs-tripod --depth 45.0 --airgap 12.0
```

---

## 📚 Rincian Modul & Cara Pakai Lengkap

### 1. Document & Graphic Converters (`converters/`)
Mengatasi masalah klasik grafik buram saat mengekspor visualisasi dari Bentley SACS / Precede ke dokumen Microsoft Word atau LaTeX:
- **`wmf_converter.py`**: Menggunakan Windows GDI+ untuk merasterisasi file `.wmf` dan `.emf` menjadi PNG berkualitas publikasi (300 hingga 600 DPI) tanpa pecah/pixelated.
- **`pdf_converter.py`**: Merasterisasi gambar teknik PDF per halaman secara cepat menggunakan Chromium PDFium engine.

```bash
# Mengonversi seluruh isi folder berisi banyak file .wmf sekaligus:
python cli.py wmf2png ./folder_grafik_sacs/ --dpi 300

# Mengonversi laporan drawing PDF ke gambar PNG:
python cli.py pdf2png drawing_pelabuhan.pdf --dpi 300 -o ./output_gambar/
```

---

### 2. Metocean & Bathymetry Fetcher (`metocean/`)
Mengambil data oseanografi dan elevasi langsung ke disk tanpa proses klik manual di web:
- **`demnas.py`**: Menghitung Nomor Lembar Peta (NLP skala 1:50.000) berdasarkan bounding box koordinat geodetik, mengunduh tile DEMNAS secara *headless*, dan mengekspornya ke format ASCII XYZ (`.xyz`) untuk mesh pemodelan.
- **`ecmwf_era5.py`**: Menghubungkan script ke Copernicus Climate Data Store (CDS API) untuk menarik data historis tinggi gelombang signifikan ($H_s$), periode ($T_p$), arah gelombang, dan angin 10 meter ($u_{10}, v_{10}$) dalam format NetCDF (`.nc`).

```bash
# Menarik DEMNAS untuk wilayah pesisir tertentu:
python cli.py demnas --bbox 106.5 -6.2 107.0 -5.8 -o ./demnas_tiles/

# Menarik gelombang ERA5 satu bulan penuh:
python cli.py era5 --years 2023 --months 1 --bbox 5.0 95.0 -11.0 141.0 -o era5_waves.nc
```

---

### 3. Hydrodynamic Modeling Helper (`hydro/`)
Otomasi definisi batas struktur penghalang untuk software pemodelan hidrodinamika pantai:
- **`delft3d_pile.py`**: Menghitung koefisien rugi-daya (*quadratic energy loss coefficient*, $c_{loss}$) untuk barisan tiang pancang (dermaga/jacket) yang direpresentasikan sebagai *porous plate* di Delft3D FLOW, serta membuat file *thin dam* (`.thd`).
- **`mike21_pile.py`**: Menghasilkan file spesifikasi tahanan tiang pancang ASCII untuk modul DHI MIKE 21 HD FM.

```bash
# Format pemakaian untuk konfigurasi 4x6 tiang:
python cli.py delft-pile --nx 4 --ny 6 --dx 5.0 --dy 5.0 --dia 1.2 -o piles.csv
```

---

### 4. SACS Offshore Automation (`sacs/`)
Otomasi pra-proses analisis struktur lepas pantai:
- **`cards.py`**: Generator kartu 80-kolom fixed-format (`JOINT`, `MEMBER`, `SECT`, `PGRP`) standar SACS 2025.
- **`runner.py`**: Menjalankan Bentley SACS Executive dan membuka Precede 3D modeler secara aman tanpa risiko auto-close.

```bash
# Buka SACS Precede langsung dari terminal:
python cli.py sacs-precede
```

---

## 📂 Struktur Repositori

```
ocean-engineering-toolkit/
├── converters/               # Modul konversi grafis & dokumen
│   ├── wmf_converter.py
│   └── pdf_converter.py
├── metocean/                 # Modul unduh DEMNAS & ECMWF ERA5
│   ├── demnas.py
│   └── ecmwf_era5.py
├── hydro/                    # Modul struktur tiang Delft3D & MIKE 21
│   ├── delft3d_pile.py
│   └── mike21_pile.py
├── sacs/                     # Modul kartu SACS & runner
│   ├── cards.py
│   └── runner.py
├── examples/                 # Contoh file input & hasil tes
├── cli.py                    # Antarmuka CLI utama
├── requirements.txt          # Daftar dependencies Python
├── LICENSE                   # Lisensi open-source MIT
└── README.md                 # Dokumentasi proyek
```

---

## 📄 Lisensi

Didistribusikan di bawah Lisensi MIT. Siapapun bebas menggunakan, menyalin, dan memodifikasi untuk keperluan riset maupun pekerjaan profesional. Lihat file [LICENSE](LICENSE) untuk ketentuan lengkap.
