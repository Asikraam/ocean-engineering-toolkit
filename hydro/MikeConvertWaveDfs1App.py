r"""
# DHI MIKE 21 SW Spectral Wave Boundary Condition Generator (NetCDF to DFS1)

Interactive desktop tool designed to generate DHI MIKE 21 Spectral Wave (SW) line boundary files (`.dfs1`) directly from atmospheric/oceanographic NetCDF datasets (ERA5 & Copernicus Marine Service).

## Key Engineering Capabilities
- **Mesh Open Boundary Code Auto-Detection**:
  - Parses project mesh (`.mesh`) to detect open boundary segments (Code 2, Code 3, Code 4, etc.).
- **Counter-Clockwise (CCW) Point Sorting**:
  - Enforces mandatory DHI MIKE SW geometric node ordering to prevent inverse wave propagation direction errors.
- **Spectral Parameter Interpolation**:
  - Extracts Significant Wave Height ($H_s$), Peak Wave Period ($T_p$), Mean Wave Direction ($MWD$), and calculates Directional Standard Deviation ($DSD$).
- **Visual Preview Dashboard**:
  - Interactive map preview displaying model boundary lines, coordinate node sequences, and wave climate time-series.

## Installation & Requirements
```bash
pip install -r requirements.txt
```
Dependencies: `mikeio >= 1.5.0`, `netCDF4 >= 1.6.5`, `numpy >= 1.26.0`, `matplotlib >= 3.8.0`

## How to Run
```bash
python hydro/MikeConvertWaveDfs1App.py
```
Or via main toolkit CLI:
```bash
python cli.py mike-wave-dfs1
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
from scipy.interpolate import interp1d
import pyproj
from pyproj import Transformer
import mikeio
from mikeio.eum import EUMType, ItemInfo, EUMUnit


def order_polyline_nearest_neighbor(coords):
    """Menyusun titik polyline berdasarkan ketetanggaan terdekat."""
    coords = list(coords)
    if not coords:
        return []
    ordered = [coords.pop(0)]
    while coords:
        last = ordered[-1]
        nearest_idx = min(range(len(coords)), key=lambda i: math.hypot(coords[i][0] - last[0], coords[i][1] - last[1]))
        ordered.append(coords.pop(nearest_idx))
    return ordered


def ensure_ccw_direction(ordered_coords, centroid):
    """Memastikan urutan titik berjalan Counter-Clockwise (CCW) mengelilingi pusat domain."""
    if len(ordered_coords) < 2:
        return ordered_coords
    start, end = ordered_coords[0], ordered_coords[-1]
    v_start = (start[0] - centroid[0], start[1] - centroid[1])
    v_end = (end[0] - centroid[0], end[1] - centroid[1])
    cross_product = v_start[0] * v_end[1] - v_start[1] * v_end[0]
    if cross_product < 0:
        return ordered_coords[::-1]
    return ordered_coords


def generate_equidistant_points(path, target_spacing):
    """Menghasilkan titik stasiun berjarak teratur (equidistant) sepanjang garis batas."""
    if len(path) < 2:
        return path, 0.0
    x = [p[0] for p in path]
    y = [p[1] for p in path]
    dx = np.diff(x)
    dy = np.diff(y)
    segment_lengths = np.hypot(dx, dy)
    cumulative_dist = np.insert(np.cumsum(segment_lengths), 0, 0.0)
    total_length = cumulative_dist[-1]
    
    num_intervals = int(np.floor(total_length / target_spacing))
    if num_intervals == 0:
        return [tuple(path[0])], 0.0
        
    actual_spacing = total_length / num_intervals
    s_new = np.linspace(0, total_length, num_intervals + 1)
    
    fx = interp1d(cumulative_dist, x, kind='linear')
    fy = interp1d(cumulative_dist, y, kind='linear')
    
    x_new = fx(s_new)
    y_new = fy(s_new)
    return list(zip(x_new, y_new)), actual_spacing


def proses_wave_nc_to_dfs1(wave_folder_or_file, mesh_file, output_folder=None,
                           mesh_epsg="EPSG:32752", nc_epsg="EPSG:4326",
                           spacing_multiplier=0.5, custom_dsd=12.5):
    """
    Eksekusi konversi NetCDF gelombang menjadi DFS1 per kode boundary mesh.
    """
    if os.path.isdir(wave_folder_or_file):
        nc_files = sorted(glob.glob(os.path.join(wave_folder_or_file, "*.nc")))
        if not nc_files:
            raise FileNotFoundError(f"Tidak ada file .nc di folder: {wave_folder_or_file}")
    elif os.path.isfile(wave_folder_or_file):
        nc_files = [wave_folder_or_file]
    else:
        raise FileNotFoundError(f"Path Wave tidak ditemukan: {wave_folder_or_file}")

    if not os.path.exists(mesh_file):
        raise FileNotFoundError(f"File mesh tidak ditemukan: {mesh_file}")

    if output_folder is None:
        output_folder = os.path.dirname(mesh_file)
    os.makedirs(output_folder, exist_ok=True)

    print(f"[INFO] Membaca {len(nc_files)} file NetCDF Wave...")
    ds = xr.open_mfdataset(nc_files, combine='by_coords')

    # Deteksi nama kolom koordinat
    lon_col = 'longitude' if 'longitude' in ds.coords else 'lon'
    lat_col = 'latitude' if 'latitude' in ds.coords else 'lat'
    time_col = 'valid_time' if 'valid_time' in ds.coords else 'time'

    # Deteksi nama variabel
    var_map = {}
    for candidate in ['swh', 'VHM0', 'significant_height_of_combined_wind_waves_and_swell']:
        if candidate in ds.data_vars:
            var_map['hs'] = candidate
            break
    for candidate in ['pp1d', 'mwp', 'VTPK', 'peak_wave_period']:
        if candidate in ds.data_vars:
            var_map['tp'] = candidate
            break
    for candidate in ['mwd', 'VMDR', 'mean_wave_direction']:
        if candidate in ds.data_vars:
            var_map['dir'] = candidate
            break

    if 'hs' not in var_map or 'tp' not in var_map or 'dir' not in var_map:
        raise ValueError(f"Variabel gelombang tidak lengkap di NetCDF. Ditemukan: {list(ds.data_vars.keys())}")

    print(f"[INFO] Variabel terdeteksi: Hs='{var_map['hs']}', Tp='{var_map['tp']}', Dir='{var_map['dir']}'")
    print(f"[INFO] Dimensi waktu: {len(ds[time_col])} langkah waktu.")

    # Hitung resolusi grid NetCDF
    lon_vals = ds.coords[lon_col].values
    lat_vals = ds.coords[lat_col].values
    lon_spacing = abs(np.mean(np.diff(lon_vals)))
    lat_spacing = abs(np.mean(np.diff(lat_vals)))
    mean_lat = np.mean(lat_vals)
    nc_spacing_x = lon_spacing * 111320 * np.cos(np.radians(mean_lat))
    nc_spacing_y = lat_spacing * 111000
    nc_resolution = min(nc_spacing_x, nc_spacing_y)
    target_spacing = nc_resolution * spacing_multiplier
    print(f"[INFO] Resolusi NetCDF: ~{nc_resolution:.1f}m | Jarak Antar Stasiun Batas: {target_spacing:.1f}m")

    # Baca Mesh
    print(f"[INFO] Membaca mesh: {mesh_file}")
    msh = mikeio.Mesh(mesh_file)
    mesh_boundaries_raw = {}
    all_x, all_y = [], []
    for i, code in enumerate(msh.geometry.codes):
        x = float(msh.geometry.node_coordinates[i, 0])
        y = float(msh.geometry.node_coordinates[i, 1])
        all_x.append(x)
        all_y.append(y)
        if code > 1: # Open boundary
            if code not in mesh_boundaries_raw:
                mesh_boundaries_raw[code] = []
            mesh_boundaries_raw[code].append((x, y))

    if not mesh_boundaries_raw:
        raise ValueError("Tidak ditemukan kode batas terbuka (code > 1) di dalam file mesh.")

    domain_centroid = (np.mean(all_x), np.mean(all_y))
    try:
        mesh_crs = pyproj.CRS.from_user_input(msh.geometry.projection_string)
        print(f"[INFO] Sistem Proyeksi Mesh Otomatis Terdeteksi: {mesh_crs.name}")
    except Exception:
        mesh_crs = mesh_epsg
        print(f"[INFO] Menggunakan proyeksi mesh manual: {mesh_epsg}")
    transformer_to_ll = Transformer.from_crs(mesh_crs, nc_epsg, always_xy=True)

    generated_files = []
    boundaries_info = {}

    for code in sorted(mesh_boundaries_raw.keys()):
        raw_coords = mesh_boundaries_raw[code]
        ordered_xy = order_polyline_nearest_neighbor(raw_coords)
        ccw_xy = ensure_ccw_direction(ordered_xy, domain_centroid)
        synthetic_xy, actual_spacing = generate_equidistant_points(ccw_xy, target_spacing)

        # Ubah ke Lon/Lat
        ll_coords = [transformer_to_ll.transform(x, y) for x, y in synthetic_xy]
        num_stations = len(ll_coords)
        safe_dx = max(float(actual_spacing), 1.0)

        print(f"[INFO] Memproses Boundary Code {code}: {num_stations} stasiun (dx={safe_dx:.1f}m)...")

        lons_da = xr.DataArray([c[0] for c in ll_coords], dims="station")
        lats_da = xr.DataArray([c[1] for c in ll_coords], dims="station")

        # Ekstrak data terdekat
        sample_slice = ds.sel({lon_col: lons_da, lat_col: lats_da}, method='nearest')
        if 'depth' in sample_slice.dims:
            sample_slice = sample_slice.isel(depth=0)

        time_steps = pd.DatetimeIndex(ds[time_col].values)
        geometry = mikeio.Grid1D(
            nx=num_stations,
            dx=safe_dx,
            projection=msh.geometry.projection_string
        )

        # Siapkan DataArray mikeio
        da_list = []
        
        # 1. Hs
        vals_hs = sample_slice[var_map['hs']].transpose(time_col, 'station').values.astype(np.float32)
        da_hs = mikeio.DataArray(
            data=vals_hs,
            time=time_steps,
            geometry=geometry,
            item=ItemInfo("Significant wave height", EUMType.Significant_wave_height, EUMUnit.meter)
        )
        da_list.append(da_hs)

        # 2. Tp
        vals_tp = sample_slice[var_map['tp']].transpose(time_col, 'station').values.astype(np.float32)
        da_tp = mikeio.DataArray(
            data=vals_tp,
            time=time_steps,
            geometry=geometry,
            item=ItemInfo("Wave period", EUMType.Wave_period, EUMUnit.second)
        )
        da_list.append(da_tp)

        # 3. Dir
        vals_dir = sample_slice[var_map['dir']].transpose(time_col, 'station').values.astype(np.float32)
        da_dir = mikeio.DataArray(
            data=vals_dir,
            time=time_steps,
            geometry=geometry,
            item=ItemInfo("Wave direction", EUMType.Wave_direction, EUMUnit.degree)
        )
        da_list.append(da_dir)

        # 4. DSD (Directional Standard Deviation)
        vals_dsd = np.full((len(time_steps), num_stations), custom_dsd, dtype=np.float32)
        da_dsd = mikeio.DataArray(
            data=vals_dsd,
            time=time_steps,
            geometry=geometry,
            item=ItemInfo("Directional Standard Deviation", EUMType.Directional_Standard_Deviation, EUMUnit.degree)
        )
        da_list.append(da_dsd)

        # Tulis DFS1
        mesh_base = os.path.splitext(os.path.basename(mesh_file))[0]
        out_filename = os.path.join(output_folder, f"Wave_Boundary_{mesh_base}_Code_{code}.dfs1")
        ds_mike = mikeio.Dataset(da_list)
        ds_mike.to_dfs(out_filename)
        print(f"[SUKSES] DFS1 tersimpan: {out_filename}")
        generated_files.append(out_filename)

        boundaries_info[code] = {
            "synthetic_xy": synthetic_xy,
            "ll_coords": ll_coords,
            "sample_hs": vals_hs[:, 0], # Stasiun pertama
            "sample_tp": vals_tp[:, 0],
            "sample_dir": vals_dir[:, 0],
            "time_steps": time_steps,
            "filename": out_filename
        }

    ds.close()

    return {
        "mesh_boundaries": boundaries_info,
        "centroid": domain_centroid,
        "all_x": all_x,
        "all_y": all_y,
        "generated_files": generated_files
    }


def visualisasi_wave_boundary(result_info):
    """Menampilkan visualisasi preview peta batas dan time series gelombang."""
    try:
        import matplotlib.pyplot as plt
        import warnings
        warnings.filterwarnings("ignore", message=".*Ignoring fixed.*")
    except ImportError:
        print("[INFO] Matplotlib tidak terpasang, preview visual dilewati.")
        return

    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1.0])

    # 1. Peta Domain dan Boundary
    ax_map = fig.add_subplot(gs[:, 0])
    all_x = result_info["all_x"]
    all_y = result_info["all_y"]
    ax_map.scatter(all_x[::5], all_y[::5], color='lightgray', s=1, alpha=0.3, label='Mesh Domain')

    colors = ['#E53935', '#43A047', '#1E88E5', '#FB8C00', '#8E24AA']
    for idx, (code, info) in enumerate(result_info["mesh_boundaries"].items()):
        pts = info["synthetic_xy"]
        c = colors[idx % len(colors)]
        px = [p[0] for p in pts]
        py = [p[1] for p in pts]
        
        # Garis batas
        ax_map.plot(px, py, color=c, linewidth=2.5, label=f"Boundary Code {code} ({len(pts)} nodes)")
        # Arah panah CCW
        mid = len(pts) // 2
        if len(pts) >= 2:
            ax_map.annotate('', xy=(px[mid+1], py[mid+1]), xytext=(px[mid], py[mid]),
                            arrowprops=dict(arrowstyle="->", color=c, lw=2.5))
        # Titik start
        ax_map.scatter(px[0], py[0], color='black', marker='s', s=40, zorder=5)

    ax_map.set_title("Peta Verifikasi Wave Boundary (Mesh Open Boundary Nodes)\n*Panah menunjukkan orientasi Counter-Clockwise (CCW)*", fontsize=10, fontweight='bold')
    ax_map.set_xlabel("Easting / X (m)")
    ax_map.set_ylabel("Northing / Y (m)")
    ax_map.set_aspect('equal', adjustable='datalim')
    ax_map.grid(True, linestyle='--', alpha=0.5)
    ax_map.legend(loc='lower right', fontsize=8)

    # Ambil sample boundary pertama untuk time series
    first_code = list(result_info["mesh_boundaries"].keys())[0]
    sample = result_info["mesh_boundaries"][first_code]
    t = sample["time_steps"]

    # 2. Grafik Hs & Tp Time Series
    ax_hs = fig.add_subplot(gs[0, 1])
    ax_hs.plot(t, sample["sample_hs"], color='#1E88E5', lw=1.2, label='Hs (Tinggi Signifikan [m])')
    ax_hs.plot(t, sample["sample_tp"], color='#FB8C00', lw=1.0, alpha=0.8, label='Tp (Periode Puncak [s])')
    ax_hs.set_title(f"Preview Deret Waktu Gelombang (Code {first_code} - Stasiun 1)", fontsize=10, fontweight='bold')
    ax_hs.set_ylabel("Hs (m) / Tp (s)")
    ax_hs.grid(True, linestyle='--', alpha=0.5)
    ax_hs.legend(loc='upper right', fontsize=8)

    # 3. Grafik Arah Gelombang
    ax_dir = fig.add_subplot(gs[1, 1], sharex=ax_hs)
    ax_dir.scatter(t[::6], sample["sample_dir"][::6], color='#43A047', s=8, alpha=0.7, label='Arah Gelombang (°)')
    ax_dir.set_ylabel("Arah (° Nautical)")
    ax_dir.set_xlabel("Waktu (Tanggal)")
    ax_dir.grid(True, linestyle='--', alpha=0.5)
    ax_dir.legend(loc='upper right', fontsize=8)

    fig.tight_layout()
    plt.show()


def jalankan_gui():
    """Antarmuka GUI Desktop Tkinter."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    def browse_nc_folder():
        d = filedialog.askdirectory(title="Pilih Folder Berisi File NetCDF Gelombang (.nc)")
        if d:
            entry_nc.delete(0, tk.END)
            entry_nc.insert(0, d)

    def browse_mesh():
        f = filedialog.askopenfilename(title="Pilih File Mesh (.mesh)", filetypes=(("MIKE Mesh", "*.mesh"), ("All Files", "*.*")))
        if f:
            entry_mesh.delete(0, tk.END)
            entry_mesh.insert(0, f)
            if not entry_out.get().strip():
                default_dir = os.path.dirname(f)
                entry_out.delete(0, tk.END)
                entry_out.insert(0, default_dir)

    def browse_out():
        d = filedialog.askdirectory(title="Pilih Folder Penyimpanan File DFS1")
        if d:
            entry_out.delete(0, tk.END)
            entry_out.insert(0, d)

    def aksi_proses():
        nc_p = entry_nc.get().strip()
        mesh_p = entry_mesh.get().strip()
        out_p = entry_out.get().strip() or None

        if not nc_p or not os.path.exists(nc_p):
            messagebox.showerror("Error", "Pilih folder data NetCDF Wave yang valid!")
            return
        if not mesh_p or not os.path.exists(mesh_p):
            messagebox.showerror("Error", "Pilih file .mesh yang valid!")
            return

        try:
            mult = float(entry_mult.get().strip())
            dsd_val = 12.5  # Nilai standar MIKE 21 SW di latar belakang
        except ValueError:
            messagebox.showerror("Error", "Parameter spacing multiplier tidak valid!")
            return

        try:
            res = proses_wave_nc_to_dfs1(
                wave_folder_or_file=nc_p,
                mesh_file=mesh_p,
                output_folder=out_p,
                spacing_multiplier=mult,
                custom_dsd=dsd_val
            )
            files_str = "\n".join([f"• {os.path.basename(f)}" for f in res["generated_files"]])
            msg = f"SUKSES!\n\nFile Wave Boundary .dfs1 berhasil dibuat:\n{files_str}\n\nKlik OK untuk melihat preview visual peta dan grafik gelombang."
            messagebox.showinfo("Konversi Selesai", msg)
            visualisasi_wave_boundary(res)
        except Exception as e:
            messagebox.showerror("Gagal", f"Terjadi kesalahan saat memproses:\n{e}")

    root = tk.Tk()
    root.title("Konverter Wave NetCDF ke DFS1 (MIKE 21 SW)")
    root.geometry("620x290")
    root.resizable(False, False)

    lbl_title = tk.Label(root, text="Generator Wave Boundary (.dfs1) dari NetCDF", font=("Arial", 11, "bold"))
    lbl_title.pack(pady=8)

    frm = tk.Frame(root, padx=15, pady=5)
    frm.pack(fill="both", expand=True)

    # 1. Folder NC
    tk.Label(frm, text="Folder NetCDF Wave:", anchor="w").grid(row=0, column=0, sticky="w", pady=4)
    entry_nc = tk.Entry(frm, width=44)
    entry_nc.grid(row=0, column=1, padx=5, pady=4)
    tk.Button(frm, text="Browse...", command=browse_nc_folder, width=10).grid(row=0, column=2, padx=5, pady=4)

    # 2. File Mesh
    tk.Label(frm, text="File Mesh (.mesh):", anchor="w").grid(row=1, column=0, sticky="w", pady=4)
    entry_mesh = tk.Entry(frm, width=44)
    entry_mesh.grid(row=1, column=1, padx=5, pady=4)
    tk.Button(frm, text="Browse...", command=browse_mesh, width=10).grid(row=1, column=2, padx=5, pady=4)

    # 3. Output Dir
    tk.Label(frm, text="Folder Output DFS1:", anchor="w").grid(row=2, column=0, sticky="w", pady=4)
    entry_out = tk.Entry(frm, width=44)
    entry_out.grid(row=2, column=1, padx=5, pady=4)
    tk.Button(frm, text="Browse...", command=browse_out, width=10).grid(row=2, column=2, padx=5, pady=4)

    # 4. Spacing Multiplier
    tk.Label(frm, text="Spacing Multiplier:", anchor="w").grid(row=3, column=0, sticky="w", pady=4)
    entry_mult = tk.Entry(frm, width=12)
    entry_mult.insert(0, "0.5")
    entry_mult.grid(row=3, column=1, sticky="w", padx=5, pady=4)
    tk.Label(frm, text="(0.5 = 2x resolusi grid NC)", font=("Arial", 8, "italic"), fg="gray").grid(row=3, column=1, padx=(90, 0), sticky="w")

    tk.Button(root, text="KONVERSI SEKARANG & LIHAT PREVIEW VISUAL", command=aksi_proses, bg="#1E88E5", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=25, pady=(5, 12))

    root.mainloop()


