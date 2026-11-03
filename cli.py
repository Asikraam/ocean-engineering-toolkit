#!/usr/bin/env python3
"""
Ocean Engineering Toolkit - Command Line Interface (CLI)
Automating Bentley SACS, Delft3D/MIKE 21 Structures, Metocean Fetchers, and Graphic Converters.
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Ocean Engineering Toolkit - Automation Suite for Marine & Offshore Engineers"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. wmf2png
    p_wmf = subparsers.add_parser("wmf2png", help="Convert SACS WMF/EMF vector graphics to high-DPI PNG")
    p_wmf.add_argument("input", help="Path to .wmf/.emf file or directory of files")
    p_wmf.add_argument("-o", "--output", help="Output PNG path or directory", default=None)
    p_wmf.add_argument("--dpi", type=int, default=300, help="Target DPI resolution (default: 300)")

    # 2. pdf2png
    p_pdf = subparsers.add_parser("pdf2png", help="Render PDF engineering drawings/reports to crisp PNG")
    p_pdf.add_argument("input", help="Path to PDF file")
    p_pdf.add_argument("-o", "--output-dir", help="Output directory for PNG pages", default=None)
    p_pdf.add_argument("--dpi", type=int, default=300, help="Target DPI (default: 300)")

    # 3. demnas
    p_dem = subparsers.add_parser("demnas", help="Headless Indonesian DEMNAS tile fetcher via BBox")
    p_dem.add_argument("--bbox", nargs=4, type=float, required=True,
                       metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
                       help="Bounding box: min_lon min_lat max_lon max_lat (e.g. 106.5 -6.2 107.0 -5.8)")
    p_dem.add_argument("-o", "--output-dir", default="./demnas_tiles", help="Output folder for GeoTIFF tiles")

    # 4. era5
    p_era = subparsers.add_parser("era5", help="ECMWF ERA5 ocean wave & wind reanalysis downloader")
    p_era.add_argument("--years", nargs="+", type=int, default=[2023], help="Target years")
    p_era.add_argument("--months", nargs="+", type=int, default=[1], help="Target months (1-12)")
    p_era.add_argument("--bbox", nargs=4, type=float, required=True,
                       metavar=("NORTH", "WEST", "SOUTH", "EAST"),
                       help="Area bounding box (N W S E)")
    p_era.add_argument("-o", "--output", default="era5_waves.nc", help="Output NetCDF file path")

    # 5. delft-pile
    p_dpile = subparsers.add_parser("delft-pile", help="Generate Delft3D pile group layout & porous loss")
    p_dpile.add_argument("--nx", type=int, default=3, help="Number of piles in X direction")
    p_dpile.add_argument("--ny", type=int, default=4, help="Number of piles in Y direction")
    p_dpile.add_argument("--dx", type=float, default=6.0, help="Pile spacing in X (m)")
    p_dpile.add_argument("--dy", type=float, default=6.0, help="Pile spacing in Y (m)")
    p_dpile.add_argument("--dia", type=float, default=1.2, help="Pile outer diameter (m)")
    p_dpile.add_argument("-o", "--output", default="piles.csv", help="Output CSV path")

    # 6. mike-pile
    p_mpile = subparsers.add_parser("mike-pile", help="Generate MIKE 21 ASCII pile resistance specification")
    p_mpile.add_argument("--dia", type=float, default=1.2, help="Pile diameter (m)")
    p_mpile.add_argument("--cd", type=float, default=1.0, help="Drag coefficient Cd")
    p_mpile.add_argument("-o", "--output", default="mike21_piles.txt", help="Output ASCII file")

    # 7. sacs-tripod
    p_tripod = subparsers.add_parser("sacs-tripod", help="Generate parametric 3-Leg Tripod Jacket SACS input file")
    p_tripod.add_argument("--depth", type=float, default=45.0, help="Water depth (m)")
    p_tripod.add_argument("--airgap", type=float, default=12.0, help="Air gap to topside deck (m)")
    p_tripod.add_argument("--base-rad", type=float, default=14.0, help="Base mudline footprint radius (m)")
    p_tripod.add_argument("--top-rad", type=float, default=6.5, help="Top deck footprint radius (m)")
    p_tripod.add_argument("-o", "--output", default="sacinp.tripod", help="Output SACS input file")

    # 8. sacs-precede
    p_precede = subparsers.add_parser("sacs-precede", help="Launch SACS Precede 3D modeler safely detached")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "wmf2png":
        from converters import convert_wmf_via_gdiplus, batch_convert_wmf
        target = Path(args.input)
        if target.is_dir():
            res = batch_convert_wmf(target, target_dpi=args.dpi)
            print(f"[+] Converted {len(res)} files in {target}")
        else:
            out = convert_wmf_via_gdiplus(target, args.output, target_dpi=args.dpi)
            print(f"[+] Converted: {out}")

    elif args.command == "pdf2png":
        from converters import convert_pdf_to_png
        res = convert_pdf_to_png(args.input, output_dir=args.output_dir, dpi=args.dpi)
        print(f"[+] Rendered {len(res)} pages from {args.input}")

    elif args.command == "demnas":
        from metocean import fetch_demnas_for_bbox
        min_lon, min_lat, max_lon, max_lat = args.bbox
        res = fetch_demnas_for_bbox(min_lon, min_lat, max_lon, max_lat, args.output_dir)
        print(f"[+] Completed DEMNAS fetch task. Output directory: {args.output_dir}")

    elif args.command == "era5":
        from metocean import download_era5_waves_and_wind
        n, w, s, e = args.bbox
        download_era5_waves_and_wind(
            years=args.years,
            months=args.months,
            days=list(range(1, 32)),
            hours=[0, 6, 12, 18],
            area_bbox=(n, w, s, e),
            output_netcdf=args.output
        )

    elif args.command == "delft-pile":
        from hydro import generate_pile_group_layout, export_piles_to_csv, calculate_porous_loss_coefficient
        piles = generate_pile_group_layout(0.0, 0.0, args.nx, args.ny, args.dx, args.dy, args.dia)
        export_piles_to_csv(piles, args.output)
        loss = calculate_porous_loss_coefficient(args.dia, args.dx)
        print(f"[+] Generated {len(piles)} piles saved to: {args.output}")
        print(f"[*] Equivalent Delft3D porous plate loss coefficient (c_loss): {loss}")

    elif args.command == "mike-pile":
        from hydro import generate_pile_group_layout, generate_mike21_pile_input
        piles = generate_pile_group_layout(0.0, 0.0, 4, 4, 5.0, 5.0, args.dia)
        for p in piles:
            p.drag_cd = args.cd
        out = generate_mike21_pile_input(piles, args.output)
        print(f"[+] MIKE 21 pile input generated: {out}")

    elif args.command == "sacs-tripod":
        from sacs import build_tripod_jacket_sacinp
        out = build_tripod_jacket_sacinp(
            base_radius_m=args.base_rad,
            top_radius_m=args.top_rad,
            water_depth_m=args.depth,
            air_gap_m=args.airgap,
            output_path=args.output
        )
        print(f"[+] Generated SACS input model: {out}")

    elif args.command == "sacs-precede":
        from sacs import launch_precede_detached
        if launch_precede_detached():
            print("[+] SACS Precede launched successfully in detached mode.")
        else:
            print("[-] Could not launch Precede.")


if __name__ == "__main__":
    main()
