r"""
# DHI MIKE 21 Universal Pile & Obstacle Inserter (CLI & GUI)

Production-grade algorithm to convert structural pile coordinates (XYZ points) into closed rectangular polygons for DHI MIKE 21 Flexible Mesh (FM) hydrodynamic obstruction modeling.

## Features
- **Smart Auto-Detection**:
  - Automatically identifies whether input is a single-point centroid file (1 line = 1 pile) or an existing boundary file.
  - Computes true centroids to prevent duplicate 4-corner cluster artifacts.
- **Standard MIKE Connectivity**:
  - Uses exact DHI connectivity codes: `1, 1, 1, 1, 0` with blank delimiter lines per pile for clean obstruction boundaries.
- **Dual Mode (CLI & GUI)**:
  - Supports interactive Tkinter dialogs or headless command-line execution for automated batch workflows.
- **Heading & Azimuth Rotation**:
  - Automatically derives rotation angles from coordinate trends or allows manual degree overrides.

## Usage
```bash
# Launch interactive GUI
python hydro/MikeInsertPilesUniversal.py

# Headless CLI conversion
python hydro/MikeInsertPilesUniversal.py --input piles.xyz --output boundary.xyz --width 1.2 --length 1.2 --angle 45.0
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import sys
import os
import math

def parse_input_piles(filepath):
    """
    Membaca file XYZ secara cerdas:
    - Jika input berupa Scatter Point (1 baris = 1 titik pusat pile), langsung diambil.
    - Jika input berupa Boundary Polygon lama (berisi 4-5 titik sudut per tiang),
      script secara otomatis menghitung centroid (titik tengahnya) agar tidak
      beranak menjadi 4 kotak di sudut tiang.
    """
    raw_lines = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2]) if len(parts) > 2 else 0.0
                    conn = int(float(parts[3])) if len(parts) > 3 else 0
                    raw_lines.append((x, y, z, conn))
                except ValueError:
                    pass

    if not raw_lines:
        raise ValueError(f"File '{filepath}' kosong atau tidak memiliki koordinat valid!")

    # Deteksi apakah file ini adalah boundary polygon yang sudah ada
    # Cirinya: ada connectivity 1 dan 0, atau titik-titik berurutan berjarak sangat dekat (~1m)
    has_conn_1 = any(p[3] == 1 for p in raw_lines[:100])
    close_consecutive = 0
    for i in range(min(30, len(raw_lines) - 1)):
        dist = math.hypot(raw_lines[i+1][0] - raw_lines[i][0], raw_lines[i+1][1] - raw_lines[i][1])
        if 0.4 <= dist <= 1.8:
            close_consecutive += 1

    is_boundary_file = has_conn_1 or (close_consecutive >= 3)

    centers = []
    detected_type = ""

    if is_boundary_file:
        # File ini adalah boundary polygon (berisi 4-5 titik sudut per kotak)
        # Ekstrak titik tengah (centroid) dari masing-masing kotak lama
        curr_poly = []
        for p in raw_lines:
            curr_poly.append(p)
            is_closing = (p[3] == 0 and len(curr_poly) >= 3)
            if not is_closing and len(curr_poly) >= 4:
                d_start = math.hypot(p[0] - curr_poly[0][0], p[1] - curr_poly[0][1])
                if d_start < 0.01:
                    is_closing = True
            
            if is_closing or len(curr_poly) == 5:
                pts = curr_poly
                if len(curr_poly) >= 2:
                    d_start = math.hypot(curr_poly[-1][0] - curr_poly[0][0], curr_poly[-1][1] - curr_poly[0][1])
                    if d_start < 0.01:
                        pts = curr_poly[:-1]
                
                if len(pts) >= 3:
                    cx = sum(pt[0] for pt in pts) / len(pts)
                    cy = sum(pt[1] for pt in pts) / len(pts)
                    centers.append((cx, cy))
                curr_poly = []

        if len(curr_poly) >= 3:
            cx = sum(pt[0] for pt in curr_poly) / len(curr_poly)
            cy = sum(pt[1] for pt in curr_poly) / len(curr_poly)
            centers.append((cx, cy))

        detected_type = "BOUNDARY_POLYGON (Titik Sudut Kotak Lama -> Otomatis Diekstrak Centroid Titik Pusat)"
    else:
        # File scatter murni titik pusat pile
        centers = [(p[0], p[1]) for p in raw_lines]
        detected_type = "SCATTER_CENTER_POINTS (Titik Pusat Pile Murni)"

    return detected_type, centers


def hitung_kotak_pile(input_file, output_file, geser=0.5, custom_angle_deg=None, z_value=0.0):
    """
    Menghasilkan 1 kotak bujur sangkar (default 1m x 1m) per titik tengah tiang pancang.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File input '{input_file}' tidak ditemukan!")

    detected_type, koordinat_pile = parse_input_piles(input_file)
    num_piles = len(koordinat_pile)
    if num_piles < 1:
        raise ValueError("Gagal menemukan titik tiang pancang dari file input.")

    # Tentukan orientasi sudut tiang (radian)
    if custom_angle_deg is not None:
        rad = math.radians(custom_angle_deg)
        sudut_deg = custom_angle_deg
        mode_sudut = f"Manual ({sudut_deg:.2f}°)"
    else:
        if num_piles >= 2:
            x1, y1 = koordinat_pile[0]
            x2, y2 = koordinat_pile[1]
            rad = math.atan2(y2 - y1, x2 - x1)
            sudut_deg = math.degrees(rad)
            mode_sudut = f"Otomatis dari orientasi titik ({sudut_deg:.2f}°)"
        else:
            rad = 0.0
            sudut_deg = 0.0
            mode_sudut = "Default 0.0°"

    lokal_titik = [
        (-geser, -geser),
        (geser, -geser),
        (geser, geser),
        (-geser, geser)
    ]

    cos_rad = math.cos(rad)
    sin_rad = math.sin(rad)

    all_boxes = []

    with open(output_file, "w") as f_out:
        for cx, cy in koordinat_pile:
            box_coords = []
            
            # Titik Sudut 1
            x_start = cx + (lokal_titik[0][0] * cos_rad - lokal_titik[0][1] * sin_rad)
            y_start = cy + (lokal_titik[0][0] * sin_rad + lokal_titik[0][1] * cos_rad)
            box_coords.append((x_start, y_start))
            
            # Titik 1: Connectivity = 1 (Tarik garis ke titik 2)
            f_out.write(f"{x_start:.6f}\t{y_start:.6f}\t{z_value:.1f}\t1\n")
            
            # Titik 2, 3, 4: Connectivity = 1 (Keliling kotak)
            for i in range(1, 4):
                lx, ly = lokal_titik[i]
                rx = cx + (lx * cos_rad - ly * sin_rad)
                ry = cy + (lx * sin_rad + ly * cos_rad)
                box_coords.append((rx, ry))
                f_out.write(f"{rx:.6f}\t{ry:.6f}\t{z_value:.1f}\t1\n")
            
            # Titik 5: Tutup Poligon kembali ke Titik 1, Connectivity = 0 (Putus garis)
            f_out.write(f"{x_start:.6f}\t{y_start:.6f}\t{z_value:.1f}\t0\n")
            box_coords.append((x_start, y_start))
            
            # Enter pemisah poligon (Anti zig-zag di MIKE Mesh Generator)
            f_out.write("\n")
            
            all_boxes.append(box_coords)

    dimensi = geser * 2.0
    return {
        "num_piles": num_piles,
        "sudut_deg": sudut_deg,
        "mode_sudut": mode_sudut,
        "dimensi": dimensi,
        "detected_type": detected_type,
        "centers": koordinat_pile,
        "boxes": all_boxes
    }