def jalankan_cli():
    """Eksekusi command-line."""
    import argparse
    parser = argparse.ArgumentParser(description="Konversi Wave NetCDF ke DFS1 (MIKE 21 SW)")
    parser.add_argument("wave_folder", help="Folder berisi file .nc gelombang")
    parser.add_argument("mesh_file", help="File .mesh domain")
    parser.add_argument("--out", default=None, help="Folder tujuan penyimpanan file .dfs1")
    parser.add_argument("--multiplier", type=float, default=0.5, help="Faktor pengali resolusi stasiun batas")
    parser.add_argument("--dsd", type=float, default=12.5, help="Nilai Directional Standard Deviation")
    parser.add_argument("--no-plot", action="store_true", help="Jangan tampilkan plot grafik")

    args = parser.parse_args()
    res = proses_wave_nc_to_dfs1(
        wave_folder_or_file=args.wave_folder,
        mesh_file=args.mesh_file,
        output_folder=args.out,
        spacing_multiplier=args.multiplier,
        custom_dsd=args.dsd
    )
    if not args.no_plot:
        visualisasi_wave_boundary(res)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        try:
            jalankan_gui()
        except Exception as e:
            print(f"[INFO] GUI Tkinter tidak dapat dibuka ({e}). Beralih ke bantuan CLI:")
            jalankan_cli()
    else:
        jalankan_cli()
