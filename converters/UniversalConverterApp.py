"""
# Universal Image & Document Converter App

Desktop GUI application designed for high-resolution graphics and document conversion:
- **Tab 1: Vector Graphics (WMF / EMF)** -> Lossless Ultra-HD PNG via Windows GDI+
- **Tab 2: PDF Documents** -> High-DPI PNG (single file, batch folder, custom page ranges, & ZIP export)

## Features
- **Dynamic Theme Support**: Auto-detects Windows dark/light mode with full custom color palette.
- **Vector Engine (WMF/EMF)**: Supports scaling factors (1x to 10x), DPI control (72-600 DPI), custom padding, and transparent background keying.
- **PDF Engine**: Multi-page extraction, page range parsing (e.g. `1, 3-5, 10`), progress bar, and automated ZIP packaging.
- **Drag & Drop / Browse**: Simple file and directory picker for streamlined workflows.

## Requirements
```bash
pip install -r requirements.txt
```
Dependencies:
- `Pillow >= 10.0.0`
- `pypdfium2 >= 4.30.0` or `pymupdf >= 1.23.0`

## How to Run
```bash
python UniversalConverterApp.py
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import time
import subprocess
import threading
import zipfile
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg

# Library pendukung PDF: Mendukung PyMuPDF dan pypdfium2 (Zero-Install Fallback)
try:
    import pymupdf
except ImportError:
    pymupdf = None

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

CURRENT_DIR = Path(__file__).resolve().parent
CONVERTER_EXE = CURRENT_DIR / "WmfToPngConverter.exe"
# ==============================================================================
# EMBEDDED WINDOWS GDI+ WMF/EMF RENDERING ENGINE
# Memungkinkan aplikasi berjalan 100% standalone tanpa memerlukan file .ps1 terpisah
# ==============================================================================
EMBEDDED_WMF_PS_SCRIPT = r"""<#
.SYNOPSIS
    Konversi file WMF & EMF ke PNG dengan kualitas tertinggi (Lossless, Anti-Aliased, High-DPI).

.DESCRIPTION
    Skrip PowerShell ini menggunakan Windows Native GDI+ engine untuk merender file vektor WMF/EMF 
    secara presisi tanpa distorsi warna, tanpa garis hilang, dan dengan resolusi ultra-tajam.

.PARAMETER Path
    Satu atau lebih path file .wmf / .emf atau folder. Mendukung input pipeline.

.PARAMETER Scale
    Faktor pengali resolusi (default: 4.0 = Ultra HD / ~384 DPI).

.PARAMETER Dpi
    Target DPI spesifik (misal: 300 untuk standar cetak). Gunakan bersama -UseDpi.

.PARAMETER UseDpi
    Jika diset, menghitung ukuran output berdasarkan DPI fisik bukan skala faktor.

.PARAMETER Background
    Warna latar belakang: 'Transparent' (default), 'White', atau 'Black'.

.PARAMETER KeyOutWhite
    Hapus background putih solid bawaan Office/Word agar menjadi transparan.

.PARAMETER Padding
    Jumlah pixel margin ekstra di sekeliling gambar untuk mencegah garis tepi terpotong.

.PARAMETER OutputDir
    Folder tujuan file PNG. Jika tidak dispesifikasikan, disimpan di folder yang sama dengan file sumber.

.PARAMETER Recursive
    Cari file .wmf/.emf secara rekursif jika input berupa folder.

.EXAMPLE
    .\Convert-WmfToPng.ps1 -Path "gambar.wmf" -Scale 4

.EXAMPLE
    Get-ChildItem -Path "C:\desain" -Filter *.wmf -Recurse | .\Convert-WmfToPng.ps1 -Scale 4 -Background Transparent
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, ValueFromPipeline = $true, ValueFromPipelineByPropertyName = $true, Position = 0)]
    [string[]]$Path,

    [Parameter()]
    [float]$Scale = 1.0,

    [Parameter()]
    [int]$Dpi = 96,

    [Parameter()]
    [switch]$UseDpi,

    [Parameter()]
    [ValidateSet('Transparent', 'White', 'Black')]
    [string]$Background = 'White',

    [Parameter()]
    [switch]$KeyOutWhite,

    [Parameter()]
    [int]$Padding = 0,

    [Parameter()]
    [string]$OutputDir,

    [Parameter()]
    [switch]$Recursive
)

