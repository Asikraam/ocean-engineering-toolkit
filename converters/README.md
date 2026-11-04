# 🖼️ Engineering Document & Graphic Converters

Koleksi aplikasi desktop berbasis antarmuka grafis (**GUI**) dan mesin render vektor berkecepatan tinggi untuk menghasilkan gambar teknik beresolusi tinggi (300–600 DPI) siap cetak dan laporan.

---

## 🚀 Perbandingan & Pilihan Aplikasi

Folder ini menyediakan 3 varian aplikasi desktop sesuai kebutuhan kerja:

| Aplikasi | Format Input | Format Output | Antarmuka | Fitur Unggulan |
| :--- | :--- | :--- | :--- | :--- |
| **`UniversalConverterApp.py`** ⭐ *(All-in-One)* | `.wmf`, `.emf`, `.pdf` | `.png` | GUI Dual-Tab | Aplikasi terpadu untuk semua jenis konversi grafis & dokumen dalam 1 jendela |
| **`WmfToPngConverterApp.py`** | `.wmf`, `.emf` | `.png` | GUI Dedicated | Khusus grafik vektor SACS Precede & CAD, kontrol DPI (72–600), key-out background putih transparan |
| **`PdfToPngTurboApp.py`** | `.pdf` | `.png` | GUI Dedicated | Khusus gambar teknik & laporan PDF, ekstraksi multi-halaman cepat, filter rentang halaman, auto-ZIP |
| **`ConvertWmfToPng.ps1`** | `.wmf`, `.emf` | `.png` | CLI Engine | Mesin render berbasis Windows Native GDI+ yang menggerakkan konversi vektor di background |

---

## 💻 Cara Menjalankan Aplikasi

Pastikan Python dan dependensi pendukung sudah terpasang:

```bash
# 1. Install dependensi grafis
pip install pillow pymupdf pypdfium2

# 2. Jalankan aplikasi pilihanmu:
python UniversalConverterApp.py
# ATAU
python WmfToPngConverterApp.py
# ATAU
python PdfToPngTurboApp.py
```

---

## ⚙️ Mengapa Ada File `ConvertWmfToPng.ps1`?

File `ConvertWmfToPng.ps1` adalah **mesin render native Windows GDI+**. 

Aplikasi Python `WmfToPngConverterApp.py` dan `UniversalConverterApp.py` memanggil skrip ini di balik layar untuk memastikan garis vektor halus, teks grafik tidak terdistorsi, dan warna grafik dari Bentley SACS / AutoCAD terkonversi secara presisi tanpa garis putus-putus.
