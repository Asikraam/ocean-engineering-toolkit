r"""
# Metocean NetCDF to Formatted Excel Converter (Interactive GUI & Visualizer)

A comprehensive oceanographic & meteorological application to extract multi-variable NetCDF reanalysis datasets (ECMWF ERA5 & Copernicus Marine Service) at arbitrary or preset geographic coordinates into professionally styled multi-sheet Microsoft Excel workbooks.

## Features
- **Interactive GUI (Tkinter)**: Intuitive interface to select input folders, customize spatial coordinates, and configure report options.
- **Meteorological & Oceanographic Computations**:
  - Wind velocity ($U_{10}, V_{10}$) converted to wind speed ($m/s$) and meteorological direction ($0^{\circ}-360^{\circ}$).
  - Atmospheric pressure conversion from Pascal ($Pa$) to hectopascal ($hPa$).
  - Wave spectral parameters: Significant Wave Height ($H_s$), Peak Wave Period ($T_p$), and Mean Wave Direction ($MWD$).
- **Professional Excel Styling (OpenPyXL)**:
  - Multi-sheet layout: Statistical Summary, Consolidated Time-Series, Wind Sheet, Wave Sheet.
  - Formatted headers, freeze panes, auto column sizing, alternating zebra striping, and precision number formatting.
- **Integrated 4-Panel Preview**: Matplotlib interactive visualization showing wind speed, wind direction, wave height, and wave period time-series.

## Installation & Requirements
```bash
pip install -r requirements.txt
```
Dependencies:
- `netCDF4 >= 1.6.5`
- `xarray >= 2024.1.0`
- `numpy >= 1.26.0`
- `pandas >= 2.1.0`
- `openpyxl >= 3.1.2`
- `matplotlib >= 3.8.0`

## How to Run
```bash
python MetoceanNcToExcelApp.py
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import sys
import os
import glob
import math
import threading
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# Default Directory Paths (Portable & Cross-Platform)
USER_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
DEFAULT_BASE = os.path.join(os.getcwd(), "data")
DEFAULT_METEO = os.path.join(DEFAULT_BASE, "Meteo_ERA5") if os.path.exists(os.path.join(DEFAULT_BASE, "Meteo_ERA5")) else ""
DEFAULT_WAVE = os.path.join(DEFAULT_BASE, "Wave_Marine") if os.path.exists(os.path.join(DEFAULT_BASE, "Wave_Marine")) else ""
DEFAULT_OUTPUT = os.path.join(USER_DOWNLOADS, "Metocean_Archive_Report.xlsx")

PRESETS = {
    "Masela Site (Tanimbar) [Lat: -8.00, Lon: 131.25]": (-8.00, 131.25),
    "Area Dermaga MOF & Jetty [Lat: -8.00, Lon: 131.24]": (-8.00, 131.24),
    "Offshore Laut Arafura Selatan [Lat: -8.50, Lon: 131.25]": (-8.50, 131.25),
    "Offshore Terbuka Timur [Lat: -8.00, Lon: 132.00]": (-8.00, 132.00),
    "Custom (Masukkan Manual)": (None, None)
}


def proses_konversi(meteo_dir, wave_dir, output_excel, target_lat, target_lon,
                    opt_summary=True, opt_combined=True, opt_wind=True, opt_wave=True,
                    log_callback=print):
    """Fungsi inti pengolahan NetCDF ke Excel."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    log_callback(f"Memulai ekstraksi pada koordinat: Lat {target_lat:.4f}, Lon {target_lon:.4f}")
    
    # --- 1. EKSTRAKSI ANGIN ---
    log_callback("--> [1/4] Membaca data NetCDF Angin (ERA5)...")
    m_files = sorted(glob.glob(os.path.join(meteo_dir, "*.nc")))
    if not m_files:
        raise FileNotFoundError(f"Tidak ada file .nc di folder Angin: {meteo_dir}")

    wind_dfs = []
    for f in m_files:
        ds = xr.open_dataset(f)
        time_var = 'valid_time' if 'valid_time' in ds else 'time'
        pt = ds.sel(latitude=target_lat, longitude=target_lon, method='nearest')
        
        times = pd.to_datetime(pt[time_var].values)
        u10 = pt['u10'].values
        v10 = pt['v10'].values
        msl = pt['msl'].values / 100.0 if 'msl' in pt else np.zeros_like(u10)
        
        wspd = np.sqrt(u10**2 + v10**2)
        wdir = (180.0 + np.degrees(np.arctan2(u10, v10))) % 360.0
        
        df_m = pd.DataFrame({
            'Datetime': times,
            'U10_ms': [round(float(x), 2) for x in u10],
            'V10_ms': [round(float(x), 2) for x in v10],
            'Kecepatan_Angin_ms': [round(float(x), 2) for x in wspd],
            'Arah_Angin_deg': [round(float(x), 1) for x in wdir],
            'Tekanan_Udara_hPa': [round(float(x), 1) for x in msl]
        })
        wind_dfs.append(df_m)
        ds.close()
    df_wind = pd.concat(wind_dfs, ignore_index=True)
    log_callback(f"    Berhasil membaca {len(df_wind):,} rekaman jam data angin.")

    # --- 2. EKSTRAKSI GELOMBANG ---
    log_callback("--> [2/4] Membaca data NetCDF Gelombang (Copernicus Marine)...")
    w_files = sorted(glob.glob(os.path.join(wave_dir, "*.nc")))
    if not w_files:
        raise FileNotFoundError(f"Tidak ada file .nc di folder Gelombang: {wave_dir}")

    wave_dfs = []
    for f in w_files:
        ds = xr.open_dataset(f)
        time_var = 'valid_time' if 'valid_time' in ds else 'time'
        pt = ds.sel(latitude=target_lat, longitude=target_lon, method='nearest')
        
        times = pd.to_datetime(pt[time_var].values)
        swh = pt['swh'].values if 'swh' in pt else pt['VHM0'].values
        pp1d = pt['pp1d'].values if 'pp1d' in pt else pt['VTPK'].values
        mwd = pt['mwd'].values if 'mwd' in pt else pt['VMDR'].values
        
        df_w = pd.DataFrame({
            'Datetime': times,
            'Tinggi_Gelombang_Hs_m': [round(float(x), 2) for x in swh],
            'Periode_Puncak_Tp_s': [round(float(x), 2) for x in pp1d],
            'Arah_Gelombang_deg': [round(float(x), 1) for x in mwd]
        })
        wave_dfs.append(df_w)
        ds.close()
    df_wave = pd.concat(wave_dfs, ignore_index=True)
    log_callback(f"    Berhasil membaca {len(df_wave):,} rekaman jam data gelombang.")

    # --- 3. GABUNGKAN DATA ---
    log_callback("--> [3/4] Menghitung rekapitulasi statistik & sinkronisasi deret waktu...")
    df_all = pd.merge(df_wind, df_wave, on='Datetime', how='inner')
    df_all.insert(1, 'Bulan', df_all['Datetime'].dt.strftime('%B'))
    df_all.insert(2, 'Tanggal', df_all['Datetime'].dt.strftime('%Y-%m-%d'))
    df_all.insert(3, 'Jam', df_all['Datetime'].dt.strftime('%H:00'))

    # Rekap Bulanan
    df_all['Month_Num'] = pd.to_datetime(df_all['Datetime']).dt.month
    monthly_rows = []
    b_names = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
               'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    for mn, mname in enumerate(b_names, 1):
        sub = df_all[df_all['Month_Num'] == mn]
        if len(sub) > 0:
            monthly_rows.append({
                'Bulan': mname,
                'Jumlah_Jam': int(len(sub)),
                'Angin_Rata_ms': round(float(sub['Kecepatan_Angin_ms'].mean()), 2),
                'Angin_Maks_ms': round(float(sub['Kecepatan_Angin_ms'].max()), 2),
                'Arah_Angin_deg': round(float(sub['Arah_Angin_deg'].mean()), 1),
                'Hs_Rata_m': round(float(sub['Tinggi_Gelombang_Hs_m'].mean()), 2),
                'Hs_Maks_m': round(float(sub['Tinggi_Gelombang_Hs_m'].max()), 2),
                'Tp_Rata_s': round(float(sub['Periode_Puncak_Tp_s'].mean()), 2),
                'Arah_Gelombang_deg': round(float(sub['Arah_Gelombang_deg'].mean()), 1),
                'Tekanan_Rata_hPa': round(float(sub['Tekanan_Udara_hPa'].mean()), 1)
            })
    df_summary = pd.DataFrame(monthly_rows)
    df_all.drop(columns=['Month_Num'], inplace=True)

    # Format Datetime
    df_all['Datetime'] = df_all['Datetime'].dt.strftime('%Y-%m-%d %H:%M')
    df_wind['Datetime'] = df_wind['Datetime'].dt.strftime('%Y-%m-%d %H:%M')
    df_wave['Datetime'] = df_wave['Datetime'].dt.strftime('%Y-%m-%d %H:%M')

    # --- 4. EXCEL WRITING DENGAN STYLING ---
    log_callback("--> [4/4] Memformat workbook Excel dengan styling profesional...")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Hapus default

    NAVY_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    TEAL_FILL = PatternFill(start_color="1B7575", end_color="1B7575", fill_type="solid")
    BLUE_FILL = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    ZEBRA_FILL = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")

    FONT_HDR = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    FONT_TITLE = Font(name="Calibri", size=13, bold=True, color="1F4E78")
    FONT_CELL = Font(name="Calibri", size=10)

    BORDER_CELL = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    def write_sheet(ws, title, fill, df):
        ws.views.sheetView[0].showGridLines = True
        ws.merge_cells("A1:H1")
        ws["A1"] = title
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[1].height = 28

        for c_idx, h in enumerate(df.columns, 1):
            c = ws.cell(row=3, column=c_idx, value=h.replace('_', ' '))
            c.font = FONT_HDR
            c.fill = fill
            c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 24

        for r_idx, r_data in enumerate(df.values, 4):
            even = (r_idx % 2 == 0)
            for c_idx, val in enumerate(r_data, 1):
                c = ws.cell(row=r_idx, column=c_idx, value=val)
                c.font = FONT_CELL
                c.border = BORDER_CELL
                if isinstance(val, (int, np.integer)):
                    c.alignment = Alignment(horizontal="right")
                    c.number_format = "#,##0"
                elif isinstance(val, (float, np.floating)):
                    c.alignment = Alignment(horizontal="right")
                    c.number_format = "#,##0.00"
                elif isinstance(val, str) and (":" in val or "-" in val):
                    c.alignment = Alignment(horizontal="center")
                if even:
                    c.fill = ZEBRA_FILL
            ws.row_dimensions[r_idx].height = 18

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max([len(str(cell.value or '')) for cell in col if cell.row >= 3] or [10])
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        ws.freeze_panes = "A4"

    if opt_summary:
        ws1 = wb.create_sheet(title="Rekap_Statistik_Bulanan")
        write_sheet(ws1, f"RINGKASAN METOCEAN 2020 (LAT: {target_lat}, LON: {target_lon})", NAVY_FILL, df_summary)

    if opt_combined:
        ws2 = wb.create_sheet(title="Data_Gabungan_2020")
        write_sheet(ws2, "DERET WAKTU LENGKAP ANGIN & GELOMBANG 2020 (8.784 JAM)", NAVY_FILL, df_all)

    if opt_wind:
        ws3 = wb.create_sheet(title="Data_Angin_ERA5")
        write_sheet(ws3, "DERET WAKTU ANGIN ERA5 (U10, V10, SPEED, DIR, MSL)", TEAL_FILL, df_wind)

    if opt_wave:
        ws4 = wb.create_sheet(title="Data_Gelombang_Marine")
        write_sheet(ws4, "DERET WAKTU GELOMBANG COPERNICUS (Hs, Tp, MWD)", BLUE_FILL, df_wave)

    wb.save(output_excel)
    log_callback(f"--> SUKSES! File Excel tersimpan: {output_excel}")
    return df_all


