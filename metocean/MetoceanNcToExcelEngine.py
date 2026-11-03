"""
# Metocean NetCDF to Formatted Excel Engine (CLI & Headless Pipeline)

Core headless Python module for extracting, processing, and generating formatted multi-sheet Excel reports from ECMWF ERA5 and Copernicus Marine NetCDF files.

## Features
- **Headless Pipeline**: Suitable for automated scheduled tasks, batch jobs, and server environments.
- **NetCDF Parsing**: Automatically scans and concatenates temporal series from NetCDF files.
- **Geographic Nearest-Neighbor Interpolation**: Extracts data points closest to user-defined coordinates.
- **Multi-Sheet Report Generation**: Builds summary statistics, wind time-series, wave time-series, and unified datasets.

## Usage (CLI)
```bash
python MetoceanNcToExcelEngine.py --meteo-dir ./data/Meteo_ERA5 --wave-dir ./data/Wave_Marine --lat -8.00 --lon 131.25 --output Metocean_Report.xlsx
```

## Requirements
```bash
pip install -r requirements.txt
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import glob
import math
import numpy as np
import pandas as pd
import xarray as xr
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def extract_wind_data(meteo_dir, target_lat, target_lon):
    """Extract ERA5 wind data from NetCDF files."""
    meteo_files = sorted(glob.glob(os.path.join(meteo_dir, "*.nc")))
    if not meteo_files:
        raise FileNotFoundError(f"File angin tidak ditemukan di {meteo_dir}")

    dfs = []
    for f in meteo_files:
        ds = xr.open_dataset(f)
        time_var = "valid_time" if "valid_time" in ds else "time"
        pt = ds.sel(latitude=target_lat, longitude=target_lon, method="nearest")

        times = pd.to_datetime(pt[time_var].values)
        u10 = pt["u10"].values
        v10 = pt["v10"].values
        msl = pt["msl"].values / 100.0  # Pa to hPa

        wind_speed = np.sqrt(u10**2 + v10**2)
        wind_dir = (270.0 - np.arctan2(v10, u10) * (180.0 / np.pi)) % 360.0

        df_temp = pd.DataFrame({
            "Datetime": times,
            "U10_ms": u10,
            "V10_ms": v10,
            "Wind_Speed_ms": wind_speed,
            "Wind_Dir_deg": wind_dir,
            "MSL_Pressure_hPa": msl
        })
        dfs.append(df_temp)
        ds.close()

    df_wind = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["Datetime"]).sort_values("Datetime")
    return df_wind


def extract_wave_data(wave_dir, target_lat, target_lon):
    """Extract Copernicus Marine wave data from NetCDF files."""
    wave_files = sorted(glob.glob(os.path.join(wave_dir, "*.nc")))
    if not wave_files:
        raise FileNotFoundError(f"File gelombang tidak ditemukan di {wave_dir}")

    dfs = []
    for f in wave_files:
        ds = xr.open_dataset(f)
        time_var = "time" if "time" in ds else "valid_time"
        pt = ds.sel(latitude=target_lat, longitude=target_lon, method="nearest")

        times = pd.to_datetime(pt[time_var].values)

        def get_var(names):
            for name in names:
                if name in pt:
                    return pt[name].values
            return np.full(len(times), np.nan)

        hs = get_var(["VHM0", "hs", "swh"])
        tp = get_var(["VTPK", "tp", "pp1d"])
        mwd = get_var(["VMDR", "mwd", "mdir"])

        df_temp = pd.DataFrame({
            "Datetime": times,
            "Hs_WaveHeight_m": hs,
            "Tp_PeakPeriod_s": tp,
            "Mean_Wave_Dir_deg": mwd
        })
        dfs.append(df_temp)
        ds.close()

    df_wave = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["Datetime"]).sort_values("Datetime")
    return df_wave


def export_netcdf_to_excel(meteo_dir, wave_dir, output_excel, target_lat=-8.00, target_lon=131.25, log_callback=print):
    """
    Main orchestration function to export Metocean NetCDF to styled Excel.
    """
    log_callback("=" * 75)
    log_callback("MEMULAI PROSES EKSTRAKSI DATA NETCDF (ANGIN & GELOMBANG) KE EXCEL")
    log_callback(f"Target Lokasi: Lat {target_lat} S, Lon {target_lon} E")
    log_callback("=" * 75)

    log_callback("[1/4] Membaca dan mengekstrak data NetCDF Angin (ERA5)...")
    df_wind = extract_wind_data(meteo_dir, target_lat, target_lon)

    log_callback("[2/4] Membaca dan mengekstrak data NetCDF Gelombang (Copernicus Marine)...")
    df_wave = extract_wave_data(wave_dir, target_lat, target_lon)

    log_callback("[3/4] Melakukan sinkronisasi waktu dan komputasi statistik bulanan...")
    df_all = pd.merge(df_wind, df_wave, on="Datetime", how="inner")

    df_all["Tahun"] = df_all["Datetime"].dt.year
    df_all["Bulan_Num"] = df_all["Datetime"].dt.month
    month_names = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni",
                   7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    df_all["Bulan"] = df_all["Bulan_Num"].map(month_names)

    summary_rows = []
    for m in range(1, 13):
        sub = df_all[df_all["Bulan_Num"] == m]
        if len(sub) == 0:
            continue
        summary_rows.append({
            "Bulan": month_names[m],
            "Jumlah_Data_Jam": len(sub),
            "Kecepatan_Angin_Max_ms": sub["Wind_Speed_ms"].max(),
            "Kecepatan_Angin_Avg_ms": sub["Wind_Speed_ms"].mean(),
            "Hs_Gelombang_Max_m": sub["Hs_WaveHeight_m"].max(),
            "Hs_Gelombang_Avg_m": sub["Hs_WaveHeight_m"].mean(),
            "Tp_Periode_Puncak_Max_s": sub["Tp_PeakPeriod_s"].max(),
            "Tekanan_Udara_Min_hPa": sub["MSL_Pressure_hPa"].min(),
            "Tekanan_Udara_Avg_hPa": sub["MSL_Pressure_hPa"].mean()
        })

    summary_rows.append({
        "Bulan": "TAHUNAN (TOTAL/AVG)",
        "Jumlah_Data_Jam": len(df_all),
        "Kecepatan_Angin_Max_ms": df_all["Wind_Speed_ms"].max(),
        "Kecepatan_Angin_Avg_ms": df_all["Wind_Speed_ms"].mean(),
        "Hs_Gelombang_Max_m": df_all["Hs_WaveHeight_m"].max(),
        "Hs_Gelombang_Avg_m": df_all["Hs_WaveHeight_m"].mean(),
        "Tp_Periode_Puncak_Max_s": df_all["Tp_PeakPeriod_s"].max(),
        "Tekanan_Udara_Min_hPa": df_all["MSL_Pressure_hPa"].min(),
        "Tekanan_Udara_Avg_hPa": df_all["MSL_Pressure_hPa"].mean()
    })
    df_summary = pd.DataFrame(summary_rows)

    df_wind["Datetime"] = df_wind["Datetime"].dt.strftime("%Y-%m-%d %H:%M")
    df_wave["Datetime"] = df_wave["Datetime"].dt.strftime("%Y-%m-%d %H:%M")
    df_all["Datetime"] = df_all["Datetime"].dt.strftime("%Y-%m-%d %H:%M")
    df_all = df_all.drop(columns=["Tahun", "Bulan_Num", "Bulan"])

    log_callback(f"[4/4] Membangun workbook Excel profesional: {output_excel}...")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="1B365D")
    FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    FONT_DATA = Font(name="Calibri", size=10, bold=False, color="000000")
    FONT_TOTAL = Font(name="Calibri", size=10, bold=True, color="000000")

    HEADER_FILL_NAVY = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    HEADER_FILL_TEAL = PatternFill(start_color="005F73", end_color="005F73", fill_type="solid")
    HEADER_FILL_BLUE = PatternFill(start_color="0A9396", end_color="0A9396", fill_type="solid")
    ZEBRA_FILL = PatternFill(start_color="F4F6F9", end_color="F4F6F9", fill_type="solid")
    TOTAL_FILL = PatternFill(start_color="D9E2EC", end_color="D9E2EC", fill_type="solid")

    BORDER_THIN = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB")
    )
    BORDER_DOUBLE_BOTTOM = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="double", color="1B365D")
    )

    ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
    ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

    def style_sheet(ws, title, header_fill, df):
        ws.views.sheetView[0].showGridLines = True
        ws.cell(row=1, column=1, value=title).font = FONT_TITLE
        ws.row_dimensions[1].height = 30

        columns = list(df.columns)
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=3, column=col_idx, value=col_name.replace("_", " "))
            cell.font = FONT_HEADER
            cell.fill = header_fill
            cell.alignment = ALIGN_CENTER
            cell.border = BORDER_THIN
        ws.row_dimensions[3].height = 28

        for row_idx, row_data in enumerate(df.values, 4):
            is_even = (row_idx % 2 == 0)
            is_total_row = ("TOTAL" in str(row_data[0]) or "TAHUNAN" in str(row_data[0]))
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = FONT_TOTAL if is_total_row else FONT_DATA
                cell.border = BORDER_DOUBLE_BOTTOM if is_total_row else BORDER_THIN
                if is_total_row:
                    cell.fill = TOTAL_FILL
                elif is_even:
                    cell.fill = ZEBRA_FILL

                if isinstance(val, (int, np.integer)):
                    cell.alignment = ALIGN_RIGHT
                    cell.number_format = "#,##0"
                elif isinstance(val, (float, np.floating)):
                    cell.alignment = ALIGN_RIGHT
                    cell.number_format = "#,##0.00"
                elif isinstance(val, str) and (":" in val or "-" in val):
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT
            ws.row_dimensions[row_idx].height = 18

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row >= 3:
                    val_str = str(cell.value or "")
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        ws.freeze_panes = "A4"

    ws_sum = wb.create_sheet(title="Rekap_Statistik_Bulanan")
    style_sheet(ws_sum, f"RINGKASAN METOCEAN TAHUNAN - LAT {target_lat}, LON {target_lon}", HEADER_FILL_NAVY, df_summary)

    ws_all = wb.create_sheet(title="Data_Gabungan")
    style_sheet(ws_all, f"DERET WAKTU LENGKAP ANGIN & GELOMBANG ({len(df_all):,} DATA)", HEADER_FILL_NAVY, df_all)

    ws_wind = wb.create_sheet(title="Data_Angin_ERA5")
    style_sheet(ws_wind, "DATA PARAMETER ANGIN ERA5 (U10, V10, SPEED, DIR, MSL)", HEADER_FILL_TEAL, df_wind)

    ws_wave = wb.create_sheet(title="Data_Gelombang_Marine")
    style_sheet(ws_wave, "DATA PARAMETER GELOMBANG SPEKTRAL (Hs, Tp, MWD)", HEADER_FILL_BLUE, df_wave)

    os.makedirs(os.path.dirname(os.path.abspath(output_excel)), exist_ok=True)
    wb.save(output_excel)
    log_callback(f"BERHASIL! File Excel rapi tersimpan di: {output_excel}")
    return output_excel


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Metocean NetCDF to Excel Engine")
    parser.add_argument("--meteo-dir", required=True, help="Path folder NetCDF Angin (ERA5)")
    parser.add_argument("--wave-dir", required=True, help="Path folder NetCDF Gelombang (Copernicus)")
    parser.add_argument("--output", default="Metocean_Report.xlsx", help="Path output file Excel (.xlsx)")
    parser.add_argument("--lat", type=float, default=-8.00, help="Target Latitude (default: -8.00)")
    parser.add_argument("--lon", type=float, default=131.25, help="Target Longitude (default: 131.25)")

    args = parser.parse_args()
    export_netcdf_to_excel(
        meteo_dir=args.meteo_dir,
        wave_dir=args.wave_dir,
        output_excel=args.output,
        target_lat=args.lat,
        target_lon=args.lon
    )


if __name__ == "__main__":
    main()
