r"""
# DHI MIKE 21 Pile & Trestle Generator Desktop GUI

Interactive desktop application for generating and configuring structural pile groups, piers, trestles, and jetty obstacles for **DHI MIKE 21 Flexible Mesh (FM)** modeling.

## Features
- **Visual Parametric Input**: Set pile section length, width, angle of incidence, and pile spacing.
- **Automated Geometry Transformation**: Rotates 4-corner boundary points matching jetty headings and structure azimuths.
- **Mesh-Ready ASCII Export**: Produces cleanly closed poligon boundaries (`.xyz`) ready for direct import into DHI MIKE Mesh Generator.
- **Real-Time Visual Verification**: Matplotlib 1:1 aspect-ratio plot preview ensures geometries are distortion-free before running simulations.

## Installation & Requirements
```bash
pip install -r requirements.txt
```
Dependencies: `matplotlib >= 3.8.0`

## How to Run
```bash
python hydro/MikePileGeneratorApp.py
```
Or via main toolkit CLI:
```bash
python cli.py mike-pile-gui
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import math
import matplotlib.pyplot as plt

def proses_file():
    # 1. Dialog Pilih File Input
    nama_file_input = filedialog.askopenfilename(
        title="Pilih file XYZ Input (Data Pile)",
        filetypes=(("XYZ Files", "*.xyz"), ("Text Files", "*.txt"), ("All Files", "*.*"))
    )
    if not nama_file_input:
        return # Batal pilih file

    # 2. Dialog Pilih Lokasi Save Output
    file_boundary = filedialog.asksaveasfilename(
        title="Simpan file Boundary",
        defaultextension=".xyz",
        filetypes=(("XYZ Files", "*.xyz"), ("All Files", "*.*"))
    )
    if not file_boundary:
        return # Batal save

    # 3. Baca Data Pile
    koordinat_pile = []
    try:
        with open(nama_file_input, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        koordinat_pile.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        continue 
    except Exception as e:
        messagebox.showerror("Error", f"Gagal baca file: {e}")
        return

    num_points = len(koordinat_pile)
    if num_points < 2:
        messagebox.showwarning("Warning", "Titik kurang dari 2, gagal ngitung.")
        return

    # ==========================================
    # LOGIKA PERHITUNGAN (Rotated Bounding Box)
    # ==========================================
    try:
        x1, y1 = koordinat_pile[0]
        # Pengecekan biar aman kalau file nya beda format jumlahnya
        idx_ujung = 15 if num_points > 15 else num_points - 1
        x_ujung, y_ujung = koordinat_pile[idx_ujung]

        # Hitung orientasi
        rad_orientation = math.atan2(y_ujung - y1, x_ujung - x1)
        rad_to_local = -rad_orientation 

        # Hitung center titik
        sum_x = sum(p[0] for p in koordinat_pile)
        sum_y = sum(p[1] for p in koordinat_pile)
        center_x = sum_x / num_points
        center_y = sum_y / num_points

        # Transformasi ke lokal
        local_coordinates = []
        cos_to_local = math.cos(rad_to_local)
        sin_to_local = math.sin(rad_to_local)

        for x, y in koordinat_pile:
            tx = x - center_x
            ty = y - center_y
            lx = tx * cos_to_local - ty * sin_to_local
            ly = tx * sin_to_local + ty * cos_to_local
            local_coordinates.append((lx, ly))

        # Cari Min/Max di lokal
        min_lx = min(p[0] for p in local_coordinates)
        max_lx = max(p[0] for p in local_coordinates)
        min_ly = min(p[1] for p in local_coordinates)
        max_ly = max(p[1] for p in local_coordinates)

        # Ambil nilai geser dari Input GUI
        g = float(entry_geser.get()) 

        # Tentukan 4 sudut lokal
        local_corners = [
            (min_lx - g, min_ly - g), 
            (max_lx + g, min_ly - g), 
            (max_lx + g, max_ly + g), 
            (min_lx - g, max_ly + g)  
        ]

        # Kembalikan sudut lokal ke global coordinate
        global_corners = []
        cos_from_local = math.cos(rad_orientation)
        sin_from_local = math.sin(rad_orientation)

        for lx, ly in local_corners:
            rx = lx * cos_from_local - ly * sin_from_local
            ry = lx * sin_from_local + ly * cos_from_local
            final_x = rx + center_x
            final_y = ry + center_y
            global_corners.append((final_x, final_y))

        # 4. Tulis file output
        with open(file_boundary, "w") as f_bound:
            x_ll, y_ll = global_corners[0]
            f_bound.write(f"{x_ll:.6f}\t{y_ll:.6f}\t0\t0\n") 
            
            for i in range(1, 4):
                x, y = global_corners[i]
                f_bound.write(f"{x:.6f}\t{y:.6f}\t0\t1\n") 
                
            f_bound.write(f"{x_ll:.6f}\t{y_ll:.6f}\t0\t1\n") 

    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan saat menghitung/menyimpan:\n{e}")
        return

    # ==========================================
    # VISUALISASI MATPLOTLIB (Buat Checking)
    # ==========================================
    # Render visualisasi geometri kotak tiang pancang
    plt.figure(figsize=(8, 6))
    
    # Plot Titik Pile (Merah)
    px = [p[0] for p in koordinat_pile]
    py = [p[1] for p in koordinat_pile]
    plt.scatter(px, py, color='red', label='Titik Pile (Data Input)', zorder=5, s=20)

    # Plot Boundary Box (Hijau)
    bx = [p[0] for p in global_corners]
    by = [p[1] for p in global_corners]
    # Tambahkan titik awal lagi di akhir biar poligonnya nutup di grafik
    bx.append(global_corners[0][0]) 
    by.append(global_corners[0][1])
    
    plt.plot(bx, by, color='green', linewidth=2, label=f'Boundary Box (Buffer {g}m)', zorder=4)

    # Setting Tampilan Grafik
    plt.title('Cek Visual: Rotated Bounding Box MOF')
    plt.xlabel('Koordinat X')
    plt.ylabel('Koordinat Y')
    plt.axis('equal') # Menjaga aspect ratio equal agar rasio visual 1:1 persegi tidak terdistorsi
    plt.grid(True, linestyle='--', color='blue', alpha=0.3)
    plt.legend()
    
    # Tampilkan notif sukses dulu, baru buka grafiknya
    messagebox.showinfo("Sukses", f"Perhitungan beres bro!\nData disimpen di:\n{file_boundary}\n\nKlik OK untuk melihat hasil visual plotnya.")
    plt.show()

# ==========================================
# SETUP UI / JENDELA GUI UTAMA
# ==========================================
root = tk.Tk()
root.title("Generator Boundary Box MOF")
root.geometry("350x150")

label_info = tk.Label(root, text="Masukkan Nilai Geser/Buffer (m):", font=("Arial", 10))
label_info.pack(pady=(15, 5))

entry_geser = tk.Entry(root, font=("Arial", 12), justify='center', width=10)
entry_geser.insert(0, "0.5") # Default value 0.5 meter
entry_geser.pack()

btn_proses = tk.Button(root, text="Pilih File XYZ & Proses", command=proses_file, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_proses.pack(pady=15)

# Jalanin program
root.mainloop()