def tampilkan_grafik_interaktif(df_all, target_lat, target_lon):
    """Menampilkan jendela grafik interaktif 4-Panel menggunakan Matplotlib."""
    times = pd.to_datetime(df_all['Datetime'])
    wspd = df_all['Kecepatan_Angin_ms']
    wdir = df_all['Arah_Angin_deg']
    hs = df_all['Tinggi_Gelombang_Hs_m']
    tp = df_all['Periode_Puncak_Tp_s']

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.canvas.manager.set_window_title(f"Preview Visual Metocean Masela 2020 (Lat {target_lat}, Lon {target_lon})")

    # Panel 1: Wind Speed
    axes[0, 0].plot(times, wspd, color='#1F77B4', lw=0.8, alpha=0.9)
    axes[0, 0].set_title("Deret Waktu Kecepatan Angin (m/s) - ERA5 2020", fontweight='bold', color='#1F4E78')
    axes[0, 0].set_ylabel("Kecepatan Angin [m/s]")
    axes[0, 0].grid(True, linestyle='--', alpha=0.6)

    # Panel 2: Wind Direction
    axes[0, 1].scatter(times, wdir, color='#FF7F0E', s=3, alpha=0.5)
    axes[0, 1].set_title("Arah Datang Angin (°) - Meteorological Convention", fontweight='bold', color='#1F4E78')
    axes[0, 1].set_ylabel("Arah [Derajat]")
    axes[0, 1].set_ylim(0, 360)
    axes[0, 1].grid(True, linestyle='--', alpha=0.6)

    # Panel 3: Significant Wave Height (Hs)
    axes[1, 0].plot(times, hs, color='#2CA02C', lw=0.8, alpha=0.9)
    axes[1, 0].set_title("Deret Waktu Tinggi Gelombang Signifikan Hs (m) - Copernicus Marine", fontweight='bold', color='#1F4E78')
    axes[1, 0].set_ylabel("Hs [m]")
    axes[1, 0].grid(True, linestyle='--', alpha=0.6)

    # Panel 4: Wave Period (Tp) vs Hs Scatter
    sc = axes[1, 1].scatter(tp, hs, c=wspd, cmap='viridis', s=6, alpha=0.6)
    cbar = plt.colorbar(sc, ax=axes[1, 1])
    cbar.set_label("Kecepatan Angin [m/s]")
    axes[1, 1].set_title("Korelasi Periode Gelombang (Tp) vs Hs", fontweight='bold', color='#1F4E78')
    axes[1, 1].set_xlabel("Periode Puncak Tp [s]")
    axes[1, 1].set_ylabel("Tinggi Gelombang Hs [m]")
    axes[1, 1].grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()


