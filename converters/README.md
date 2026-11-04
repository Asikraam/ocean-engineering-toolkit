# Graphic & Document Converters Studio

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI: Tkinter](https://img.shields.io/badge/GUI-Tkinter%20Native-0284c7?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![DPI Control](https://img.shields.io/badge/Resolution-Up%20to%20600%20DPI-10b981?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)
[![Standalone](https://img.shields.io/badge/Design-100%25%20Self--Contained-8b5cf6?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)

A suite of production-grade desktop GUI applications designed for high-resolution graphics and technical drawing rasterization. Tailored for ocean, civil, and offshore engineering workflows to produce publication-ready figures (300–600 DPI) for reports and journal manuscripts.

All tools in this directory are **100% self-contained standalone Python applications**. All rendering engines (Windows GDI+ vector rasterizer and PDF engines) are embedded internally—no external helper scripts or loose files are required.

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

## 🏗️ Technical Architecture & Engine Design

```
converters/
├── UniversalConverterApp.py    # All-in-one dual-tab GUI (Vector & PDF)
├── WmfToPngConverterApp.py     # Standalone SACS/CAD vector metafile converter
├── PdfToPngTurboApp.py         # Multi-threaded turbo PDF rasterizer
└── README.md                   # Technical documentation
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
