"""
# WMF & EMF Vector to PNG Converter App

Desktop GUI tool designed to convert AutoCAD, MicroStation, and Microsoft Office vector metafiles (`.wmf`, `.emf`) into high-resolution, anti-aliased PNG images without line loss or color degradation.

## Features
- **Ultra-HD Vector Rasterization**: Windows Native GDI+ engine renders curves and lines with maximum fidelity.
- **Transparency Support**: Key out solid white backgrounds to produce transparent vector cuts.
- **Custom Dimensions**: Scale up to 10x or specify precise target DPI (e.g. 300/600 DPI).
- **Batch Processing**: Convert individual files or recursive directory structures with a single click.

## Requirements
```bash
pip install -r requirements.txt
```

## How to Run
```bash
python WmfToPngConverterApp.py
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg

CURRENT_DIR = Path(__file__).resolve().parent
CONVERTER_EXE = CURRENT_DIR / "WmfToPngConverter.exe"
CONVERTER_PS1 = CURRENT_DIR / "ConvertWmfToPng.ps1" if (CURRENT_DIR / "ConvertWmfToPng.ps1").exists() else CURRENT_DIR / "Convert-WmfToPng.ps1"


def get_windows_apps_light_theme() -> bool:
    """Deteksi apakah Windows menggunakan mode terang (Light Theme)."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return bool(val == 1)
    except Exception:
        return True


class WmfToPngApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WMF to PNG Converter")
        self.geometry("640x530")
        self.minsize(600, 500)

        self.selected_files = []
        self.is_folder_mode = False
        self.last_output_dir = None

        # Default tema mengikuti preferensi sistem Windows
        self.is_dark = not get_windows_apps_light_theme()

        self.setup_theme_palette()
        self.setup_styles()
        self.create_widgets()
        self.apply_theme()

    def setup_theme_palette(self):
        """Definisi palet warna untuk Mode Terang & Mode Gelap ber-kontras tinggi."""
        if self.is_dark:
            self.c_win = "#0f172a"          # Background jendela utama
            self.c_card = "#1e293b"         # Background kartu
            self.c_border = "#334155"       # Garis tepi kartu & input
            self.c_border_focus = "#38bdf8" # Garis tepi saat aktif
            self.c_title = "#f8fafc"        # Judul utama (putih terang)
            self.c_desc = "#94a3b8"         # Subjudul / deskripsi
            self.c_text = "#f1f5f9"         # Teks umum / label
            self.c_muted = "#94a3b8"        # Teks bantuan
            self.c_entry_bg = "#0f172a"     # Kotak input
            self.c_entry_fg = "#ffffff"     # Teks dalam input
            self.c_btn_p_bg = "#2563eb"     # Tombol primer (Royal Blue)
            self.c_btn_p_fg = "#ffffff"
            self.c_btn_p_act = "#1d4ed8"
            self.c_btn_s_bg = "#334155"     # Tombol sekunder
            self.c_btn_s_fg = "#f8fafc"
            self.c_btn_s_act = "#475569"
            self.c_btn_s_bdr = "#475569"
            self.c_prog_bg = "#1e293b"
            self.c_prog_fg = "#38bdf8"
            self.theme_btn_text = "☀️ Mode Terang"
        else:
            self.c_win = "#f1f5f9"          # Background jendela (Slate 100 soft)
            self.c_card = "#ffffff"         # Background kartu (Putih bersih)
            self.c_border = "#cbd5e1"       # Garis tepi tegas & jelas (Slate 300)
            self.c_border_focus = "#2563eb" # Garis tepi saat aktif
            self.c_title = "#0f172a"        # Judul utama (Hitam pekat Slate 900)
            self.c_desc = "#64748b"         # Subjudul (Abu-abu elegan Slate 500)
            self.c_text = "#1e293b"         # Teks label (Slate 800 - kontras tinggi)
            self.c_muted = "#64748b"        # Teks bantuan
            self.c_entry_bg = "#ffffff"     # Kotak input putih bersih
            self.c_entry_fg = "#0f172a"     # Teks input hitam pekat
            self.c_btn_p_bg = "#2563eb"     # Tombol primer (Royal Blue)
            self.c_btn_p_fg = "#ffffff"
            self.c_btn_p_act = "#1d4ed8"
            self.c_btn_s_bg = "#ffffff"     # Tombol sekunder (Putih ber-border)
            self.c_btn_s_fg = "#1e293b"
            self.c_btn_s_act = "#f1f5f9"
            self.c_btn_s_bdr = "#cbd5e1"
            self.c_prog_bg = "#e2e8f0"
            self.c_prog_fg = "#2563eb"
            self.theme_btn_text = "🌙 Mode Gelap"

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

    def toggle_theme(self):
        """Beralih antara Mode Terang dan Gelap."""
        self.is_dark = not self.is_dark
        self.setup_theme_palette()
        self.apply_theme()

    def create_widgets(self):
        # 1. Header Bar
        self.header_frame = tk.Frame(self, padx=24, pady=16)
        self.header_frame.pack(fill="x")

        # Sub-frame kiri untuk judul
        title_box = tk.Frame(self.header_frame)
        title_box.pack(side="left", fill="both", expand=True)

        self.lbl_title = tk.Label(
            title_box,
            text="WMF to PNG Converter",
            font=("Segoe UI", 14, "bold")
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_desc = tk.Label(
            title_box,
            text="Konversi format WMF & EMF ke PNG dengan warna akurat dan garis tajam.",
            font=("Segoe UI", 9)
        )
        self.lbl_desc.pack(anchor="w", pady=(2, 0))

        # Tombol ganti tema di pojok kanan atas
        self.btn_theme = tk.Button(
            self.header_frame,
            text=self.theme_btn_text,
            command=self.toggle_theme,
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.btn_theme.pack(side="right")

        # Garis pemisah header
        self.sep_header = tk.Frame(self, height=1)
        self.sep_header.pack(fill="x")

        # 2. Main Content
        self.content_frame = tk.Frame(self, padx=24, pady=16)
        self.content_frame.pack(fill="both", expand=True)

        # Bagian 1: Input Sumber
        self.lbl_input = tk.Label(
            self.content_frame,
            text="File atau Folder Sumber:",
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_input.pack(anchor="w", pady=(0, 4))

        self.input_box = tk.Frame(self.content_frame)
        self.input_box.pack(fill="x", pady=(0, 14))

        self.entry_input = tk.Entry(
            self.input_box,
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1
        )
        self.entry_input.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=5)

        self.btn_files = tk.Button(
            self.input_box,
            text="Pilih File...",
            command=self.browse_wmf_files,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            cursor="hand2"
        )
        self.btn_files.pack(side="left", padx=(0, 6))

        self.btn_folder = tk.Button(
            self.input_box,
            text="Folder...",
            command=self.browse_input_folder,
            font=("Segoe UI", 9),
            relief="flat",
            padx=12,
            cursor="hand2"
        )
        self.btn_folder.pack(side="left")

        # Bagian 2: Kartu Pengaturan
        self.opt_card = tk.Frame(self.content_frame, padx=18, pady=16, highlightthickness=1)
        self.opt_card.pack(fill="x", pady=(0, 14))

        # Row 1: Resolusi
        self.row_res = tk.Frame(self.opt_card)
        self.row_res.pack(fill="x", pady=(0, 10))

        self.lbl_res = tk.Label(
            self.row_res,
            text="Resolusi:",
            font=("Segoe UI", 9, "bold"),
            width=14,
            anchor="w"
        )
        self.lbl_res.pack(side="left")

        self.scale_var = tk.StringVar()
        scale_items = [
            "1x (Ukuran Asli - Garis Tebal seperti MS Paint)",
            "2x (HD 2K - Lebih Tajam & Tetap Pekat)",
            "3x (Super HD 3K)",
            "4x (Ultra HD 4K untuk Cetak)"
        ]
        self.combo_scale = ttk.Combobox(
            self.row_res,
            textvariable=self.scale_var,
            values=scale_items,
            state="readonly",
            width=46
        )
        self.combo_scale.current(0)
        self.combo_scale.pack(side="left")

        # Row 2: Latar Belakang
        self.row_bg = tk.Frame(self.opt_card)
        self.row_bg.pack(fill="x", pady=(0, 10))

        self.lbl_bg = tk.Label(
            self.row_bg,
            text="Latar Belakang:",
            font=("Segoe UI", 9, "bold"),
            width=14,
            anchor="w"
        )
        self.lbl_bg.pack(side="left")

        self.bg_var = tk.StringVar(value="white")

        self.rb_white = tk.Radiobutton(
            self.row_bg,
            text="Putih Solid (Standar Peta & Dokumen)",
            value="white",
            variable=self.bg_var,
            font=("Segoe UI", 9),
            cursor="hand2"
        )
        self.rb_white.pack(side="left", padx=(0, 16))

        self.rb_trans = tk.Radiobutton(
            self.row_bg,
            text="Transparan (PNG Alpha)",
            value="transparent",
            variable=self.bg_var,
            font=("Segoe UI", 9),
            cursor="hand2"
        )
        self.rb_trans.pack(side="left")

        # Row 3: Folder Tujuan
        self.row_out = tk.Frame(self.opt_card)
        self.row_out.pack(fill="x", pady=(0, 4))

        self.lbl_out = tk.Label(
            self.row_out,
            text="Folder Tujuan:",
            font=("Segoe UI", 9, "bold"),
            width=14,
            anchor="w"
        )
        self.lbl_out.pack(side="left")

        self.entry_out = tk.Entry(
            self.row_out,
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        self.btn_browse_out = tk.Button(
            self.row_out,
            text="Ubah...",
            command=self.browse_output_dir,
            font=("Segoe UI", 8),
            relief="flat",
            padx=10,
            cursor="hand2"
        )
        self.btn_browse_out.pack(side="left")

        # Row 4: Checkbox
        self.row_chk = tk.Frame(self.opt_card)
        self.row_chk.pack(fill="x", pady=(8, 0))

        self.var_open_folder = tk.BooleanVar(value=True)
        self.chk_open = tk.Checkbutton(
            self.row_chk,
            text="Buka folder hasil otomatis setelah selesai",
            variable=self.var_open_folder,
            font=("Segoe UI", 9),
            cursor="hand2"
        )
        self.chk_open.pack(side="left")

        # Bagian 3: Tombol Aksi & Progress
        self.btn_convert = tk.Button(
            self.content_frame,
            text="Konversi ke PNG",
            command=self.start_conversion,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=9
        )
        self.btn_convert.pack(fill="x", pady=(4, 8))

        self.prog_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate")
        self.prog_bar.pack(fill="x", pady=(0, 8))

        # Status Bar Bawah
        self.status_bar = tk.Frame(self.content_frame)
        self.status_bar.pack(fill="x")

        self.lbl_status = tk.Label(
            self.status_bar,
            text="Pilih file .wmf atau .emf untuk memulai.",
            font=("Segoe UI", 9)
        )
        self.lbl_status.pack(side="left")

        self.btn_open_result = tk.Button(
            self.status_bar,
            text="Buka Folder Hasil",
            command=self.open_output_dir,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            state="disabled",
            padx=8,
            pady=2
        )
        self.btn_open_result.pack(side="right")

    def apply_theme(self):
        """Menerapkan warna palet aktif ke seluruh widget secara dinamis."""
        self.configure(bg=self.c_win)

        # Header
        self.header_frame.configure(bg=self.c_card)
        for child in self.header_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=self.c_card)
        self.lbl_title.configure(bg=self.c_card, fg=self.c_title)
        self.lbl_desc.configure(bg=self.c_card, fg=self.c_desc)

        # Tombol ganti tema
        self.btn_theme.configure(
            text=self.theme_btn_text,
            bg=self.c_btn_s_bg,
            fg=self.c_btn_s_fg,
            activebackground=self.c_btn_s_act,
            activeforeground=self.c_btn_s_fg,
            highlightbackground=self.c_btn_s_bdr,
            highlightthickness=1
        )

        self.sep_header.configure(bg=self.c_border)

        # Content Frame
        self.content_frame.configure(bg=self.c_win)
        self.lbl_input.configure(bg=self.c_win, fg=self.c_text)
        self.input_box.configure(bg=self.c_win)

        # Input Sumber
        self.entry_input.configure(
            bg=self.c_entry_bg,
            fg=self.c_entry_fg,
            insertbackground=self.c_entry_fg,
            highlightbackground=self.c_border,
            highlightcolor=self.c_border_focus
        )
        self.btn_files.configure(
            bg=self.c_btn_p_bg,
            fg=self.c_btn_p_fg,
            activebackground=self.c_btn_p_act,
            activeforeground=self.c_btn_p_fg
        )
        self.btn_folder.configure(
            bg=self.c_btn_s_bg,
            fg=self.c_btn_s_fg,
            activebackground=self.c_btn_s_act,
            activeforeground=self.c_btn_s_fg,
            highlightbackground=self.c_btn_s_bdr,
            highlightthickness=1
        )

        # Card Pengaturan
        self.opt_card.configure(
            bg=self.c_card,
            highlightbackground=self.c_border
        )
        for row in [self.row_res, self.row_bg, self.row_out, self.row_chk]:
            row.configure(bg=self.c_card)

        self.lbl_res.configure(bg=self.c_card, fg=self.c_text)
        self.lbl_bg.configure(bg=self.c_card, fg=self.c_text)
        self.lbl_out.configure(bg=self.c_card, fg=self.c_text)

        # Radio & Checkbox
        for rb in [self.rb_white, self.rb_trans, self.chk_open]:
            rb.configure(
                bg=self.c_card,
                fg=self.c_text,
                selectcolor=self.c_entry_bg,
                activebackground=self.c_card,
                activeforeground=self.c_title
            )

        # Entry Output
        self.entry_out.configure(
            bg=self.c_entry_bg,
            fg=self.c_entry_fg,
            insertbackground=self.c_entry_fg,
            highlightbackground=self.c_border,
            highlightcolor=self.c_border_focus
        )
        self.btn_browse_out.configure(
            bg=self.c_btn_s_bg,
            fg=self.c_btn_s_fg,
            activebackground=self.c_btn_s_act,
            activeforeground=self.c_btn_s_fg,
            highlightbackground=self.c_btn_s_bdr,
            highlightthickness=1
        )

        # Tombol Konversi
        self.btn_convert.configure(
            bg=self.c_btn_p_bg,
            fg=self.c_btn_p_fg,
            activebackground=self.c_btn_p_act,
            activeforeground=self.c_btn_p_fg
        )

        # Style Combobox & Progressbar
        self.style.configure(
            "TProgressbar",
            troughcolor=self.c_prog_bg,
            background=self.c_prog_fg,
            bordercolor=self.c_border,
            lightcolor=self.c_prog_fg,
            darkcolor=self.c_prog_fg
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=self.c_entry_bg,
            background=self.c_btn_s_bg,
            foreground=self.c_entry_fg,
            darkcolor=self.c_border,
            lightcolor=self.c_border,
            arrowcolor=self.c_text
        )
        self.option_add("*TCombobox*Listbox.background", self.c_entry_bg)
        self.option_add("*TCombobox*Listbox.foreground", self.c_entry_fg)
        self.option_add("*TCombobox*Listbox.selectBackground", self.c_btn_p_bg)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        # Status Bar
        self.status_bar.configure(bg=self.c_win)
        self.lbl_status.configure(bg=self.c_win, fg=self.c_muted)
        self.btn_open_result.configure(
            bg=self.c_card,
            fg=self.c_btn_p_bg,
            activebackground=self.c_win,
            activeforeground=self.c_btn_p_act,
            highlightbackground=self.c_border,
            highlightthickness=1
        )

    def browse_wmf_files(self):
        files = filedialog.askopenfilenames(
            title="Pilih File WMF / EMF",
            filetypes=[("Windows Metafile (*.wmf;*.emf)", "*.wmf;*.emf"), ("Semua File (*.*)", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.is_folder_mode = False
            if len(self.selected_files) == 1:
                p = Path(self.selected_files[0])
                self.entry_input.delete(0, tk.END)
                self.entry_input.insert(0, str(p))
                self.lbl_status.config(text=f"1 file dipilih: {p.name}", fg=self.c_text)
            else:
                self.entry_input.delete(0, tk.END)
                self.entry_input.insert(0, f"{len(self.selected_files)} file dipilih")
                self.lbl_status.config(text=f"{len(self.selected_files)} file siap dikonversi.", fg=self.c_text)

    def browse_input_folder(self):
        d = filedialog.askdirectory(title="Pilih Folder Berisi File WMF/EMF")
        if d:
            self.entry_input.delete(0, tk.END)
            self.entry_input.insert(0, d)
            self.is_folder_mode = True
            self.selected_files = []
            self.lbl_status.config(text=f"Folder: {Path(d).name} (semua file .wmf / .emf di dalamnya)", fg=self.c_text)

    def browse_output_dir(self):
        d = filedialog.askdirectory(title="Pilih Folder Tujuan PNG")
        if d:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, d)

    def get_scale_value(self) -> float:
        idx = self.combo_scale.current()
        scale_map = {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0}
        return scale_map.get(idx, 1.0)

    def open_output_dir(self):
        if self.last_output_dir and Path(self.last_output_dir).exists():
            try:
                os.startfile(str(self.last_output_dir))
            except Exception:
                pass

    def start_conversion(self):
        raw_val = self.entry_input.get().strip().strip('"').strip("'")

        target_files = []
        if self.selected_files:
            target_files = [f for f in self.selected_files if Path(f).exists()]
        elif raw_val:
            p = Path(raw_val)
            if p.is_dir():
                target_files = list(p.rglob("*.wmf")) + list(p.rglob("*.emf"))
            elif p.is_file():
                target_files = [str(p)]

        if not target_files:
            messagebox.showwarning("Perhatian", "Silakan pilih file .wmf / .emf atau folder terlebih dahulu.")
            return

        self.btn_convert.config(state="disabled", text="Sedang Mengonversi...")
        self.btn_open_result.config(state="disabled")
        threading.Thread(target=self.run_process, args=(target_files,), daemon=True).start()

    def run_process(self, target_files: list):
        start_time = time.time()
        total = len(target_files)
        custom_out = self.entry_out.get().strip().strip('"').strip("'")
        scale = self.get_scale_value()
        bg = self.bg_var.get()

        self.prog_bar["maximum"] = total
        self.prog_bar["value"] = 0

        success = 0
        last_dir = None

        for idx, item in enumerate(target_files):
            src = Path(item)
            self.lbl_status.config(
                text=f"Mengonversi ({idx + 1}/{total}): {src.name}...",
                fg=self.c_btn_p_bg
            )

            out_dir = Path(custom_out) if custom_out else src.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            last_dir = out_dir
            dest = out_dir / (src.stem + ".png")

            ok = self.convert_file(src, dest, scale, bg)
            if ok:
                success += 1

            self.prog_bar["value"] = idx + 1
            self.update_idletasks()

        elapsed = time.time() - start_time
        self.last_output_dir = last_dir

        self.btn_convert.config(state="normal", text="Konversi ke PNG")
        if last_dir and last_dir.exists():
            self.btn_open_result.config(state="normal")

        msg = f"Selesai: {success}/{total} file dikonversi ({elapsed:.2f} detik)."
        success_color = "#059669" if not self.is_dark else "#10b981"
        self.lbl_status.config(text=msg, fg=success_color if success == total else "#d97706")

        if self.var_open_folder.get() and last_dir and last_dir.exists():
            try:
                os.startfile(str(last_dir))
            except Exception:
                pass

    def convert_file(self, src: Path, dest: Path, scale: float, bg: str) -> bool:
        if not src.exists():
            return False

        # 1. Gunakan WmfToPngConverter.exe jika ada
        if CONVERTER_EXE.exists():
            cmd = [str(CONVERTER_EXE), str(src), "--scale", str(scale), "--bg", bg, "--out", str(dest.parent)]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                if dest.exists():
                    return True
            except Exception:
                pass

        # 2. Fallback ke PowerShell GDI+
        if CONVERTER_PS1.exists():
            ps_cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(CONVERTER_PS1),
                "-Path", str(src),
                "-Scale", str(scale),
                "-Background", bg.capitalize(),
                "-OutputDir", str(dest.parent)
            ]
            try:
                subprocess.run(ps_cmd, capture_output=True, text=True, check=True)
                if dest.exists():
                    return True
            except Exception:
                pass

        return False


def main():
    app = WmfToPngApp()
    app.mainloop()


if __name__ == "__main__":
    main()