# ==============================================================================
# GUI DESKTOP TKINTER INTERAKTIF
# ==============================================================================
def jalankan_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("Konverter & Pengarsip NetCDF Metocean ke Excel (Masela)")
    root.geometry("780x680")
    root.minsize(720, 600)

    # Styling
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TLabel", font=("Segoe UI", 9))
    style.configure("TButton", font=("Segoe UI", 9, "bold"))
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1F4E78")
    style.configure("SubHeader.TLabel", font=("Segoe UI", 9, "bold"), foreground="#333333")

    # Header Banner
    header_frame = tk.Frame(root, bg="#1F4E78", height=60)
    header_frame.pack(fill="x", side="top")
    lbl_title = tk.Label(header_frame, text="ARSIP NETCDF METOCEAN (ANGIN & GELOMBANG) KE EXCEL", 
                         bg="#1F4E78", fg="white", font=("Segoe UI", 12, "bold"))
    lbl_title.pack(pady=8)
    lbl_sub = tk.Label(header_frame, text="Otomasi Ekstraksi Multi-File NetCDF 1 Tahun ke Format Excel Profesional", 
                        bg="#1F4E78", fg="#D9E1F2", font=("Segoe UI", 9))
    lbl_sub.pack()

    # Main Scrollable / Padded Container
    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill="both", expand=True)

    # 1. Groupbox Path Folder Input / Output
    lf_path = ttk.LabelFrame(main_frame, text=" 📁 Lokasi Folder Data & Output Excel ", padding="10")
    lf_path.pack(fill="x", pady=5)

    # Meteo Folder
    ttk.Label(lf_path, text="Folder NetCDF Angin (ERA5):").grid(row=0, column=0, sticky="w", pady=3)
    entry_meteo = ttk.Entry(lf_path, width=60)
    entry_meteo.grid(row=0, column=1, padx=5, pady=3, sticky="we")
    entry_meteo.insert(0, DEFAULT_METEO)
    btn_m = ttk.Button(lf_path, text="Pilih Folder...", command=lambda: browse_dir(entry_meteo))
    btn_m.grid(row=0, column=2, padx=2, pady=3)

    # Wave Folder
    ttk.Label(lf_path, text="Folder NetCDF Gelombang (Copernicus):").grid(row=1, column=0, sticky="w", pady=3)
    entry_wave = ttk.Entry(lf_path, width=60)
    entry_wave.grid(row=1, column=1, padx=5, pady=3, sticky="we")
    entry_wave.insert(0, DEFAULT_WAVE)
    btn_w = ttk.Button(lf_path, text="Pilih Folder...", command=lambda: browse_dir(entry_wave))
    btn_w.grid(row=1, column=2, padx=2, pady=3)

    # Output Excel
    ttk.Label(lf_path, text="File Excel Hasil Output:").grid(row=2, column=0, sticky="w", pady=3)
    entry_out = ttk.Entry(lf_path, width=60)
    entry_out.grid(row=2, column=1, padx=5, pady=3, sticky="we")
    entry_out.insert(0, DEFAULT_OUTPUT)
    btn_o = ttk.Button(lf_path, text="Simpan Ke...", command=lambda: browse_save_file(entry_out))
    btn_o.grid(row=2, column=2, padx=2, pady=3)
    lf_path.columnconfigure(1, weight=1)

    # 2. Groupbox Koordinat Ekstraksi
    lf_coord = ttk.LabelFrame(main_frame, text=" 📍 Titik Koordinat Ekstraksi ", padding="10")
    lf_coord.pack(fill="x", pady=5)

    ttk.Label(lf_coord, text="Pilih Preset Lokasi:").grid(row=0, column=0, sticky="w", pady=3)
    combo_preset = ttk.Combobox(lf_coord, values=list(PRESETS.keys()), state="readonly", width=45)
    combo_preset.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=3)
    combo_preset.current(0)

    ttk.Label(lf_coord, text="Latitude (Lintang):").grid(row=1, column=0, sticky="w", pady=3)
    entry_lat = ttk.Entry(lf_coord, width=15)
    entry_lat.grid(row=1, column=1, sticky="w", padx=5, pady=3)
    entry_lat.insert(0, "-8.00")

    ttk.Label(lf_coord, text="Longitude (Bujur):").grid(row=1, column=2, sticky="w", pady=3)
    entry_lon = ttk.Entry(lf_coord, width=15)
    entry_lon.grid(row=1, column=3, sticky="w", padx=5, pady=3)
    entry_lon.insert(0, "131.25")

    def on_preset_change(event):
        sel = combo_preset.get()
        coords = PRESETS.get(sel, (None, None))
        if coords[0] is not None:
            entry_lat.delete(0, tk.END)
            entry_lat.insert(0, str(coords[0]))
            entry_lon.delete(0, tk.END)
            entry_lon.insert(0, str(coords[1]))
    combo_preset.bind("<<ComboboxSelected>>", on_preset_change)

    # 3. Opsi Sheet Excel
    lf_opts = ttk.LabelFrame(main_frame, text=" ⚙️ Opsi Lembar Kerja (Sheets) ", padding="8")
    lf_opts.pack(fill="x", pady=5)

    var_sum = tk.BooleanVar(value=True)
    var_all = tk.BooleanVar(value=True)
    var_wnd = tk.BooleanVar(value=True)
    var_wav = tk.BooleanVar(value=True)
    var_plot = tk.BooleanVar(value=True)

    ttk.Checkbutton(lf_opts, text="Sheet Rekapitulasi Statistik Bulanan", variable=var_sum).grid(row=0, column=0, padx=8, sticky="w")
    ttk.Checkbutton(lf_opts, text="Sheet Data Gabungan Jam-jaman", variable=var_all).grid(row=0, column=1, padx=8, sticky="w")
    ttk.Checkbutton(lf_opts, text="Sheet Data Angin ERA5", variable=var_wnd).grid(row=1, column=0, padx=8, sticky="w")
    ttk.Checkbutton(lf_opts, text="Sheet Data Gelombang", variable=var_wav).grid(row=1, column=1, padx=8, sticky="w")
    ttk.Checkbutton(lf_opts, text="Tampilkan Jendela Grafik Interaktif Setelah Selesai", variable=var_plot).grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky="w")

    # 4. Kotak Log Aktivitas
    lf_log = ttk.LabelFrame(main_frame, text=" 📝 Log Aktivitas & Status ", padding="6")
    lf_log.pack(fill="both", expand=True, pady=5)

    text_log = tk.Text(lf_log, height=8, wrap="word", font=("Consolas", 8), bg="#F8F9FA")
    text_log.pack(fill="both", expand=True)

    def log_msg(msg):
        text_log.insert(tk.END, msg + "\n")
        text_log.see(tk.END)
        root.update_idletasks()

    # 5. Tombol Aksi
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=8)

    cached_df = {"df": None, "lat": None, "lon": None}

    def browse_dir(entry):
        d = filedialog.askdirectory()
        if d:
            entry.delete(0, tk.END)
            entry.insert(0, d)

    def browse_save_file(entry):
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if f:
            entry.delete(0, tk.END)
            entry.insert(0, f)

    def open_excel():
        out_p = entry_out.get().strip()
        if os.path.exists(out_p):
            try:
                os.startfile(out_p)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka file:\n{e}")
        else:
            messagebox.showwarning("Peringatan", "File Excel belum dibuat! Jalankan konversi terlebih dahulu.")

    def show_preview():
        if cached_df["df"] is not None:
            tampilkan_grafik_interaktif(cached_df["df"], cached_df["lat"], cached_df["lon"])
        else:
            messagebox.showinfo("Info", "Lakukan proses ekspor terlebih dahulu agar data siap divisualisasikan.")

    def run_all_stations_thread():
        text_log.delete("1.0", tk.END)
        log_msg("=== MEMULAI EKSTRAKSI SELURUH TITIK GRID METOCEAN (DIPECAH PER BULAN) ===")
        log_msg("Memanggil modul split_and_export_nc_metocean_all_stations...")
        
        def task_all():
            btn_run.config(state="disabled")
            btn_all_grid.config(state="disabled")
            try:
                import split_and_export_nc_metocean_all_stations as splitter
                log_msg("1. Memproses 529 Grid Angin ERA5 per bulan...")
                cat_w = splitter.process_all_wind_monthly()
                log_msg("2. Memproses 144 Grid Gelombang Copernicus per bulan...")
                cat_wv = splitter.process_all_wave_monthly()
                log_msg("3. Menulis Master Katalog Koordinat Grid...")
                splitter.generate_master_catalog_file(cat_w, cat_wv)
                log_msg("=== SELESAI! Seluruh 25 file Excel berhasil disimpan ===")
                messagebox.showinfo("Sukses!", f"Berhasil mengekstrak seluruh titik!\nFolder: {splitter.OUTPUT_MASTER_DIR}")
            except Exception as e:
                log_msg(f"[ERROR]: {e}")
                messagebox.showerror("Error", f"Gagal mengekstrak seluruh titik:\n{e}")
            finally:
                btn_run.config(state="normal")
                btn_all_grid.config(state="normal")
                
        threading.Thread(target=task_all, daemon=True).start()

    def run_process_thread():
        btn_run.config(state="disabled")
        text_log.delete("1.0", tk.END)
        
        m_dir = entry_meteo.get().strip()
        w_dir = entry_wave.get().strip()
        out_p = entry_out.get().strip()

        try:
            lat = float(entry_lat.get().strip())
            lon = float(entry_lon.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Nilai Latitude dan Longitude harus berupa angka desimal!")
            btn_run.config(state="normal")
            return

        def task():
            try:
                df_res = proses_konversi(
                    meteo_dir=m_dir,
                    wave_dir=w_dir,
                    output_excel=out_p,
                    target_lat=lat,
                    target_lon=lon,
                    opt_summary=var_sum.get(),
                    opt_combined=var_all.get(),
                    opt_wind=var_wnd.get(),
                    opt_wave=var_wav.get(),
                    log_callback=log_msg
                )
                cached_df["df"] = df_res
                cached_df["lat"] = lat
                cached_df["lon"] = lon
                btn_open.config(state="normal")
                btn_plot.config(state="normal")
                messagebox.showinfo("Sukses!", f"Arsip data Metocean 2020 berhasil dibuat di:\n{out_p}")
                if var_plot.get():
                    tampilkan_grafik_interaktif(df_res, lat, lon)
            except Exception as e:
                log_msg(f"[ERROR]: {e}")
                messagebox.showerror("Terjadi Kesalahan", f"Gagal memproses data:\n{e}")
            finally:
                btn_run.config(state="normal")

        threading.Thread(target=task, daemon=True).start()

    btn_run = tk.Button(btn_frame, text="🚀 EKSPOR STASIUN TERPILIH", bg="#1F4E78", fg="white", 
                        font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=run_process_thread)
    btn_run.pack(side="left", padx=3)

    btn_all_grid = tk.Button(btn_frame, text="⚡ EKSPOR SEMUA TITIK (PECAH PER BULAN)", bg="#8E44AD", fg="white", 
                             font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=run_all_stations_thread)
    btn_all_grid.pack(side="left", padx=3)

    btn_open = tk.Button(btn_frame, text="📊 Buka Excel", bg="#2CA02C", fg="white", 
                         font=("Segoe UI", 9, "bold"), padx=8, pady=6, command=open_excel)
    btn_open.pack(side="left", padx=3)

    btn_open_folder = tk.Button(btn_frame, text="📁 Buka Folder Semua Titik", bg="#34495E", fg="white", 
                                font=("Segoe UI", 9, "bold"), padx=8, pady=6, 
                                command=lambda: os.startfile(r"C:\Users\Windows\Downloads\Arsip_Metocean_Lengkap_Semua_Titik_Masela_2020"))
    btn_open_folder.pack(side="left", padx=3)

    btn_plot = tk.Button(btn_frame, text="📈 Grafik", bg="#E67E22", fg="white", 
                         font=("Segoe UI", 9, "bold"), padx=8, pady=6, command=show_preview)
    btn_plot.pack(side="left", padx=3)

    log_msg("Aplikasi siap. Klik 'EKSPOR SEMUA TITIK (PECAH PER BULAN)' untuk mengekstrak seluruh 529 grid angin & 144 gelombang.")
    root.mainloop()


if __name__ == "__main__":
    jalankan_gui()