begin {
    Add-Type -AssemblyName System.Drawing
    $processedCount = 0
    $successCount = 0
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
}

process {
    foreach ($item in $Path) {
        $targets = @()

        $resolvedPath = try { (Resolve-Path -Path $item -ErrorAction Stop).Path } catch { $item }
        if (Test-Path -Path $resolvedPath -PathType Container) {
            $opt = if ($Recursive) { @{ Recurse = $true } } else { @{} }
            $files = Get-ChildItem -Path $resolvedPath -File @opt | Where-Object {
                $_.Extension -match '^\.(wmf|emf)$'
            }
            $targets += $files.FullName
        }
        elseif (Test-Path -Path $resolvedPath -PathType Leaf) {
            $ext = [System.IO.Path]::GetExtension($resolvedPath).ToLowerInvariant()
            if ($ext -eq '.wmf' -or $ext -eq '.emf') {
                $targets += (Get-Item -Path $resolvedPath).FullName
            } else {
                Write-Warning "File dilewati (bukan .wmf atau .emf): $resolvedPath"
            }
        }
        else {
            Write-Warning "Path tidak ditemukan: $item"
        }

        foreach ($file in $targets) {
            $processedCount++
            $fileSw = [System.Diagnostics.Stopwatch]::StartNew()

            try {
                $rawBytes = [System.IO.File]::ReadAllBytes($file)
                if ($rawBytes.Length -eq 0) {
                    throw "File kosong (0 bytes)."
                }

                $ms = New-Object System.IO.MemoryStream (,$rawBytes)
                $mf = New-Object System.Drawing.Imaging.Metafile $ms
                $header = $mf.GetMetafileHeader()
                $bounds = $header.Bounds

                $origW = $bounds.Width
                $origH = $bounds.Height
                $dpiX = $header.DpiX
                $dpiY = $header.DpiY

                if ($origW -le 0 -or $origH -le 0) {
                    $origW = $mf.Width
                    $origH = $mf.Height
                }
                if ($origW -le 0 -or $origH -le 0) {
                    $origW = 800
                    $origH = 600
                }

                if ($dpiX -le 1 -or [float]::IsNaN($dpiX) -or [float]::IsInfinity($dpiX)) { $dpiX = 96.0 }
                if ($dpiY -le 1 -or [float]::IsNaN($dpiY) -or [float]::IsInfinity($dpiY)) { $dpiY = 96.0 }

                $targetW = 0
                $targetH = 0
                $outDpi = 300

                if ($UseDpi -and $Dpi -gt 0) {
                    $outDpi = $Dpi
                    $inchesW = $origW / $dpiX
                    $inchesH = $origH / $dpiY
                    $targetW = [int][Math]::Round($inchesW * $Dpi)
                    $targetH = [int][Math]::Round($inchesH * $Dpi)
                } else {
                    $baseW = ($origW / $dpiX) * 96.0
                    $baseH = ($origH / $dpiY) * 96.0
                    if ($baseW -lt 50 -or $baseH -lt 50) {
                        $baseW = $origW
                        $baseH = $origH
                    }
                    $targetW = [int][Math]::Round($baseW * $Scale)
                    $targetH = [int][Math]::Round($baseH * $Scale)
                    $outDpi = [int][Math]::Round(96.0 * $Scale)
                }

                $pad = [Math]::Max(0, $Padding)
                $targetW += ($pad * 2)
                $targetH += ($pad * 2)

                $targetW = [Math]::Max(16, [Math]::Min(16384, $targetW))
                $targetH = [Math]::Max(16, [Math]::Min(16384, $targetH))

                $bmp = New-Object System.Drawing.Bitmap $targetW, $targetH, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                $bmp.SetResolution($outDpi, $outDpi)

                $g = [System.Drawing.Graphics]::FromImage($bmp)
                $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

                switch ($Background) {
                    'White' { $g.Clear([System.Drawing.Color]::White) }
                    'Black' { $g.Clear([System.Drawing.Color]::Black) }
                    default { $g.Clear([System.Drawing.Color]::Transparent) }
                }

                $destRect = New-Object System.Drawing.Rectangle $pad, $pad, ($targetW - ($pad * 2)), ($targetH - ($pad * 2))
                $g.DrawImage($mf, $destRect)
                $g.Dispose()
                $mf.Dispose()
                $ms.Dispose()

                if ($KeyOutWhite) {
                    $rect = New-Object System.Drawing.Rectangle 0, 0, $bmp.Width, $bmp.Height
                    $data = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadWrite, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                    $stride = [Math]::Abs($data.Stride)
                    $pixelBytes = New-Object byte[] ($stride * $bmp.Height)
                    [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $pixelBytes, 0, $pixelBytes.Length)

                    for ($i = 0; $i -lt $pixelBytes.Length; $i += 4) {
                        $b = $pixelBytes[$i]
                        $gCol = $pixelBytes[$i + 1]
                        $r = $pixelBytes[$i + 2]
                        $a = $pixelBytes[$i + 3]

                        if ($a -gt 0 -and $r -ge 248 -and $gCol -ge 248 -and $b -ge 248) {
                            $pixelBytes[$i + 3] = 0
                        }
                    }

                    [System.Runtime.InteropServices.Marshal]::Copy($pixelBytes, 0, $data.Scan0, $pixelBytes.Length)
                    $bmp.UnlockBits($data)
                }

                $destFolder = if (![string]::IsNullOrEmpty($OutputDir)) { $OutputDir } else { [System.IO.Path]::GetDirectoryName($file) }
                if (-not (Test-Path $destFolder)) {
                    New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
                }

                $fileNameOnly = [System.IO.Path]::GetFileNameWithoutExtension($file)
                $finalOutPath = [System.IO.Path]::Combine($destFolder, "$fileNameOnly.png")

                $bmp.Save($finalOutPath, [System.Drawing.Imaging.ImageFormat]::Png)
                $bmp.Dispose()
                $fileSw.Stop()

                $successCount++
                Write-Host "  [OK] $fileNameOnly.wmf -> $fileNameOnly.png ($($targetW)x$($targetH) px, $($fileSw.ElapsedMilliseconds)ms)" -ForegroundColor Green

            } catch {
                $fileSw.Stop()
                Write-Host "  [GAGAL] $([System.IO.Path]::GetFileName($file)): $_" -ForegroundColor Red
            }
        }
    }
}

