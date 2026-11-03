r"""
# DHI MIKE 21 Wind Forcing Grid Generator (NetCDF to DFS2)

Universal generator for constructing 2D dynamic wind and atmospheric pressure forcing grids (`.dfs2`) from ECMWF ERA5 NetCDF reanalysis data for **MIKE 21 HD** (Hydrodynamic) and **MIKE 21 SW** (Spectral Wave) simulations.

## Key Engineering Capabilities
- **Temporal Concatenation**:
  - Automatically merges multi-month or annual NetCDF files (e.g. 8,784 hourly timesteps) into a continuous sequence.
- **Coordinate System Flexibility**:
  - **Geographic (Long/Lat - WGS 84)**: Official DHI recommendation where MIKE dynamically reprojects onto UTM meshes at runtime.
  - **Projected (UTM Meter)**: Features *Auto-Detect UTM Zone* or allows manual global UTM selection (e.g. UTM 48S to 54S, UTM 46N to 52N).
- **Physical Parameters**:
  - Calculates $10	ext{ m}$ $U$-velocity ($m/s$), $V$-velocity ($m/s$), and Mean Sea Level Pressure ($hPa$).

## Installation & Requirements
```bash
pip install -r requirements.txt
```
Dependencies: `mikeio >= 1.5.0`, `netCDF4 >= 1.6.5`, `numpy >= 1.26.0`, `pyproj >= 3.6.0`

## How to Run
```bash
python hydro/MikeConvertWindDfs2App.py
```
Or via main toolkit CLI:
```bash
python cli.py mike-wind-dfs2
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import sys
import os
import glob
import math
import numpy as np
import pandas as pd
import xarray as xr
import pyproj
from scipy.interpolate import RegularGridInterpolator
import mikeio
from mikeio.eum import EUMType, ItemInfo, EUMUnit


def tentukan_utm_epsg(lon, lat, custom_zone=None):
    """
    Menghitung zona UTM dan kode EPSG secara otomatis dari koordinat atau custom zone.
    custom_zone bisa berupa 'AUTO', '52S', '48S', '50N', '32752', 'EPSG:32752', dll.
    """
    if custom_zone and str(custom_zone).strip().upper() not in ["AUTO", "NONE", ""]:
        cz = str(custom_zone).strip().upper().replace("UTM", "").replace("-", "").replace(" ", "")
        if cz.startswith("EPSG:"):
            return cz
        if cz.isdigit() and len(cz) == 5:
            return f"EPSG:{cz}"
        if len(cz) >= 2 and cz[-1] in ['N', 'S']:
            num = int(cz[:-1])
            hemi = cz[-1]
            epsg = 32700 + num if hemi == 'S' else 32600 + num
            return f"EPSG:{epsg}"

    # Auto-detect dari koordinat pusat
    zone_num = int(math.floor((lon + 180.0) / 6.0)) + 1
    hemi = 'S' if lat < 0 else 'N'
    epsg = 32700 + zone_num if hemi == 'S' else 32600 + zone_num
    return f"EPSG:{epsg}"


def proses_wind_nc_to_dfs2(wind_folder_or_file, output_dfs2_file=None, target_proj="LONG/LAT", utm_zone="AUTO"):
    """
    Eksekusi konversi NetCDF angin ERA5 menjadi DFS2 Grid2D MIKE.
    target_proj: 'LONG/LAT' atau 'UTM'
    utm_zone: 'AUTO' atau nama zona (misal '48S', '50S', '52S', '46N')
    """
    if os.path.isdir(wind_folder_or_file):
        nc_files = sorted(glob.glob(os.path.join(wind_folder_or_file, "*.nc")))
        if not nc_files:
            raise FileNotFoundError(f"Tidak ada file .nc di folder: {wind_folder_or_file}")
    elif os.path.isfile(wind_folder_or_file):
        nc_files = [wind_folder_or_file]
    else:
        raise FileNotFoundError(f"Path Wind tidak ditemukan: {wind_folder_or_file}")

    print(f"[INFO] Membaca {len(nc_files)} file NetCDF Wind/Meteo...")
    ds = xr.open_mfdataset(nc_files, combine='by_coords')

    # Deteksi koordinat
    lon_col = 'longitude' if 'longitude' in ds.coords else 'lon'
    lat_col = 'latitude' if 'latitude' in ds.coords else 'lat'
    time_col = 'valid_time' if 'valid_time' in ds.coords else 'time'

    # Deteksi variabel
    u_var = None
    for cand in ['u10', '10m_u_component_of_wind', 'u']:
        if cand in ds.data_vars:
            u_var = cand
            break

    v_var = None
    for cand in ['v10', '10m_v_component_of_wind', 'v']:
        if cand in ds.data_vars:
            v_var = cand
            break

    p_var = None
    for cand in ['msl', 'mean_sea_level_pressure', 'sp', 'pressure']:
        if cand in ds.data_vars:
            p_var = cand
            break

    if not u_var or not v_var or not p_var:
        raise ValueError(f"Variabel angin tidak lengkap di NetCDF. Ditemukan: {list(ds.data_vars.keys())}")

    print(f"[INFO] Variabel terdeteksi: U='{u_var}', V='{v_var}', P='{p_var}'")

    # Pastikan Latitude terurut menaik (dari Selatan ke Utara)
    if ds[lat_col].values[0] > ds[lat_col].values[-1]:
        ds = ds.sortby(lat_col, ascending=True)

    if ds[lon_col].values[0] > ds[lon_col].values[-1]:
        ds = ds.sortby(lon_col, ascending=True)

    lat_vals = ds[lat_col].values
    lon_vals = ds[lon_col].values
    time_vals = ds[time_col].values
    time_steps = pd.DatetimeIndex(time_vals)
    n_timesteps = len(time_steps)

    center_lon = float(np.mean(lon_vals))
    center_lat = float(np.mean(lat_vals))

    if target_proj.upper() == "UTM":
        actual_epsg = tentukan_utm_epsg(center_lon, center_lat, utm_zone)
        crs = pyproj.CRS(actual_epsg)
        print(f"[INFO] Menggunakan Sistem Proyeksi: {crs.name} ({actual_epsg})")

        if output_dfs2_file is None:
            folder_parent = os.path.dirname(nc_files[0])
            zone_clean = crs.name.replace(" ", "_").replace("/", "_")
            output_dfs2_file = os.path.join(folder_parent, f"Wind_Forcing_{zone_clean}.dfs2")

        t_to_ll = pyproj.Transformer.from_crs(actual_epsg, 'EPSG:4326', always_xy=True)
        t_to_utm = pyproj.Transformer.from_crs('EPSG:4326', actual_epsg, always_xy=True)

        # Hitung bounding box UTM
        x_min, y_min = t_to_utm.transform(lon_vals.min(), lat_vals.min())
        x_max, y_max = t_to_utm.transform(lon_vals.max(), lat_vals.max())

        # Resolusi grid ~25 km (25.000 meter)
        dx, dy = 25000.0, 25000.0
        nx = int(np.ceil((x_max - x_min) / dx)) + 1
        ny = int(np.ceil((y_max - y_min) / dy)) + 1
        origin_x, origin_y = float(x_min), float(y_min)

        print(f"[INFO] Geometri UTM Grid2D: ny={ny}, nx={nx}, dx={dx:.0f}m, dy={dy:.0f}m")
        print(f"[INFO] Origin UTM: ({origin_x:.1f}, {origin_y:.1f}) | Timestep: {n_timesteps}")

        # Format ASCII WKT1_GDAL yang kompatibel dengan DLL MIKE
        proj_utm_str = crs.to_wkt(version="WKT1_GDAL")

        geometry = mikeio.Grid2D(
            dx=dx,
            dy=dy,
            nx=nx,
            ny=ny,
            origin=(origin_x, origin_y),
            projection=proj_utm_str
        )

        utm_x = origin_x + np.arange(nx) * dx
        utm_y = origin_y + np.arange(ny) * dy
        gx, gy = np.meshgrid(utm_x, utm_y)
        glon, glat = t_to_ll.transform(gx, gy)
        pts = np.column_stack([glat.ravel(), glon.ravel()])

        raw_u = ds[u_var].values
        raw_v = ds[v_var].values
        raw_p = ds[p_var].values

        u_vals = np.zeros((n_timesteps, ny, nx), dtype=np.float32)
        v_vals = np.zeros((n_timesteps, ny, nx), dtype=np.float32)
        p_vals = np.zeros((n_timesteps, ny, nx), dtype=np.float32)

        print("[INFO] Melakukan interpolasi spasial ke grid UTM...")
        for t in range(n_timesteps):
            rgi_u = RegularGridInterpolator((lat_vals, lon_vals), raw_u[t], bounds_error=False, fill_value=0.0)
            rgi_v = RegularGridInterpolator((lat_vals, lon_vals), raw_v[t], bounds_error=False, fill_value=0.0)
            rgi_p = RegularGridInterpolator((lat_vals, lon_vals), raw_p[t], bounds_error=False, fill_value=101325.0)

            u_vals[t] = rgi_u(pts).reshape((ny, nx))
            v_vals[t] = rgi_v(pts).reshape((ny, nx))
            p_vals[t] = rgi_p(pts).reshape((ny, nx))

        plot_lon_2d, plot_lat_2d = glon, glat
        clon, clat = glon[ny // 2, nx // 2], glat[ny // 2, nx // 2]
        proj_label = f"UTM ({crs.name})"
    else:
        # Standar LONG/LAT
        if output_dfs2_file is None:
            folder_parent = os.path.dirname(nc_files[0])
            output_dfs2_file = os.path.join(folder_parent, "Wind_Forcing_LongLat.dfs2")

        nx = len(lon_vals)
        ny = len(lat_vals)
        dx = float(abs(lon_vals[1] - lon_vals[0]))
        dy = float(abs(lat_vals[1] - lat_vals[0]))
        origin_x = float(lon_vals[0])
        origin_y = float(lat_vals[0])

        print(f"[INFO] Geometri LONG/LAT Grid2D: ny={ny}, nx={nx}, dx={dx:.4f}°, dy={dy:.4f}°")
        print(f"[INFO] Origin: ({origin_x:.4f}, {origin_y:.4f}) | Timestep: {n_timesteps}")

        geometry = mikeio.Grid2D(
            dx=dx,
            dy=dy,
            nx=nx,
            ny=ny,
            origin=(origin_x, origin_y),
            projection="LONG/LAT"
        )

        u_vals = ds[u_var].values.astype(np.float32)
        v_vals = ds[v_var].values.astype(np.float32)
        p_vals = ds[p_var].values.astype(np.float32)

        plot_lon_2d, plot_lat_2d = np.meshgrid(lon_vals, lat_vals)
        clon, clat = lon_vals[nx // 2], lat_vals[ny // 2]
        proj_label = "LONG/LAT (WGS84)"

    os.makedirs(os.path.dirname(os.path.abspath(output_dfs2_file)), exist_ok=True)

    da_u = mikeio.DataArray(
        data=u_vals,
        time=time_steps,
        geometry=geometry,
        item=ItemInfo("10m u-velocity", EUMType.Wind_Velocity, EUMUnit.meter_per_sec)
    )

    da_v = mikeio.DataArray(
        data=v_vals,
        time=time_steps,
        geometry=geometry,
        item=ItemInfo("10m v-velocity", EUMType.Wind_Velocity, EUMUnit.meter_per_sec)
    )

    da_p = mikeio.DataArray(
        data=p_vals,
        time=time_steps,
        geometry=geometry,
        item=ItemInfo("Pressure", EUMType.Pressure, EUMUnit.pascal)
    )

    ds_mike = mikeio.Dataset([da_u, da_v, da_p])
    ds_mike.to_dfs(output_dfs2_file)
    print(f"[SUKSES] File DFS2 Wind Forcing ({proj_label}) tersimpan: {output_dfs2_file}")

    center_y_idx = ny // 2
    center_x_idx = nx // 2
    u_center = u_vals[:, center_y_idx, center_x_idx]
    v_center = v_vals[:, center_y_idx, center_x_idx]
    speed_center = np.hypot(u_center, v_center)
    dir_center = (270.0 - np.degrees(np.arctan2(v_center, u_center))) % 360.0

    max_t_idx = int(np.argmax(speed_center))

    sample_info = {
        "lon_2d": plot_lon_2d,
        "lat_2d": plot_lat_2d,
        "u_max_slice": u_vals[max_t_idx],
        "v_max_slice": v_vals[max_t_idx],
        "p_max_slice": p_vals[max_t_idx] / 100.0,
        "max_time_str": str(time_steps[max_t_idx]),
        "time_steps": time_steps,
        "speed_center": speed_center,
        "dir_center": dir_center,
        "center_coord": (clon, clat),
        "target_proj": proj_label,
        "output_file": output_dfs2_file
    }

    ds.close()
    return sample_info


def visualisasi_wind_forcing(sample_info):
    """Menampilkan visualisasi preview peta vektor angin dan time series kecepatan angin."""
    try:
        import matplotlib.pyplot as plt
        import warnings
        warnings.filterwarnings("ignore", message=".*Ignoring fixed.*")
    except ImportError:
        print("[INFO] Matplotlib tidak terpasang, preview visual dilewati.")
        return

    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1.0])

    lon_2d = sample_info["lon_2d"]
    lat_2d = sample_info["lat_2d"]
    u_slice = sample_info["u_max_slice"]
    v_slice = sample_info["v_max_slice"]
    p_slice = sample_info["p_max_slice"]
    speed_slice = np.hypot(u_slice, v_slice)

    # 1. Peta Vektor Spasial Angin 2D
    ax_map = fig.add_subplot(gs[:, 0])
    cf = ax_map.contourf(lon_2d, lat_2d, p_slice, cmap='coolwarm', alpha=0.6, levels=12)
    cb = plt.colorbar(cf, ax=ax_map, orientation='horizontal', pad=0.08, shrink=0.85)
    cb.set_label("Tekanan Permukaan Laut / MSL (hPa)")

    skip = (slice(None, None, 1), slice(None, None, 1))
    q = ax_map.quiver(lon_2d[skip], lat_2d[skip], u_slice[skip], v_slice[skip],
                      speed_slice[skip], cmap='viridis', scale=120, width=0.005)

    clon, clat = sample_info["center_coord"]
    ax_map.scatter(clon, clat, color='red', marker='*', s=120, zorder=5, label='Titik Monitoring Tengah')

    ax_map.set_title(f"Peta Sebaran Vektor Angin 2D ({sample_info['target_proj']})\nSnapshot Waktu: {sample_info['max_time_str']}", fontsize=10, fontweight='bold')
    ax_map.set_xlabel("Longitude (°E)")
    ax_map.set_ylabel("Latitude (°S)")
    ax_map.set_aspect('equal', adjustable='datalim')
    ax_map.grid(True, linestyle='--', alpha=0.5)
    ax_map.legend(loc='lower left', fontsize=8)

    # 2. Grafik Kecepatan Angin
    t = sample_info["time_steps"]
    ax_spd = fig.add_subplot(gs[0, 1])
    ax_spd.plot(t, sample_info["speed_center"], color='#D32F2F', lw=1.0, label='Kecepatan Angin (m/s)')
    ax_spd.set_title(f"Preview Deret Waktu Angin ({clon:.2f}°E, {clat:.2f}°S)", fontsize=10, fontweight='bold')
    ax_spd.set_ylabel("Kecepatan (m/s)")
    ax_spd.grid(True, linestyle='--', alpha=0.5)
    ax_spd.legend(loc='upper right', fontsize=8)

    # 3. Grafik Arah Angin
    ax_dir = fig.add_subplot(gs[1, 1], sharex=ax_spd)
    ax_dir.scatter(t[::12], sample_info["dir_center"][::12], color='#1976D2', s=6, alpha=0.6, label='Arah Datang Angin (°)')
    ax_dir.set_ylabel("Arah (° Dari)")
    ax_dir.set_xlabel("Waktu (Bulan/Tahun)")
    ax_dir.grid(True, linestyle='--', alpha=0.5)
    ax_dir.legend(loc='upper right', fontsize=8)

    fig.tight_layout()
    plt.show()


def jalankan_gui():
    """Antarmuka GUI Desktop Tkinter."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    def browse_nc_folder():
        d = filedialog.askdirectory(title="Pilih Folder Berisi File NetCDF Angin (.nc)")
        if d:
            entry_nc.delete(0, tk.END)
            entry_nc.insert(0, d)
            update_default_out()

    def update_default_out(*args):
        d = entry_nc.get().strip()
        if d:
            z_txt = entry_utm_zone.get().strip().upper() if var_proj.get() == "UTM" else "LongLat"
            suffix = f"UTM_{z_txt}" if var_proj.get() == "UTM" else "LongLat"
            default_file = os.path.join(d, f"Wind_Forcing_{suffix}.dfs2")
            entry_out.delete(0, tk.END)
            entry_out.insert(0, default_file)

    def on_proj_change():
        if var_proj.get() == "UTM":
            entry_utm_zone.config(state="normal")
            lbl_utm.config(fg="black")
        else:
            entry_utm_zone.config(state="disabled")
            lbl_utm.config(fg="gray")
        update_default_out()

    def browse_out():
        f = filedialog.asksaveasfilename(
            title="Simpan File Wind Forcing DFS2",
            defaultextension=".dfs2",
            filetypes=(("MIKE DFS2", "*.dfs2"), ("All Files", "*.*"))
        )
        if f:
            entry_out.delete(0, tk.END)
            entry_out.insert(0, f)

    def aksi_proses():
        nc_p = entry_nc.get().strip()
        out_p = entry_out.get().strip()
        proj_mode = var_proj.get()
        custom_z = entry_utm_zone.get().strip()

        if not nc_p or not os.path.exists(nc_p):
            messagebox.showerror("Error", "Pilih folder data NetCDF Angin yang valid!")
            return
        if not out_p:
            messagebox.showerror("Error", "Tentukan lokasi file output .dfs2!")
            return

        try:
            info = proses_wind_nc_to_dfs2(
                wind_folder_or_file=nc_p,
                output_dfs2_file=out_p,
                target_proj=proj_mode,
                utm_zone=custom_z
            )
            msg = (
                f"SUKSES!\n\n"
                f"File Wind Forcing DFS2 berhasil dibuat:\n{out_p}\n\n"
                f"• Sistem Proyeksi: {info['target_proj']}\n"
                f"• Total Langkah Waktu: {len(info['time_steps'])} timestep\n"
                f"• Variabel: 10m u-velocity, 10m v-velocity, Pressure\n\n"
                f"Klik OK untuk melihat visualisasi peta vektor angin dan grafik."
            )
            messagebox.showinfo("Konversi Berhasil", msg)
            visualisasi_wind_forcing(info)
        except Exception as e:
            messagebox.showerror("Gagal", f"Terjadi kesalahan saat memproses:\n{e}")

    root = tk.Tk()
    root.title("Konverter Wind NetCDF ke DFS2 (Universal UTM & LONG/LAT)")
    root.geometry("640x350")
    root.resizable(False, False)

    lbl_title = tk.Label(root, text="Generator Wind Forcing (.dfs2) dari NetCDF (Universal)", font=("Arial", 11, "bold"))
    lbl_title.pack(pady=8)

    frm = tk.Frame(root, padx=15, pady=5)
    frm.pack(fill="both", expand=True)

    # 1. Folder NC
    tk.Label(frm, text="Folder NetCDF Angin:", anchor="w").grid(row=0, column=0, sticky="w", pady=4)
    entry_nc = tk.Entry(frm, width=44)
    entry_nc.grid(row=0, column=1, padx=5, pady=4)
    tk.Button(frm, text="Browse...", command=browse_nc_folder, width=10).grid(row=0, column=2, padx=5, pady=4)

    # 2. Pilihan Proyeksi
    tk.Label(frm, text="Sistem Proyeksi DFS2:", anchor="w").grid(row=1, column=0, sticky="w", pady=4)
    var_proj = tk.StringVar(value="LONG/LAT")
    
    frm_radio = tk.Frame(frm)
    frm_radio.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=2)
    rb1 = tk.Radiobutton(frm_radio, text="LONG/LAT (WGS84 - Rekomendasi Resmi MIKE 21)", variable=var_proj, value="LONG/LAT", command=on_proj_change)
    rb1.pack(anchor="w")
    rb2 = tk.Radiobutton(frm_radio, text="UTM Meter (Universal Semua Zona Dunia)", variable=var_proj, value="UTM", command=on_proj_change)
    rb2.pack(anchor="w")

    # Zona UTM Entry
    lbl_utm = tk.Label(frm, text="Pilihan Zona UTM:", anchor="w", fg="gray")
    lbl_utm.grid(row=2, column=0, sticky="w", pady=4)
    entry_utm_zone = tk.Entry(frm, width=15, state="disabled")
    entry_utm_zone.insert(0, "AUTO")
    entry_utm_zone.grid(row=2, column=1, sticky="w", padx=5, pady=4)
    lbl_hint = tk.Label(frm, text="('AUTO' = deteksi otomatis, atau isi misal 48S, 50S, 52S, 46N)", font=("Arial", 8, "italic"), fg="gray")
    lbl_hint.grid(row=2, column=1, padx=(110, 0), sticky="w")

    # 3. Output File
    tk.Label(frm, text="File Output DFS2:", anchor="w").grid(row=3, column=0, sticky="w", pady=4)
    entry_out = tk.Entry(frm, width=44)
    entry_out.grid(row=3, column=1, padx=5, pady=4)
    tk.Button(frm, text="Browse...", command=browse_out, width=10).grid(row=3, column=2, padx=5, pady=4)

    tk.Button(root, text="KONVERSI SEKARANG & LIHAT PREVIEW VISUAL", command=aksi_proses, bg="#1E88E5", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=25, pady=(5, 12))

    root.mainloop()


def jalankan_cli():
    """Eksekusi command-line."""
    import argparse
    parser = argparse.ArgumentParser(description="Konversi Wind NetCDF ke DFS2 (Universal UTM & LONG/LAT)")
    parser.add_argument("wind_folder", help="Folder berisi file .nc angin ERA5")
    parser.add_argument("output_dfs2", nargs="?", default=None, help="File .dfs2 output tujuan")
    parser.add_argument("--proj", choices=["LONG/LAT", "UTM"], default="LONG/LAT", help="Pilihan proyeksi output")
    parser.add_argument("--zone", default="AUTO", help="Zona UTM (contoh: AUTO, 48S, 50S, 52S, 46N)")
    parser.add_argument("--no-plot", action="store_true", help="Jangan tampilkan plot grafik")

    args = parser.parse_args()
    info = proses_wind_nc_to_dfs2(args.wind_folder, args.output_dfs2, target_proj=args.proj, utm_zone=args.zone)
    if not args.no_plot:
        visualisasi_wind_forcing(info)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        try:
            jalankan_gui()
        except Exception as e:
            print(f"[INFO] GUI Tkinter tidak dapat dibuka ({e}). Beralih ke bantuan CLI:")
            jalankan_cli()
    else:
        jalankan_cli()
