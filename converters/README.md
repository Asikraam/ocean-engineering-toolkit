# 🎨 Graphic & Document Converters Studio

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI: Tkinter](https://img.shields.io/badge/GUI-Tkinter%20Native-0284c7?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![DPI Control](https://img.shields.io/badge/Resolution-Up%20to%20600%20DPI-10b981?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)
[![Standalone](https://img.shields.io/badge/Design-100%25%20Self--Contained-8b5cf6?style=for-the-badge)](https://github.com/Asikraam/ocean-engineering-toolkit)

A collection of easy-to-use desktop GUI tools to convert technical drawings, SACS models, CAD plots, and PDF reports into crystal-clear PNG images.

Engineered specifically to solve the common problem of **blurry graphics** when pasting plots from **Bentley SACS, Precede, AutoCAD, or PDF drawings** into Microsoft Word, PowerPoint, or LaTeX reports.

> [!NOTE]
> All applications in this folder are **100% self-contained standalone Python apps**. All rendering engines (Windows GDI+ vector rasterizer and high-speed PDF engines) are embedded directly inside—no external helper scripts or loose files are needed.
> 
> Each app includes a built-in **"📖 Panduan & Tutorial"** button in the top right corner that links directly to this guide.

---

## 🛠️ Applications at a Glance

Choose the application that best fits your workflow:

| Application | Input Files | Output | Best Used For |
| :--- | :--- | :--- | :--- |
| **`UniversalConverterApp.py`**<br>`⭐ Flagship All-in-One` | `.wmf`, `.emf`, `.pdf` | High-DPI `.png` | **Recommended for most users.** Dual-tab window that converts both vector graphics and multi-page PDF documents in one place. Auto-detects Windows Dark/Light mode. |
| **`WmfToPngConverterApp.py`**<br>`Dedicated Vector Studio` | `.wmf`, `.emf` | Lossless `.png` | Dedicated to Bentley SACS, Precede, and AutoCAD vector plots. Includes scaling up to 10x, transparent background removal, and extra border padding. |
| **`PdfToPngTurboApp.py`**<br>`Turbo PDF Extractor` | `.pdf` | 150–600 DPI `.png` | Dedicated to multi-page PDF technical drawings and reports. Features multi-threaded rendering, custom page filtering (`1, 3-5, 8`), and automatic ZIP export. |

---

## ⚡ Quickstart: How to Run

Open your terminal or command prompt inside this folder and run:

```bash
# 1. Run the Flagship All-in-One Studio (Vector + PDF)
python UniversalConverterApp.py

# 2. Run the Dedicated SACS / CAD Vector Converter
python WmfToPngConverterApp.py

# 3. Run the Dedicated PDF Document Extractor
python PdfToPngTurboApp.py
```

> [!TIP]
> **Windows Shortcut:** You can also double-click `UniversalConverterApp.py` directly from File Explorer on Windows.

---

## 📖 Step-by-Step User Guides

### 🖼️ Guide 1: Converting SACS & CAD Vector Graphics (WMF / EMF to PNG)

Use **`UniversalConverterApp.py`** (Tab 1: *WMF & EMF Converter*) or **`WmfToPngConverterApp.py`**:

```
[Select Files / Folder] ➔ [Choose Quality / Scale] ➔ [Set Background] ➔ [Click Convert] ➔ [Done!]
```

1. **Select Your Files:**
   - Click **"Pilih File..."** to select one or multiple `.wmf` / `.emf` files.
   - Or click **"Pilih Folder..."** to convert an entire directory of graphics at once (*Batch Mode*).
2. **Choose Output Folder (Optional):**
   - Click **"Pilih Folder..."** in the destination card to choose where PNG files will be saved.
   - *If left empty, images will be saved automatically in the same folder as the original file.*
3. **Set Quality & Resolution:**
   - **Resolution Scale:** Choose **4x (Ultra HD)** for inserting into Microsoft Word or LaTeX reports, or choose **Physical DPI (300 DPI)** for standard high-quality printing.
4. **Choose Background Style:**
   - **Background Color:** Select *Transparent*, *White*, or *Black*.
   - **Key-Out Solid White:** Check this option to remove the solid white background typical of CAD/SACS exports so your graphic has a clean transparent background.
5. **Start Conversion:**
   - Click **"Mulai Konversi WMF ke PNG"**.
   - Once finished, click **"Buka Folder Hasil"** to open your converted PNG images directly in File Explorer.

---

### 📄 Guide 2: Converting Multi-Page PDF Drawings & Reports to PNG

Use **`UniversalConverterApp.py`** (Tab 2: *PDF Converter*) or **`PdfToPngTurboApp.py`**:

```
[Select PDF File] ➔ [Choose Output Folder] ➔ [Set DPI & Pages] ➔ [Click Convert] ➔ [Done!]
```

1. **Select Your PDF:**
   - Click **"Pilih File PDF..."** and select your engineering drawing or document.
2. **Choose Output Folder (Optional):**
   - Click **"Pilih Folder..."** in the destination card to choose where the images should be saved.
   - A dedicated folder named `[Filename]_PNG_[DPI]DPI` will be created automatically.
3. **Select DPI Resolution:**
   - **150 DPI:** Fast rendering, great for quick web sharing and draft previews.
   - **300 DPI:** Standard for official engineering reports, theses, and publications *(Recommended)*.
   - **600 DPI:** Ultra-sharp detail for dense CAD blueprints and thin vector lines.
4. **Select Page Range (Optional):**
   - Keep `All` to convert every page in the document.
   - Or type specific pages, such as: `1, 3-5, 10` to extract only pages 1, 3, 4, 5, and 10.
5. **Automatic ZIP Packaging (Optional):**
   - Check **"Otomatis kompres semua halaman hasil konversi ke ZIP"** if you want all generated images bundled into a single `.zip` file for easy sharing.
6. **Start Conversion:**
   - Click **"Mulai Konversi PDF ke PNG"**.
   - Watch the live progress bar and percentage counter update in real time: `Memproses [file]: Halaman [X]/[Total] ([Z]%)`.
   - When finished, click **"Buka Folder Hasil"** to inspect your output files.

---

## 🎯 Which DPI Setting Should I Choose?

| DPI Setting | Image Quality | Typical File Size | Best For |
| :---: | :---: | :---: | :--- |
| **150 DPI** | Standard Clean | ~100–300 KB | Fast draft checks, email attachments, web previews. |
| **300 DPI** | High-Definition *(Recommended)* | ~500 KB–1.5 MB | Academic theses, consultant engineering reports, client presentations. |
| **600 DPI** | Ultra-HD Print | ~2–6 MB | Large A1/A0 engineering blueprints, high-detail structural member diagrams, journal publications. |

---

## 🏗️ Architecture & Key Technical Highlights

```
converters/
├── UniversalConverterApp.py    # All-in-One Flagship GUI (WMF/EMF + PDF)
├── WmfToPngConverterApp.py     # Standalone SACS/CAD Vector Metafile Converter
├── PdfToPngTurboApp.py         # Multi-threaded Turbo PDF Rasterizer
└── README.md                   # Complete documentation and user guides
```

### 1. Vector Metafile Engine (WMF / EMF)
- **Windows GDI+ Subsystem:** Uses Windows hardware GDI+ with `HighQualityBicubic` interpolation and `ClearTypeGridFit` font rendering.
- **No Line Degradation:** Eliminates broken joints, missing thin member axes, and distorted CAD font annotations typical of generic online converters.
- **Embedded Script Execution:** The rendering engine is embedded directly inside Python strings and extracted safely at runtime to temporary memory—no external `.ps1` files to manage.

### 2. PDF Rendering Engine (PDF to PNG)
- **Dual-Backend Fallback:** Automatically detects and uses `pypdfium2` (Chromium PDFium) or `PyMuPDF` (`fitz`). If one is absent, the other handles the job seamlessly without crashing.
- **Asynchronous Worker Thread:** Rendering runs on a dedicated background thread, keeping the Tkinter window responsive and smooth.
- **Live Feedback:** Dynamic progress tracking calculates the exact cumulative page count and displays real-time percentages.

---

## 📦 Requirements & Installation

These tools use standard Python libraries. Install the dependencies with a single command:

```bash
pip install pillow pypdfium2
```

*(Optional: you can also install `pip install pymupdf` if you prefer the PyMuPDF backend).*

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>1. Why do my CAD/SACS graphics look transparent?</b></summary>
When the "Key-Out Solid White" option is checked, pure white pixels (#FFFFFF) are automatically converted into transparent pixels. This allows you to paste the graphics into slides or Word documents without an awkward white rectangle background. If you prefer a solid white background, uncheck this option or choose "Putih" as your background color.
</details>

<details>
<summary><b>2. Can I run these converters without administrator privileges?</b></summary>
Yes! The converters use standard user-level Windows APIs and standard Python libraries. No administrator permissions or special registry modifications are required.
</details>

<details>
<summary><b>3. Which app should I use if I am unsure?</b></summary>
Use <b><code>UniversalConverterApp.py</code></b>. It combines the full power of both the Vector (WMF/EMF) and Document (PDF) tools in a clean, modern tabbed interface with automatic Dark/Light theme switching.
</details>

<details>
<summary><b>4. Does it work on large PDF files with 100+ pages?</b></summary>
Yes. The PDF engine uses streaming page extraction to keep memory usage minimal. You can also specify exact page ranges (e.g. <code>1-10</code>) so you only convert the pages you actually need.
</details>

---

## 📄 License & Attribution

Part of the **[Ocean Engineering Toolkit](https://github.com/Asikraam/ocean-engineering-toolkit)**.  
Created by **Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam)).  
Distributed under the **MIT License** — free for personal, academic, and commercial engineering use.