def visualisasi_plot(info, output_file):
    """Menampilkan visualisasi preview Matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import warnings
        # Filter pesan margin rasio aspek matplotlib agar terminal bersih
        warnings.filterwarnings("ignore", message=".*Ignoring fixed.*")
    except ImportError:
        print("[INFO] Matplotlib tidak ditemukan, visualisasi dilewati.")
        return

    fig, ax = plt.subplots(figsize=(9, 8))
    centers = info["centers"]
    boxes = info["boxes"]
    
    # Titik tengah
    cx = [p[0] for p in centers]
    cy = [p[1] for p in centers]
    ax.scatter(cx, cy, color='red', s=15, label=f"Titik Pusat Pile ({len(centers)} tiang)", zorder=5)

    # Poligon kotak bujur sangkar (tepat 1 kotak per tiang)
    for idx, box in enumerate(boxes):
        bx = [pt[0] for pt in box]
        by = [pt[1] for pt in box]
        label_k = "Boundary Kotak Pile (1 Tiang = 1 Kotak)" if idx == 0 else ""
        ax.plot(bx, by, color='navy', linewidth=1.2, label=label_k, zorder=4)

    ax.set_title(f"Visualisasi Hasil Pile Boundary ({info['dimensi']}m x {info['dimensi']}m)\n"
                 f"Sudut: {info['sudut_deg']:.2f}° | Total Tiang: {info['num_piles']} (1 Kotak per Tiang)",
                 fontsize=11, fontweight='bold')
    ax.set_xlabel("Easting / X (m)")
    ax.set_ylabel("Northing / Y (m)")
    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right')
    fig.tight_layout()
    plt.show()


def jalankan_gui():
    """Antarmuka GUI Tkinter Desktop."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    def pilih_input():
        f = filedialog.askopenfilename(
            title="Pilih File XYZ Input Pile",
            filetypes=(("XYZ Files", "*.xyz"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if f:
            entry_input.delete(0, tk.END)
            entry_input.insert(0, f)
            folder, fname = os.path.split(f)
            base, ext = os.path.splitext(fname)
            # Bersihkan nama jika sebelumnya berawalan Boundary_
            clean_base = base.replace("Boundary_", "").replace("_Final", "").replace("_Fixed", "")
            default_out = os.path.join(folder, f"Boundary_{clean_base}_1x1_FIX.xyz")
            entry_output.delete(0, tk.END)
            entry_output.insert(0, default_out)
            
            # Cek tipe file secara instan untuk info user
            try:
                dtype, pts = parse_input_piles(f)
                lbl_status.config(text=f"Terdeteksi: {len(pts)} tiang | {dtype.split('(')[0].strip()}", fg="#2E7D32")
            except Exception as e:
                lbl_status.config(text=f"Error baca file: {e}", fg="red")

    def pilih_output():
        f = filedialog.asksaveasfilename(
            title="Tentukan Lokasi Simpan Boundary Output",
            defaultextension=".xyz",
            filetypes=(("XYZ Files", "*.xyz"), ("All Files", "*.*"))
        )
        if f:
            entry_output.delete(0, tk.END)
            entry_output.insert(0, f)

    def aksi_proses():
        in_file = entry_input.get().strip()
        out_file = entry_output.get().strip()
        
        if not in_file or not os.path.exists(in_file):
            messagebox.showerror("Error", "Pilih file input XYZ yang valid terlebih dahulu!")
            return
        if not out_file:
            messagebox.showerror("Error", "Tentukan file output boundary tujuan!")
            return

        try:
            geser_val = float(entry_geser.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Nilai geser harus angka (0.5 = kotak 1m x 1m)!")
            return

        sudut_text = entry_sudut.get().strip()
        custom_angle = None
        if sudut_text and sudut_text.upper() != "AUTO":
            try:
                custom_angle = float(sudut_text)
            except ValueError:
                messagebox.showerror("Error", "Sudut harus angka atau 'AUTO'!")
                return

        try:
            info = hitung_kotak_pile(in_file, out_file, geser=geser_val, custom_angle_deg=custom_angle)
            pesan = (
                f"SUKSES!\n\n"
                f"• Tipe Data Input: {info['detected_type']}\n"
                f"• Total Tiang Dihasilkan: {info['num_piles']} kotak (1 kotak per tiang)\n"
                f"• Dimensi Kotak: {info['dimensi']}m x {info['dimensi']}m\n"
                f"• Sudut Rotasi: {info['sudut_deg']:.2f}° ({info['mode_sudut']})\n"
                f"• File Output: {out_file}\n\n"
                f"Format konektivitas: 1 1 1 1 0 + newline kosong (Anti Zig-Zag MIKE).\n"
                f"Klik OK untuk menampilkan grafik preview visual."
            )
            messagebox.showinfo("Proses Berhasil", pesan)
            visualisasi_plot(info, out_file)
        except Exception as e:
            messagebox.showerror("Gagal", f"Terjadi kesalahan saat memproses:\n{e}")

    root = tk.Tk()
    root.title("Universal Pile Generator - MIKE 21 (1 Kotak per Tiang)")
    root.geometry("580x350")
    root.resizable(False, False)

    lbl_title = tk.Label(root, text="Generator Kotak Tiang Pancang (Universal FIX)", font=("Arial", 11, "bold"))
    lbl_title.pack(pady=8)

    frm = tk.Frame(root, padx=15, pady=5)
    frm.pack(fill="both", expand=True)

    # Input
    tk.Label(frm, text="File Input XYZ:", anchor="w").grid(row=0, column=0, sticky="w", pady=4)
    entry_input = tk.Entry(frm, width=44)
    entry_input.grid(row=0, column=1, padx=5, pady=4)
    btn_browse_in = tk.Button(frm, text="Browse...", command=pilih_input, width=10)
    btn_browse_in.grid(row=0, column=2, padx=5, pady=4)

    # Status Label
    lbl_status = tk.Label(frm, text="Pilih file titik pusat pile atau file boundary lama", font=("Arial", 8, "italic"), fg="gray")
    lbl_status.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)

    # Output
    tk.Label(frm, text="File Output XYZ:", anchor="w").grid(row=2, column=0, sticky="w", pady=4)
    entry_output = tk.Entry(frm, width=44)
    entry_output.grid(row=2, column=1, padx=5, pady=4)
    btn_browse_out = tk.Button(frm, text="Browse...", command=pilih_output, width=10)
    btn_browse_out.grid(row=2, column=2, padx=5, pady=4)

    # Geser
    tk.Label(frm, text="Offset / Geser (m):", anchor="w").grid(row=3, column=0, sticky="w", pady=4)
    entry_geser = tk.Entry(frm, width=15)
    entry_geser.insert(0, "0.5")
    entry_geser.grid(row=3, column=1, sticky="w", padx=5, pady=4)
    tk.Label(frm, text="(0.5 = kotak 1m x 1m)", font=("Arial", 8, "italic"), fg="gray").grid(row=3, column=1, padx=(110, 0), sticky="w")

    # Sudut
    tk.Label(frm, text="Sudut Rotasi (Deg):", anchor="w").grid(row=4, column=0, sticky="w", pady=4)
    entry_sudut = tk.Entry(frm, width=15)
    entry_sudut.insert(0, "AUTO")
    entry_sudut.grid(row=4, column=1, sticky="w", padx=5, pady=4)
    tk.Label(frm, text="('AUTO' = deteksi otomatis)", font=("Arial", 8, "italic"), fg="gray").grid(row=4, column=1, padx=(110, 0), sticky="w")

    # Tombol Eksekusi
    btn_exec = tk.Button(root, text="PROSES SEKARANG & LIHAT PREVIEW VISUAL", command=aksi_proses, bg="#1E88E5", fg="white", font=("Arial", 10, "bold"), height=2)
    btn_exec.pack(fill="x", padx=25, pady=(5, 15))

    root.mainloop()


def jalankan_cli():
    """Eksekusi lewat terminal / command line."""
    import argparse
    parser = argparse.ArgumentParser(description="Universal Pile Boundary Generator (MIKE 21 / Mesh Generator)")
    parser.add_argument("input_file", help="Path file XYZ titik tiang pancang")
    parser.add_argument("output_file", nargs="?", default=None, help="Path file XYZ output boundary")
    parser.add_argument("--geser", type=float, default=0.5, help="Nilai geser setengah sisi kotak (default: 0.5 m)")
    parser.add_argument("--sudut", type=float, default=None, help="Sudut rotasi tiang dalam derajat (default: AUTO)")
    parser.add_argument("--no-plot", action="store_true", help="Jangan tampilkan plot grafik")

    args = parser.parse_args()
    in_file = args.input_file
    out_file = args.output_file
    if out_file is None:
        folder, fname = os.path.split(in_file)
        base, ext = os.path.splitext(fname)
        clean_base = base.replace("Boundary_", "").replace("_Final", "").replace("_Fixed", "")
        out_file = os.path.join(folder, f"Boundary_{clean_base}_1x1_FIX.xyz")

    print(f"\n[INFO] Membaca file input: {in_file}")
    info = hitung_kotak_pile(in_file, out_file, geser=args.geser, custom_angle_deg=args.sudut)
    print(f"[INFO] Tipe Data Terdeteksi: {info['detected_type']}")
    print(f"[SUKSES] Total {info['num_piles']} tiang berhasil diproses (1 kotak per tiang)!")
    print(f"[INFO] Dimensi Kotak: {info['dimensi']}m x {info['dimensi']}m")
    print(f"[INFO] Sudut Rotasi: {info['sudut_deg']:.2f}° ({info['mode_sudut']})")
    print(f"[INFO] Output tersimpan di: {out_file}")
    print(f"[INFO] Poligon tertutup rapat (konektivitas 1 1 1 1 0 + newline kosong, Bebas Zig-zag)\n")

    if not args.no_plot:
        visualisasi_plot(info, out_file)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        try:
            jalankan_gui()
        except Exception as e:
            print(f"[INFO] GUI Tkinter tidak dapat dibuka ({e}). Beralih ke bantuan CLI:")
            jalankan_cli()
    else:
        jalankan_cli()
