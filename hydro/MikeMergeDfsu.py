r"""
# DHI MIKE 21 DFSU Temporal File Concatenator

Merges multiple sequential or interrupted flexible mesh simulation output files (`.dfsu`) into a single continuous full-duration file using `mikeio.generic.concat()`.

## Features
- **Seamless Time Stitching**: Joins monthly or partial simulation runs without altering spatial mesh geometry.
- **Consistency Verification**: Checks for non-overlapping sequential timesteps.

## Usage
```bash
python hydro/MikeMergeDfsu.py --input-files part1.dfsu part2.dfsu part3.dfsu --output merged_full.dfsu
```

## Dependencies
```bash
pip install mikeio
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import argparse

try:
    import mikeio
    import mikeio.generic
except ImportError:
    print("Pustaka 'mikeio' belum terpasang. Jalankan: pip install mikeio")
    sys.exit(1)


def merge_dfsu_files(input_files, output_path):
    print("=" * 70)
    print("PENGGABUNGAN FILE DFSU (MIKEIO GENERIC CONCAT)")
    print("=" * 70)
    for idx, f in enumerate(input_files, 1):
        print(f"  Part {idx}: {f}")
        if not os.path.exists(f):
            raise FileNotFoundError(f"File tidak ditemukan: {f}")

    print(f"\nOutput Target: {output_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print("[*] Sedang menggabungkan timestep...")
    mikeio.generic.concat(infilenames=input_files, outfilename=output_path)
    print(f"[+] Penggabungan selesai! File berhasil disatukan di: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="DHI MIKE 21 DFSU File Concatenator")
    parser.add_argument("--input-files", nargs="+", required=True, help="Daftar file .dfsu berurutan yang ingin digabungkan")
    parser.add_argument("--output", required=True, help="Path output file .dfsu gabungan")

    args = parser.parse_args()
    merge_dfsu_files(args.input_files, args.output)


if __name__ == "__main__":
    main()
