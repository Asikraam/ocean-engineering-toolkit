"""
# PDF to PNG Turbo Converter App

High-performance, multi-threaded desktop GUI for rasterizing PDF documents to crystal-clear PNG images.

## Features
- **Turbo Multi-Threading**: Asynchronous background rendering prevents UI freeze during batch conversions.
- **Flexible Page Selection**: Convert all pages or specific page ranges (`1, 2-5, 8`).
- **Resolution Control**: User-selectable DPI options (150 DPI for web, 300 DPI for standard print, 600 DPI for ultra-sharp diagrams).
- **Direct Output or ZIP**: Automatically saves PNG files in dedicated folders or packages them into a clean ZIP archive.

## Requirements
```bash
pip install -r requirements.txt
```
Dependencies:
- `pymupdf >= 1.23.0`
- `Pillow >= 10.0.0`

## How to Run
```bash
python PdfToPngTurboApp.py
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import time
import zipfile
import re
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pymupdf
except ImportError:
    pymupdf = None

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


def parse_page_numbers(page_str: str, total_pages: int) -> list[int]:
    page_str = (page_str or "").strip().lower()
    if not page_str or page_str in ["all", "semua", "*"]:
        return list(range(total_pages))
    
    pages = set()
    parts = [p.strip() for p in page_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            sub = part.split("-")
            try:
                start = max(1, int(sub[0].strip()))
                end = min(total_pages, int(sub[1].strip()))
                if start <= end:
                    pages.update(range(start - 1, end))
            except ValueError:
                pass
        else:
            try:
                val = int(part)
                if 1 <= val <= total_pages:
                    pages.add(val - 1)
            except ValueError:
                pass
    
    result = sorted(list(pages))
    return result if result else list(range(total_pages))


class PDFToPNGTurboApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to PNG Converter")
        self.geometry("560x540")
        self.minsize(500, 480)
        self.configure(bg="#f8fafc")

        self.selected_files = []

        # Style konfigurasi
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.create_widgets()

    def create_widgets(self):
        # Container utama dengan padding seimbang
        main_frame = tk.Frame(self, bg="#f8fafc", padx=20, pady=16)
        main_frame.pack(fill="both", expand=True)

        # Header dengan Tombol Panduan
        top_header = tk.Frame(main_frame, bg="#f8fafc")
        top_header.pack(fill="x")

        lbl_title = tk.Label(
            top_header,
            text="PDF to PNG Converter",
            font=("Segoe UI", 15, "bold"),
            bg="#f8fafc",
            fg="#0f172a"
        )
        lbl_title.pack(side="left")

        btn_tutorial = tk.Button(
            top_header,
            text="📖 Panduan & Tutorial",
            font=("Segoe UI", 8, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.open_tutorial
        )
        btn_tutorial.pack(side="right")

        lbl_desc = tk.Label(
            main_frame,
            text="Ubah dokumen PDF menjadi gambar PNG per halaman dengan kualitas jernih & tajam.",
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#64748b"
        )
        lbl_desc.pack(anchor="w", pady=(2, 14))

        # --- SEKSI 1: File & Folder ---
        card_files = tk.LabelFrame(
            main_frame,
            text=" File & Lokasi ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#334155",
            padx=14,
            pady=10,
            relief="solid",
            bd=1
        )
        card_files.pack(fill="x", pady=(0, 10))

        # Input PDF
        tk.Label(card_files, text="File PDF:", font=("Segoe UI", 9), bg="#ffffff", fg="#334155").pack(anchor="w")
        row_pdf = tk.Frame(card_files, bg="#ffffff")
        row_pdf.pack(fill="x", pady=(2, 8))

        self.entry_pdf = tk.Entry(
            row_pdf,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#0f172a",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.entry_pdf.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=4)

        btn_browse_pdf = tk.Button(
            row_pdf,
            text="Pilih File...",
            command=self.browse_pdf,
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#0f172a",
            activebackground="#e2e8f0",
            relief="solid",
            bd=1,
            padx=10,
            cursor="hand2"
        )
        btn_browse_pdf.pack(side="right")

        # Input Output Folder
        tk.Label(card_files, text="Folder Tujuan (Opsional):", font=("Segoe UI", 9), bg="#ffffff", fg="#334155").pack(anchor="w")
        row_out = tk.Frame(card_files, bg="#ffffff")
        row_out.pack(fill="x", pady=(2, 2))

        self.entry_out = tk.Entry(
            row_out,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#0f172a",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=4)

        btn_browse_out = tk.Button(
            row_out,
            text="Pilih Folder...",
            command=self.browse_output,
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#0f172a",
            activebackground="#e2e8f0",
            relief="solid",
            bd=1,
            padx=10,
            cursor="hand2"
        )
        btn_browse_out.pack(side="right")

        # --- SEKSI 2: Pengaturan ---
        card_opt = tk.LabelFrame(
            main_frame,
            text=" Pengaturan ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#334155",
            padx=14,
            pady=10,
            relief="solid",
            bd=1
        )
        card_opt.pack(fill="x", pady=(0, 12))

        # Dropdown DPI
        row_dpi = tk.Frame(card_opt, bg="#ffffff")
        row_dpi.pack(fill="x", pady=(0, 8))
        tk.Label(row_dpi, text="Kualitas (DPI):", font=("Segoe UI", 9), bg="#ffffff", fg="#334155", width=14, anchor="w").pack(side="left")

        dpi_options = [
            "300 DPI (Standar Cetak HD - Rekomendasi)",
            "200 DPI (Cepat & Teks Tetap Tajam)",
            "150 DPI (Ukuran Ringan / Web)",
            "450 DPI (Super HD - Gambar Teknis / Peta)",
            "600 DPI (Kualitas Arsip Maksimal)"
        ]
        self.dpi_var = tk.StringVar(value=dpi_options[0])
        self.combo_dpi = ttk.Combobox(
            row_dpi,
            textvariable=self.dpi_var,
            values=dpi_options,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.combo_dpi.pack(side="left", fill="x", expand=True)

        # Halaman
        row_page = tk.Frame(card_opt, bg="#ffffff")
        row_page.pack(fill="x", pady=(0, 8))
        tk.Label(row_page, text="Halaman:", font=("Segoe UI", 9), bg="#ffffff", fg="#334155", width=14, anchor="w").pack(side="left")

        self.entry_pages = tk.Entry(
            row_page,
            width=12,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#0f172a",
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.entry_pages.insert(0, "all")
        self.entry_pages.pack(side="left", ipady=2)
        tk.Label(row_page, text="(Ketik 'all' untuk semua, atau misal: 1-5, 8)", font=("Segoe UI", 8), bg="#ffffff", fg="#64748b").pack(side="left", padx=8)

        # Checkboxes
        row_chk = tk.Frame(card_opt, bg="#ffffff")
        row_chk.pack(fill="x", pady=(2, 0))

        self.var_zip = tk.BooleanVar(value=True)
        chk_zip = tk.Checkbutton(
            row_chk,
            text="Buat file .ZIP otomatis",
            variable=self.var_zip,
            bg="#ffffff",
            fg="#0f172a",
            activebackground="#ffffff",
            font=("Segoe UI", 9)
        )
        chk_zip.pack(side="left", padx=(0, 16))

        self.var_open = tk.BooleanVar(value=True)
        chk_open = tk.Checkbutton(
            row_chk,
            text="Buka folder hasil saat selesai",
            variable=self.var_open,
            bg="#ffffff",
            fg="#0f172a",
            activebackground="#ffffff",
            font=("Segoe UI", 9)
        )
        chk_open.pack(side="left")

        # --- SEKSI 3: Tombol Aksi & Status ---
        self.btn_run = tk.Button(
            main_frame,
            text="Mulai Konversi ke PNG",
            command=self.start_conversion_thread,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=9
        )
        self.btn_run.pack(fill="x", pady=(2, 8))

        self.prog_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.prog_bar.pack(fill="x", pady=(0, 6))

        self.lbl_status = tk.Label(
            main_frame,
            text="Siap. Silakan pilih file PDF yang ingin dikonversi.",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 9),
            anchor="w"
        )
        self.lbl_status.pack(fill="x")

    def open_tutorial(self):
        """Buka panduan resmi tutorial penggunaan di browser."""
        import webbrowser
        webbrowser.open("https://github.com/Asikraam/ocean-engineering-toolkit/tree/main/converters#readme")

    def browse_pdf(self):
        files = filedialog.askopenfilenames(
            title="Pilih File PDF",
            filetypes=[("PDF Files (*.pdf)", "*.pdf"), ("All Files (*.*)", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            if len(self.selected_files) == 1:
                self.entry_pdf.delete(0, tk.END)
                self.entry_pdf.insert(0, self.selected_files[0])
                self.lbl_status.config(text=f"1 File dipilih: {Path(self.selected_files[0]).name}", fg="#2563eb")
            else:
                self.entry_pdf.delete(0, tk.END)
                self.entry_pdf.insert(0, f"[{len(self.selected_files)} Files Dipilih]")
                self.lbl_status.config(text=f"{len(self.selected_files)} file PDF dipilih siap dikonversi.", fg="#2563eb")

    def browse_output(self):
        d = filedialog.askdirectory(title="Pilih Folder Penyimpanan")
        if d:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, d)

    def start_conversion_thread(self):
        raw_val = self.entry_pdf.get().strip().strip('"').strip("'")
        if not self.selected_files:
            if raw_val and Path(raw_val).exists():
                self.selected_files = [raw_val]
            else:
                messagebox.showwarning("Peringatan", "Silakan pilih file PDF terlebih dahulu!")
                return

        self.btn_run.config(state="disabled", text="Sedang Mengonversi...")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        total_time_start = time.time()
        try:
            dpi_match = re.search(r'\d+', str(self.dpi_var.get()))
            dpi = int(dpi_match.group()) if dpi_match else 300
            out_dir_str = self.entry_out.get().strip()
            page_filter = self.entry_pages.get().strip()
            make_zip = self.var_zip.get()

            total_pages_all = 0
            all_target_dirs = []

            for pdf_path in self.selected_files:
                pdf_file = Path(pdf_path).resolve()
                if not pdf_file.exists():
                    continue

                if not out_dir_str:
                    safe_stem = re.sub(r'[^\w\-_.]', '_', pdf_file.stem)
                    target_dir = pdf_file.parent / f"{safe_stem}_PNG_{dpi}DPI"
                else:
                    target_dir = Path(out_dir_str).resolve() / f"{pdf_file.stem}_PNG_{dpi}DPI"

                target_dir.mkdir(parents=True, exist_ok=True)
                all_target_dirs.append(target_dir)

                saved_files = []
                if pymupdf:
                    doc = pymupdf.open(str(pdf_file))
                    tot = len(doc)
                    pages_to_convert = parse_page_numbers(page_filter, tot)
                    num_pages = len(pages_to_convert)
                    scale = dpi / 72.0

                    self.prog_bar["maximum"] = num_pages
                    self.prog_bar["value"] = 0

                    for i, page_idx in enumerate(pages_to_convert, start=1):
                        self.lbl_status.config(
                            text=f"Memproses {pdf_file.name}: halaman {page_idx + 1} dari {tot}...",
                            fg="#2563eb"
                        )
                        page = doc[page_idx]
                        pix = page.get_pixmap(dpi=dpi, alpha=False, annots=False)
                        out_path = target_dir / f"Page_{page_idx + 1:03d}.png"
                        pix.save(str(out_path))
                        saved_files.append(out_path)
                        pix = None
                        self.prog_bar["value"] = i
                    doc.close()
                elif pdfium:
                    doc = pdfium.PdfDocument(str(pdf_file))
                    tot = len(doc)
                    pages_to_convert = parse_page_numbers(page_filter, tot)
                    num_pages = len(pages_to_convert)
                    scale = dpi / 72.0

                    self.prog_bar["maximum"] = num_pages
                    self.prog_bar["value"] = 0

                    for i, page_idx in enumerate(pages_to_convert, start=1):
                        self.lbl_status.config(
                            text=f"Memproses {pdf_file.name}: halaman {page_idx + 1} dari {tot}...",
                            fg="#2563eb"
                        )
                        page = doc.get_page(page_idx)
                        bmp = page.render(scale=scale)
                        pil_img = bmp.to_pil()
                        out_path = target_dir / f"Page_{page_idx + 1:03d}.png"
                        pil_img.save(out_path, "PNG", dpi=(dpi, dpi))
                        saved_files.append(out_path)
                        self.prog_bar["value"] = i
                    doc.close()
                total_pages_all += num_pages

                if make_zip and saved_files:
                    self.lbl_status.config(text=f"Mengemas file ZIP untuk {pdf_file.name}...", fg="#2563eb")
                    safe_stem = re.sub(r'[^\w\-_.]', '_', pdf_file.stem)
                    zip_path = target_dir.parent / f"{safe_stem}_PNG_{dpi}DPI.zip"
                    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
                        for f in saved_files:
                            zf.write(f, arcname=f.name)

            elapsed_total = time.time() - total_time_start
            speed = (total_pages_all / elapsed_total) if elapsed_total > 0 else 0

            if self.var_open.get() and all_target_dirs:
                try:
                    os.startfile(str(all_target_dirs[0]))
                except Exception:
                    pass

            summary_msg = (
                f"Konversi selesai!\n\n"
                f"• Total File: {len(self.selected_files)} dokumen\n"
                f"• Total Halaman: {total_pages_all} halaman\n"
                f"• Resolusi: {dpi} DPI\n"
                f"• Waktu Proses: {elapsed_total:.2f} detik\n\n"
                f"Folder Hasil:\n{all_target_dirs[0]}"
            )

            self.lbl_status.config(
                text=f"Selesai! {total_pages_all} halaman berhasil dikonversi ({elapsed_total:.2f} detik).",
                fg="#059669"
            )
            messagebox.showinfo("Konversi Berhasil", summary_msg)

        except Exception as e:
            self.lbl_status.config(text=f"Terjadi kesalahan: {str(e)}", fg="#dc2626")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_run.config(state="normal", text="Mulai Konversi ke PNG")


if __name__ == "__main__":
    app = PDFToPNGTurboApp()
    app.mainloop()
