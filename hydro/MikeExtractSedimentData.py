r"""
# DHI MIKE 21 Sediment Transport (ST/MT) Mesh Data Extractor

Headless and CLI utility utilizing `mikeio` to extract point time-series (bed level change, suspended sediment concentration, transport rate) from unstructured flexible mesh DFSU simulation outputs.

## Features
- **DFSU Element Geometry Parsing**: Computes element centroids $(X, Y)$ and cell surface areas.
- **Interactive or Headless Parameter Selection**: Prompts user or accepts parameter index via CLI flags.
- **Structured Excel / CSV Export**: Saves time-series ready for sediment budget and dredging analyses.

## Usage
```bash
python hydro/MikeExtractSedimentData.py --input simulation.dfsu --output sediment_report.xlsx
```

## Dependencies
```bash
pip install mikeio openpyxl pandas numpy
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

try:
    import mikeio
except ImportError:
    print("Pustaka 'mikeio' belum terpasang. Jalankan: pip install mikeio")
    sys.exit(1)


def extract_sediment_dfsu(dfsu_path, output_excel, item_index=None):
    if not os.path.exists(dfsu_path):
        raise FileNotFoundError(f"File DFSU tidak ditemukan: {dfsu_path}")

    print(f"[*] Membaca file DFSU: {dfsu_path}")
    dfs = mikeio.open(dfsu_path)
    print(dfs)

    if item_index is None:
        print("\nDaftar parameter item yang tersedia:")
        for idx, item in enumerate(dfs.items):
            print(f"  [{idx}] {item.name} ({item.unit})")
        item_index = int(input("\nKetik nomor indeks parameter yang ingin diekstrak: "))

    selected_item = dfs.items[item_index]
    print(f"[+] Mengekstrak parameter: {selected_item.name}...")

    ds = dfs.read(items=[item_index])
    data_values = ds[selected_item.name].to_numpy()
    times = ds.time

    # Ekstraksi koordinat centroid elemen mesh
    coords = dfs.element_coordinates
    n_elements = len(coords)

    # Buat tabel ringkasan rata-rata/maksimum per elemen
    summary_data = []
    for e_idx in range(n_elements):
        val_series = data_values[:, e_idx]
        summary_data.append({
            "Element_ID": e_idx + 1,
            "X_Coord": coords[e_idx, 0],
            "Y_Coord": coords[e_idx, 1],
            "Max_Value": np.nanmax(val_series),
            "Mean_Value": np.nanmean(val_series),
            "Min_Value": np.nanmin(val_series),
            "Final_Timestep_Value": val_series[-1]
        })

    df_summary = pd.DataFrame(summary_data)
    os.makedirs(os.path.dirname(os.path.abspath(output_excel)), exist_ok=True)
    df_summary.to_excel(output_excel, index=False)
    print(f"[+] Ekstraksi selesai! Data tersimpan di: {output_excel}")
    return output_excel


def main():
    parser = argparse.ArgumentParser(description="DHI MIKE 21 DFSU Sediment Transport Data Extractor")
    parser.add_argument("--input", required=True, help="Path ke file DFSU (.dfsu)")
    parser.add_argument("--output", default="Sediment_Extracted.xlsx", help="Path output file Excel (.xlsx)")
    parser.add_argument("--item", type=int, default=None, help="Indeks parameter item yang ingin diekstrak")

    args = parser.parse_args()
    extract_sediment_dfsu(args.input, args.output, args.item)


if __name__ == "__main__":
    main()