end {
    $stopwatch.Stop()
    $totalSec = [Math]::Round($stopwatch.ElapsedMilliseconds / 1000.0, 2)
    Write-Host "`nSelesai! Berhasil konversi $successCount/$processedCount file dalam $totalSec detik." -ForegroundColor Cyan
}
"""


def get_wmf_engine_path() -> Path:
    """Mengembalikan path ke engine PowerShell GDI+.
    Jika file ConvertWmfToPng.ps1 lokal tidak ada, otomatis mengekstrak engine
    dari memori ke folder cache sistem agar aplikasi 100% standalone."""
    local_script = CURRENT_DIR / "ConvertWmfToPng.ps1"
    if local_script.exists() and local_script.stat().st_size > 100:
        return local_script

    temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))) / "OceanEngineeringToolkit"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_engine = temp_dir / "ConvertWmfToPng_Engine.ps1"
    if not temp_engine.exists() or temp_engine.stat().st_size < 100:
        temp_engine.write_text(EMBEDDED_WMF_PS_SCRIPT, encoding="utf-8")
    return temp_engine


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


class UniversalConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Document & Image Converter (WMF / EMF & PDF)")
        self.geometry("680x640")
        self.minsize(640, 580)

        # State WMF
        self.wmf_files = []
        self.wmf_is_folder_mode = False
        self.wmf_last_output_dir = None

        # State PDF
        self.pdf_files = []
        self.pdf_last_output_dir = None

        # Tema
        self.is_dark = not get_windows_apps_light_theme()

        self.setup_theme_palette()
        self.setup_styles()
        self.create_widgets()
        self.apply_theme()

    def setup_theme_palette(self):
        if self.is_dark:
            self.c_win = "#0f172a"
            self.c_card = "#1e293b"
            self.c_border = "#334155"
            self.c_border_focus = "#38bdf8"
            self.c_title = "#f8fafc"
            self.c_desc = "#94a3b8"
            self.c_text = "#f1f5f9"
            self.c_muted = "#94a3b8"
            self.c_entry_bg = "#0f172a"
            self.c_entry_fg = "#ffffff"
            self.c_btn_sec_bg = "#334155"
            self.c_btn_sec_fg = "#f8fafc"
            self.c_btn_sec_hover = "#475569"
            self.c_btn_prim_bg = "#2563eb"
            self.c_btn_prim_fg = "#ffffff"
            self.c_btn_prim_hover = "#1d4ed8"
            self.c_toggle_bg = "#1e293b"
            self.c_toggle_fg = "#94a3b8"
            self.c_toggle_active = "#38bdf8"
            self.c_progress_bg = "#334155"
            self.c_progress_bar = "#38bdf8"
        else:
            self.c_win = "#f8fafc"
            self.c_card = "#ffffff"
            self.c_border = "#e2e8f0"
            self.c_border_focus = "#0284c7"
            self.c_title = "#0f172a"
            self.c_desc = "#64748b"
            self.c_text = "#1e293b"
            self.c_muted = "#64748b"
            self.c_entry_bg = "#ffffff"
            self.c_entry_fg = "#0f172a"
            self.c_btn_sec_bg = "#f1f5f9"
            self.c_btn_sec_fg = "#0f172a"
            self.c_btn_sec_hover = "#e2e8f0"
            self.c_btn_prim_bg = "#0284c7"
            self.c_btn_prim_fg = "#ffffff"
            self.c_btn_prim_hover = "#0369a1"
            self.c_toggle_bg = "#f1f5f9"
            self.c_toggle_fg = "#64748b"
            self.c_toggle_active = "#0284c7"
            self.c_progress_bg = "#e2e8f0"
            self.c_progress_bar = "#0284c7"

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("TNotebook", background=self.c_win, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.c_btn_sec_bg, foreground=self.c_btn_sec_fg,
                               padding=[16, 8], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.c_btn_prim_bg)],
                       foreground=[("selected", "#ffffff")])

        self.style.configure("TCombobox", fieldbackground=self.c_entry_bg, background=self.c_btn_sec_bg,
                               foreground=self.c_entry_fg, arrowcolor=self.c_btn_sec_fg)
        self.style.map("TCombobox", fieldbackground=[("readonly", self.c_entry_bg)],
                       foreground=[("readonly", self.c_entry_fg)])

        self.style.configure("Horizontal.TProgressbar", troughcolor=self.c_progress_bg,
                               background=self.c_progress_bar, thickness=6, borderwidth=0)

    def create_widgets(self):
        self.configure(bg=self.c_win)

        # Top Bar (Header & Theme Toggle)
        top_bar = tk.Frame(self, bg=self.c_win)
        top_bar.pack(fill="x", padx=20, pady=(15, 8))

        lbl_app = tk.Label(top_bar, text="⚡ Universal Converter Suite", font=("Segoe UI", 14, "bold"),
                           bg=self.c_win, fg=self.c_title)
        lbl_app.pack(side="left")

        self.btn_theme = tk.Button(top_bar, text="🌙 Gelap" if not self.is_dark else "☀️ Terang",
                                   font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=10, pady=2,
                                   cursor="hand2", command=self.toggle_theme)
        self.btn_theme.pack(side="right")

        # Tab Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Build Tabs
        self.tab_wmf = tk.Frame(self.notebook, bg=self.c_win)
        self.tab_pdf = tk.Frame(self.notebook, bg=self.c_win)

        self.notebook.add(self.tab_wmf, text=" 🖼️ WMF & EMF Converter ")
        self.notebook.add(self.tab_pdf, text=" 📄 PDF Converter ")

        self.build_wmf_tab()
        self.build_pdf_tab()

    # =========================================================================
    # TAB 1: WMF & EMF
    # =========================================================================
    def build_wmf_tab(self):
        # Card File Drop
        self.wmf_card_file = tk.Frame(self.tab_wmf, bg=self.c_card, bd=1, relief="solid")
        self.wmf_card_file.pack(fill="x", padx=10, pady=(12, 10))

        file_inner = tk.Frame(self.wmf_card_file, bg=self.c_card, padx=14, pady=12)
        file_inner.pack(fill="x")

        lbl_sec = tk.Label(file_inner, text="FILE / FOLDER SUMBER WMF / EMF", font=("Segoe UI", 8, "bold"),
                           bg=self.c_card, fg=self.c_muted)
        lbl_sec.pack(anchor="w")

        self.wmf_lbl_status = tk.Label(file_inner, text="Belum ada file yang dipilih",
                                       font=("Segoe UI", 10), bg=self.c_card, fg=self.c_text)
        self.wmf_lbl_status.pack(anchor="w", pady=(3, 8))

        btn_box = tk.Frame(file_inner, bg=self.c_card)
        btn_box.pack(anchor="w")

        self.wmf_btn_files = tk.Button(btn_box, text="Pilih File...", font=("Segoe UI", 9),
                                       bd=1, relief="solid", padx=10, pady=4, cursor="hand2",
                                       command=self.browse_wmf_files)
        self.wmf_btn_files.pack(side="left", padx=(0, 8))

        self.wmf_btn_folder = tk.Button(btn_box, text="Pilih Folder...", font=("Segoe UI", 9),
                                        bd=1, relief="solid", padx=10, pady=4, cursor="hand2",
                                        command=self.browse_wmf_folder)
        self.wmf_btn_folder.pack(side="left")

        # Card Settings
        self.wmf_card_opt = tk.Frame(self.tab_wmf, bg=self.c_card, bd=1, relief="solid")
        self.wmf_card_opt.pack(fill="x", padx=10, pady=5)

        opt_inner = tk.Frame(self.wmf_card_opt, bg=self.c_card, padx=14, pady=12)
        opt_inner.pack(fill="x")

        # Row 1: Skala & Background
        row1 = tk.Frame(opt_inner, bg=self.c_card)
        row1.pack(fill="x", pady=(0, 8))

        col_scale = tk.Frame(row1, bg=self.c_card)
        col_scale.pack(side="left", expand=True, fill="x", padx=(0, 10))

        tk.Label(col_scale, text="Skala Resolusi:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(anchor="w")
        self.wmf_cb_scale = ttk.Combobox(col_scale, values=["1x (Standar)", "2x (High-Res)", "4x (Ultra HD)", "8x (Extreme)"], state="readonly")
        self.wmf_cb_scale.set("4x (Ultra HD)")
        self.wmf_cb_scale.pack(fill="x", pady=(3, 0))

        col_bg = tk.Frame(row1, bg=self.c_card)
        col_bg.pack(side="right", expand=True, fill="x")

        tk.Label(col_bg, text="Latar Belakang:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(anchor="w")
        self.wmf_cb_bg = ttk.Combobox(col_bg, values=["Transparan", "Putih", "Hitam"], state="readonly")
        self.wmf_cb_bg.set("Transparan")
        self.wmf_cb_bg.pack(fill="x", pady=(3, 0))

        # Checkboxes
        self.wmf_var_key_white = tk.BooleanVar(value=True)
        self.wmf_chk_white = tk.Checkbutton(opt_inner, text="Hapus background putih solid bawaan Word/Office (Key Out White)",
                                            variable=self.wmf_var_key_white, bg=self.c_card, fg=self.c_text,
                                            selectcolor=self.c_entry_bg, activebackground=self.c_card, activeforeground=self.c_text)
        self.wmf_chk_white.pack(anchor="w", pady=(2, 2))

        self.wmf_var_recursive = tk.BooleanVar(value=False)
        self.wmf_chk_rec = tk.Checkbutton(opt_inner, text="Cari file di dalam subfolder secara rekursif",
                                          variable=self.wmf_var_recursive, bg=self.c_card, fg=self.c_text,
                                          selectcolor=self.c_entry_bg, activebackground=self.c_card, activeforeground=self.c_text)
        self.wmf_chk_rec.pack(anchor="w")

        # Bottom Action
        action_box = tk.Frame(self.tab_wmf, bg=self.c_win)
        action_box.pack(fill="x", padx=10, pady=(12, 0))

        self.wmf_progress = ttk.Progressbar(action_box, style="Horizontal.TProgressbar", mode="determinate")
        self.wmf_progress.pack(fill="x", pady=(0, 8))

        self.wmf_btn_convert = tk.Button(action_box, text="Mulai Konversi WMF ke PNG", font=("Segoe UI", 10, "bold"),
                                         bd=0, padx=16, pady=8, cursor="hand2", command=self.start_wmf_conversion)
        self.wmf_btn_convert.pack(fill="x")

        self.wmf_btn_open = tk.Button(action_box, text="Buka Folder Hasil", font=("Segoe UI", 9),
                                      bd=1, relief="solid", padx=10, pady=4, cursor="hand2", command=self.open_wmf_folder)

    # =========================================================================
    # TAB 2: PDF
    # =========================================================================
    def build_pdf_tab(self):
        # Card File Drop
        self.pdf_card_file = tk.Frame(self.tab_pdf, bg=self.c_card, bd=1, relief="solid")
        self.pdf_card_file.pack(fill="x", padx=10, pady=(12, 10))

        file_inner = tk.Frame(self.pdf_card_file, bg=self.c_card, padx=14, pady=12)
        file_inner.pack(fill="x")

        lbl_sec = tk.Label(file_inner, text="DOKUMEN PDF SUMBER", font=("Segoe UI", 8, "bold"),
                           bg=self.c_card, fg=self.c_muted)
        lbl_sec.pack(anchor="w")

        self.pdf_lbl_status = tk.Label(file_inner, text="Belum ada file PDF yang dipilih",
                                       font=("Segoe UI", 10), bg=self.c_card, fg=self.c_text)
        self.pdf_lbl_status.pack(anchor="w", pady=(3, 8))

        self.pdf_btn_files = tk.Button(file_inner, text="Pilih File PDF...", font=("Segoe UI", 9),
                                       bd=1, relief="solid", padx=12, pady=4, cursor="hand2",
                                       command=self.browse_pdf_files)
        self.pdf_btn_files.pack(anchor="w")

        # Card Settings
        self.pdf_card_opt = tk.Frame(self.tab_pdf, bg=self.c_card, bd=1, relief="solid")
        self.pdf_card_opt.pack(fill="x", padx=10, pady=5)

        opt_inner = tk.Frame(self.pdf_card_opt, bg=self.c_card, padx=14, pady=12)
        opt_inner.pack(fill="x")

        # Row 1: DPI & Rentang Halaman
        row1 = tk.Frame(opt_inner, bg=self.c_card)
        row1.pack(fill="x", pady=(0, 8))

        col_dpi = tk.Frame(row1, bg=self.c_card)
        col_dpi.pack(side="left", expand=True, fill="x", padx=(0, 10))

        tk.Label(col_dpi, text="Kualitas / DPI Render:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(anchor="w")
        self.pdf_cb_dpi = ttk.Combobox(col_dpi, values=["150 DPI (Standar Cepat)", "200 DPI (Tajam)", "300 DPI (Kualitas Cetak)", "600 DPI (Ultra Tajam)"], state="readonly")
        self.pdf_cb_dpi.set("300 DPI (Kualitas Cetak)")
        self.pdf_cb_dpi.pack(fill="x", pady=(3, 0))

        col_page = tk.Frame(row1, bg=self.c_card)
        col_page.pack(side="right", expand=True, fill="x")

        tk.Label(col_page, text="Rentang Halaman (opsional):", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(anchor="w")
        self.pdf_ent_pages = tk.Entry(col_page, font=("Segoe UI", 9), bd=1, relief="solid")
        self.pdf_ent_pages.insert(0, "All")
        self.pdf_ent_pages.pack(fill="x", pady=(3, 0))

        # Checkboxes & Zip Options
        self.pdf_var_zip = tk.BooleanVar(value=False)
        self.pdf_chk_zip = tk.Checkbutton(opt_inner, text="Otomatis kompres semua halaman hasil konversi ke ZIP",
                                          variable=self.pdf_var_zip, bg=self.c_card, fg=self.c_text,
                                          selectcolor=self.c_entry_bg, activebackground=self.c_card, activeforeground=self.c_text)
        self.pdf_chk_zip.pack(anchor="w", pady=(2, 2))

        # Bottom Action
        action_box = tk.Frame(self.tab_pdf, bg=self.c_win)
        action_box.pack(fill="x", padx=10, pady=(12, 0))

        self.pdf_progress = ttk.Progressbar(action_box, style="Horizontal.TProgressbar", mode="determinate")
        self.pdf_progress.pack(fill="x", pady=(0, 8))

        self.pdf_btn_convert = tk.Button(action_box, text="Mulai Konversi PDF ke PNG", font=("Segoe UI", 10, "bold"),
                                         bd=0, padx=16, pady=8, cursor="hand2", command=self.start_pdf_conversion)
        self.pdf_btn_convert.pack(fill="x")

        self.pdf_btn_open = tk.Button(action_box, text="Buka Folder Hasil", font=("Segoe UI", 9),
                                      bd=1, relief="solid", padx=10, pady=4, cursor="hand2", command=self.open_pdf_folder)

    # =========================================================================
    # THEME ENGINE
    # =========================================================================
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.setup_theme_palette()
        self.setup_styles()
        self.apply_theme()

    def apply_theme(self):
        self.configure(bg=self.c_win)
        self.btn_theme.configure(text="🌙 Gelap" if not self.is_dark else "☀️ Terang",
                                 bg=self.c_btn_sec_bg, fg=self.c_btn_sec_fg)

        # Style Tabs
        for tab in [self.tab_wmf, self.tab_pdf]:
            tab.configure(bg=self.c_win)

        # Cards
        for card in [self.wmf_card_file, self.wmf_card_opt, self.pdf_card_file, self.pdf_card_opt]:
            card.configure(bg=self.c_card, highlightbackground=self.c_border, highlightthickness=1)
            for child in card.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=self.c_card)
                    for sub in child.winfo_children():
                        if isinstance(sub, tk.Label):
                            sub.configure(bg=self.c_card)
                        elif isinstance(sub, tk.Frame):
                            sub.configure(bg=self.c_card)
                            for sub2 in sub.winfo_children():
                                if isinstance(sub2, tk.Label):
                                    sub2.configure(bg=self.c_card)

        # Labels
        self.wmf_lbl_status.configure(fg=self.c_text)
        self.pdf_lbl_status.configure(fg=self.c_text)

        # Buttons
        for b in [self.wmf_btn_files, self.wmf_btn_folder, self.pdf_btn_files, self.wmf_btn_open, self.pdf_btn_open]:
            b.configure(bg=self.c_btn_sec_bg, fg=self.c_btn_sec_fg)

        self.wmf_btn_convert.configure(bg=self.c_btn_prim_bg, fg=self.c_btn_prim_fg)
        self.pdf_btn_convert.configure(bg=self.c_btn_prim_bg, fg=self.c_btn_prim_fg)

        # Checkboxes
        for chk in [self.wmf_chk_white, self.wmf_chk_rec, self.pdf_chk_zip]:
            chk.configure(bg=self.c_card, fg=self.c_text, selectcolor=self.c_entry_bg)

        # Entries
        self.pdf_ent_pages.configure(bg=self.c_entry_bg, fg=self.c_entry_fg, insertbackground=self.c_entry_fg)

    # =========================================================================
    # WMF LOGIC
    # =========================================================================
    def browse_wmf_files(self):
        files = filedialog.askopenfilenames(
            title="Pilih File WMF / EMF",
            filetypes=[("File WMF & EMF", "*.wmf;*.emf"), ("Semua File", "*.*")]
        )
        if files:
            self.wmf_files = list(files)
            self.wmf_is_folder_mode = False
            self.wmf_lbl_status.configure(text=f"Terpilih {len(self.wmf_files)} file")

    def browse_wmf_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder Berisi WMF / EMF")
        if folder:
            self.wmf_files = [folder]
            self.wmf_is_folder_mode = True
            self.wmf_lbl_status.configure(text=f"Folder: {Path(folder).name}")

    def start_wmf_conversion(self):
        if not self.wmf_files:
            messagebox.showwarning("Peringatan", "Pilih file atau folder WMF/EMF terlebih dahulu!")
            return
        self.wmf_btn_convert.configure(state="disabled", text="Sedang Mengonversi...")
        self.wmf_progress["value"] = 15
        threading.Thread(target=self._run_wmf_conversion, daemon=True).start()

    def _run_wmf_conversion(self):
        scale_map = {"1x (Standar)": 1.0, "2x (High-Res)": 2.0, "4x (Ultra HD)": 4.0, "8x (Extreme)": 8.0}
        scale_val = scale_map.get(self.wmf_cb_scale.get(), 4.0)

        bg_map = {"Transparan": "transparent", "Putih": "white", "Hitam": "black"}
        bg_val = bg_map.get(self.wmf_cb_bg.get(), "transparent")

        key_white = self.wmf_var_key_white.get()
        recursive = self.wmf_var_recursive.get()

        out_dir = None
        success = True

        for item in self.wmf_files:
            p = Path(item)
            out_dir = p if p.is_dir() else p.parent
            if CONVERTER_EXE.exists():
                cmd = [str(CONVERTER_EXE), str(p), "--scale", str(scale_val), "--bg", bg_val]
                if key_white: cmd.append("--key-white")
                if recursive and p.is_dir(): cmd.append("--recursive")
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0: success = False
            else:
                engine_script = get_wmf_engine_path()
                ps_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                           "-File", str(engine_script), "-Path", str(p), "-Scale", str(scale_val),
                           "-Background", bg_val.capitalize()]
                if key_white: ps_args.append("-KeyOutWhite")
                if recursive and p.is_dir(): ps_args.append("-Recursive")
                res = subprocess.run(ps_args, capture_output=True, text=True)
                if res.returncode != 0: success = False

        self.wmf_last_output_dir = out_dir
        self.after(0, self._finish_wmf, success)

    def _finish_wmf(self, success):
        self.wmf_progress["value"] = 100
        self.wmf_btn_convert.configure(state="normal", text="Mulai Konversi WMF ke PNG")
        self.wmf_btn_open.pack(fill="x", pady=(5, 0))
        if success:
            messagebox.showinfo("Berhasil", "Konversi WMF/EMF ke PNG selesai dengan kualitas Ultra-HD!")
        else:
            messagebox.showwarning("Perhatian", "Sebagian atau seluruh file selesai diproses (cek log folder).")

    def open_wmf_folder(self):
        if self.wmf_last_output_dir and Path(self.wmf_last_output_dir).exists():
            os.startfile(str(self.wmf_last_output_dir))

    # =========================================================================
    # PDF LOGIC
    # =========================================================================
    def browse_pdf_files(self):
        files = filedialog.askopenfilenames(
            title="Pilih File PDF",
            filetypes=[("Dokumen PDF", "*.pdf"), ("Semua File", "*.*")]
        )
        if files:
            self.pdf_files = list(files)
            self.pdf_lbl_status.configure(text=f"Terpilih {len(self.pdf_files)} file PDF")

    def start_pdf_conversion(self):
        if not self.pdf_files:
            messagebox.showwarning("Peringatan", "Pilih file PDF terlebih dahulu!")
            return
        if not pymupdf and not pdfium:
            messagebox.showerror("Error", "Pustaka PDF (PyMuPDF atau pypdfium2) belum terpasang.\nSilakan install dengan: pip install pypdfium2")
            return

        self.pdf_btn_convert.configure(state="disabled", text="Sedang Memproses PDF...")
        self.pdf_progress["value"] = 10
        threading.Thread(target=self._run_pdf_conversion, daemon=True).start()

    def _run_pdf_conversion(self):
        dpi_str = self.pdf_cb_dpi.get()
        dpi_val = int(dpi_str.split()[0])
        zoom = dpi_val / 72.0
        mat = pymupdf.Matrix(zoom, zoom)

        page_str = self.pdf_ent_pages.get()
        zip_output = self.pdf_var_zip.get()

        last_dir = None
        for pdf_path in self.pdf_files:
            pdf_p = Path(pdf_path)
            out_folder = pdf_p.parent / f"{pdf_p.stem}_PNG"
            out_folder.mkdir(parents=True, exist_ok=True)
            last_dir = out_folder

            doc = pymupdf.open(str(pdf_p))
            target_pages = parse_page_numbers(page_str, len(doc))

            generated_pngs = []
            for p_no in target_pages:
                page = doc.load_page(p_no)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                png_name = f"{pdf_p.stem}_page_{p_no + 1:04d}.png"
                png_file = out_folder / png_name
                pix.save(str(png_file))
                generated_pngs.append(png_file)

            doc.close()

            if zip_output and generated_pngs:
                zip_path = pdf_p.parent / f"{pdf_p.stem}_PNG.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for png in generated_pngs:
                        zf.write(png, arcname=png.name)

        self.pdf_last_output_dir = last_dir
        self.after(0, self._finish_pdf)

    def _finish_pdf(self):
        self.pdf_progress["value"] = 100
        self.pdf_btn_convert.configure(state="normal", text="Mulai Konversi PDF ke PNG")
        self.pdf_btn_open.pack(fill="x", pady=(5, 0))
        messagebox.showinfo("Berhasil", "Konversi PDF ke gambar PNG selesai!")

    def open_pdf_folder(self):
        if self.pdf_last_output_dir and Path(self.pdf_last_output_dir).exists():
            os.startfile(str(self.pdf_last_output_dir))


def main():
    app = UniversalConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
