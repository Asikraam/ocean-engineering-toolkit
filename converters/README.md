# 🖼️ Engineering Document & Graphic Converters

Koleksi aplikasi desktop berbasis antarmuka grafis (**GUI**) dan mesin render vektor berkecepatan tinggi untuk menghasilkan gambar teknik beresolusi tinggi (300–600 DPI) siap cetak dan laporan.

> [!IMPORTANT]
> **PERINGATAN WAJIB: Jangan Hapus atau Pisahkan `ConvertWmfToPng.ps1`!**  
> File `.ps1` ini adalah **mesin backend wajib**. Jika kamu menyalin atau memindahkan file aplikasi Python (`UniversalConverterApp.py` atau `WmfToPngConverterApp.py`), **pastikan file `ConvertWmfToPng.ps1` selalu berada di satu folder yang sama**. Tanpa file ini, fitur konversi vektor WMF/EMF akan error karena program Python memanggilnya secara otomatis di balik layar.

---

## 🚀 Perbandingan & Pilihan Aplikasi

Folder ini menyediakan 3 varian aplikasi desktop sesuai kebutuhan kerja:

| Aplikasi | Format Input | Format Output | Antarmuka | Fitur Unggulan | Status Wajib |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`UniversalConverterApp.py`** ⭐ *(All-in-One)* | `.wmf`, `.emf`, `.pdf` | `.png` | GUI Dual-Tab | Aplikasi terpadu untuk semua jenis konversi grafis & dokumen dalam 1 jendela | Program Utama |
| **`WmfToPngConverterApp.py`** | `.wmf`, `.emf` | `.png` | GUI Dedicated | Khusus grafik vektor SACS Precede & CAD, kontrol DPI (72–600), background transparan | Program Utama |
| **`PdfToPngTurboApp.py`** | `.pdf` | `.png` | GUI Dedicated | Khusus gambar teknik & laporan PDF, ekstraksi multi-halaman cepat, auto-ZIP | Program Utama |
| **`ConvertWmfToPng.ps1`** ⚠️ | `.wmf`, `.emf` | `.png` | CLI Engine | Mesin render native Windows GDI+ di background | **Wajib Ada di Folder** |

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
