r"""
# AutoCAD DXF to DHI MIKE 21 XYZ Land & Structure Boundary Converter

Converts AutoCAD drawing entities (`LINE`, `POLYLINE`, `LWPOLYLINE`, `POINT`) from DXF files into ASCII XYZ coordinates formatted for DHI MIKE Mesh Generator.

## Features
- **Entity Extraction**: Parses 2D/3D polyline vertices, standalone lines, and boundary contours.
- **Layer Filtering**: Extract specific layers (e.g. shoreline, revetment, jetty) or entire drawing geometries.
- **MIKE-Ready Output**: Writes standard XYZ space-delimited text files.

## Usage
```bash
python hydro/CadDxfToXyz.py --input drawing.dxf --output boundary.xyz
```

## Dependencies
```bash
pip install ezdxf
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import argparse

try:
    import ezdxf
except ImportError:
    print("Pustaka 'ezdxf' belum terpasang. Jalankan: pip install ezdxf")
    sys.exit(1)


def convert_dxf_to_xyz(dxf_path, output_xyz, target_layer=None):
    if not os.path.exists(dxf_path):
        raise FileNotFoundError(f"File DXF tidak ditemukan: {dxf_path}")

    print(f"[*] Membaca file DXF: {dxf_path}")
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    points = []
    for e in msp:
        if target_layer and e.dxf.layer.lower() != target_layer.lower():
            continue

        if e.dxftype() == "LINE":
            points.append((e.dxf.start.x, e.dxf.start.y, getattr(e.dxf.start, "z", 0.0)))
            points.append((e.dxf.end.x, e.dxf.end.y, getattr(e.dxf.end, "z", 0.0)))
        elif e.dxftype() in ("POLYLINE", "LWPOLYLINE"):
            for p in e.get_points():
                points.append((p[0], p[1], p[2] if len(p) > 2 else 0.0))
        elif e.dxftype() == "POINT":
            points.append((e.dxf.location.x, e.dxf.location.y, getattr(e.dxf.location, "z", 0.0)))

    os.makedirs(os.path.dirname(os.path.abspath(output_xyz)), exist_ok=True)
    with open(output_xyz, "w", encoding="utf-8") as f:
        for pt in points:
            f.write(f"{pt[0]:.6f} {pt[1]:.6f} {pt[2]:.6f}\n")

    print(f"[+] Berhasil mengekstrak {len(points)} koordinat titik ke: {output_xyz}")
    return output_xyz


def main():
    parser = argparse.ArgumentParser(description="AutoCAD DXF to DHI MIKE XYZ Converter")
    parser.add_argument("--input", required=True, help="Path ke file DXF input (.dxf)")
    parser.add_argument("--output", default="output_boundary.xyz", help="Path file output (.xyz)")
    parser.add_argument("--layer", default=None, help="Nama layer spesifik (opsional)")

    args = parser.parse_args()
    convert_dxf_to_xyz(args.input, args.output, args.layer)


if __name__ == "__main__":
    main()
