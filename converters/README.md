# Graphic & Document Converters Studio

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI: Tkinter](https://img.shields.io/badge/GUI-Tkinter%20Native-0284c7?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![DPI Control](https://img.shields.io/badge/Resolution-Up%20to%20600%20DPI-10b981?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)
[![Standalone](https://img.shields.io/badge/Design-100%25%20Self--Contained-8b5cf6?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)

A suite of production-grade desktop GUI applications designed for high-resolution graphics and technical drawing rasterization. Tailored for ocean, civil, and offshore engineering workflows to produce publication-ready figures (300–600 DPI) for reports and journal manuscripts.

All tools in this directory are **100% self-contained standalone Python applications**. All rendering engines (Windows GDI+ vector rasterizer and PDF engines) are embedded internally—no external helper scripts or loose files are required.

Setiap aplikasi dilengkapi tombol **"📖 Panduan & Tutorial"** di pojok kanan atas yang langsung terhubung ke dokumentasi ini.

---

## 🛠️ Applications Overview

| Application | Input Formats | Target Output | Interface | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **`UniversalConverterApp.py`**<br>`⭐ Flagship All-in-One` | `.wmf`, `.emf`, `.pdf` | High-DPI `.png` | Dual-Tab Desktop GUI | Unified converter for both CAD/SACS vector plots and multi-page PDF technical drawings in a single window. Auto-theme detection (Dark/Light). |
| **`WmfToPngConverterApp.py`**<br>`Dedicated Vector Studio` | `.wmf`, `.emf` | Lossless `.png` | Desktop GUI | Specially tuned for Bentley SACS, Precede, and AutoCAD vector metafiles. Hardware GDI+ bicubic anti-aliasing, scale factor up to 10x, and transparent background keying. |
| **`PdfToPngTurboApp.py`**<br>`Turbo Document Extractor` | `.pdf` | 300+ DPI `.png` | Desktop GUI | Multi-threaded asynchronous PDF renderer. Supports custom page ranges (`1, 3-5, 8`), batch directory processing, and automated ZIP packaging. |

---

## ⚡ Quickstart

Launch any converter directly using standard Python:

```bash
# 1. Flagship All-in-One Studio (Vector + PDF)
python UniversalConverterApp.py

# 2. Dedicated SACS / CAD Vector Converter
python WmfToPngConverterApp.py

# 3. Dedicated PDF Document & Drawing Extractor
python PdfToPngTurboApp.py
```

---

## 📖 Panduan Penggunaan Langkah demi Langkah (Tutorial)

### 🖼️ Tutorial 1: Konversi Grafik SACS / CAD (WMF & EMF ke PNG)

Gunakan **`UniversalConverterApp.py`** (Tab *WMF & EMF*) atau **`WmfToPngConverterApp.py`**:

1. **Pilih File Sumber:**
   - Klik tombol **"Pilih File..."** untuk memilih satu atau beberapa file `.wmf` / `.emf`.
   - Atau klik **"Pilih Folder..."** untuk mengonversi seluruh file dalam satu direktori secara sekaligus (*batch mode*).
2. **Atur Kualitas & Resolusi:**
   - **Skala Resolusi:** Pilih opsi **4x (Ultra HD)** untuk disisipkan ke laporan Microsoft Word / LaTeX, atau pilih **DPI Fisik (300 DPI)** untuk standar cetak dokumen teknik.
3. **Pengaturan Background:**
   - Pilih latar belakang: *Transparan*, *Putih*, atau *Hitam*.
   - Centang opsi **"Key-Out Background Putih"** jika kamu ingin menghapus warna putih latar bawaan CAD/SACS agar gambar menjadi transparan.
4. **Mulai Konversi:**
   - Klik tombol **"Mulai Konversi WMF ke PNG"**.
   - Hasil gambar `.png` otomatis disimpan di folder yang sama dengan file sumber.
   - Klik tombol **"Buka Folder Hasil"** untuk langsung melihat gambar hasil konversi.

---

### 📄 Tutorial 2: Konversi Laporan & Drawing PDF ke PNG Tajam

Gunakan **`UniversalConverterApp.py`** (Tab *PDF Converter*) atau **`PdfToPngTurboApp.py`**:

1. **Pilih Dokumen PDF:**
   - Klik **"Pilih File PDF..."** dan tentukan dokumen gambar teknik atau laporan yang ingin diekstrak halamannya.
2. **Tentukan Resolusi (DPI):**
   - **150 DPI:** Pratinjau cepat / penggunaan web.
   - **300 DPI:** Standar dokumen laporan teknik resmi & publikasi jurnal (rekomendasi).
   - **600 DPI:** Kualitas ultra-tinggi untuk drawing CAD bergaris sangat tipis (*fine-line vector*).
3. **Filter Halaman (Opsional):**
   - Biarkan bertuliskan `all` untuk mengonversi seluruh halaman dokumen.
   - Atau ketik halaman tertentu saja, misalnya: `1, 3-5, 10` untuk hanya mengambil halaman 1, 3, 4, 5, dan 10.
4. **Ekspor ZIP Otomatis (Opsional):**
   - Centang **"Export as ZIP Package"** jika kamu ingin seluruh file gambar PNG langsung dikemas dalam 1 arsip `.zip`.
5. **Mulai Ekstraksi:**
   - Klik **"Mulai Konversi PDF"**.
   - Mesin berjalan secara *asynchronous* sehingga jendela aplikasi tetap responsif.

---

## 🏗️ Technical Architecture & Engine Design

```
converters/
├── UniversalConverterApp.py    # All-in-one dual-tab GUI (Vector & PDF)
├── WmfToPngConverterApp.py     # Standalone SACS/CAD vector metafile converter
├── PdfToPngTurboApp.py         # Multi-threaded turbo PDF rasterizer
└── README.md                   # Technical documentation & tutorials
```

### 1. Vector Metafile Engine (WMF / EMF)
- **Engine:** Native Windows GDI+ subsystem with `HighQualityBicubic` interpolation and `ClearTypeGridFit` text rendering.
- **Self-Contained:** The GDI+ rendering pipeline is fully embedded within the Python scripts. When executed on any Windows machine, the engine is initialized dynamically from memory, eliminating loose script dependencies.
- **Fidelity:** Prevents broken line joints, vanishing thin structural member axes, and distorted CAD font annotations typical of generic converters.

### 2. PDF Rendering Engine (PDF to PNG)
- **Dual Backend:** Automatically prioritizes `pypdfium2` (Chromium PDFium) or `PyMuPDF` (`fitz`) depending on local availability.
- **Zero-Block Initialization:** Applications launch instantaneously without triggering blocking background installations.
- **Thread Safety:** Rasterization runs on dedicated background worker threads with thread-safe Tkinter idle task dispatching, preventing GUI lockup during large batch operations.

---

## 📦 Dependencies

Install dependencies via pip:

```bash
pip install pillow pypdfium2
```

*(Optional: `pip install pymupdf` for alternative high-speed PDF backend).*

---

## 📄 License

Part of the **Ocean Engineering Toolkit**, distributed under the MIT License.
