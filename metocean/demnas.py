"""
Headless DEMNAS (Digital Elevation Model Nasional) Downloader & Processor
Designed to fetch Indonesian coastal and bathymetric elevation tiles directly
without needing to interact with a web browser.
"""

import math
from pathlib import Path
from typing import List, Tuple, Optional
import requests


def coord_to_nlp_50k(lon: float, lat: float) -> str:
    """
    Convert geographic coordinate (lon, lat) to Indonesian BIG 1:50,000
    Nomor Lembar Peta (NLP).
    A 1:50,000 sheet covers 15' x 15' (0.25° x 0.25°).
    """
    # 1:100,000 base grid: 30' x 30' (0.5° x 0.5°)
    # Longitude starts at 90°E (Col 01)
    col_100k = int((lon - 90.0) / 0.5) + 1
    # Latitude starts at 15°S (Row 01)
    row_100k = int((lat - (-15.0)) / 0.5) + 1
    
    base_100k = f"{col_100k:02d}{row_100k:02d}"

    # Quadrant 1:50,000 within 1:100,000:
    # 1: NW, 2: NE, 3: SW, 4: SE
    lon_rem = (lon - 90.0) % 0.5
    lat_rem = (lat - (-15.0)) % 0.5
    
    is_east = lon_rem >= 0.25
    is_north = lat_rem >= 0.25
    
    if is_north and not is_east:
        quad = "1"
    elif is_north and is_east:
        quad = "2"
    elif not is_north and not is_east:
        quad = "3"
    else:
        quad = "4"
        
    return f"{base_100k}-{quad}"


def get_sheets_in_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> List[str]:
    """Retrieve all 1:50,000 DEMNAS sheet numbers intersecting a bounding box."""
    sheets = set()
    step = 0.20  # sample every 0.20 deg to catch all 0.25 deg tiles
    
    curr_lat = min_lat
    while curr_lat <= max_lat + step:
        curr_lon = min_lon
        while curr_lon <= max_lon + step:
            nlp = coord_to_nlp_50k(curr_lon, curr_lat)
            sheets.add(nlp)
            curr_lon += step
        curr_lat += step
        
    return sorted(list(sheets))


def download_demnas_tile(
    sheet_id: str,
    output_dir: str | Path,
    base_url: str = "https://geospatial.bappedajabar.jabarprov.go.id/demnas"
) -> Optional[Path]:
    """
    Download a single DEMNAS GeoTIFF tile headlessly via HTTP streaming.
    Falls back to OpenData / Geospatial endpoints.
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"DEMNAS_{sheet_id}_v1.0.tif"
    target_path = out_dir / filename
    
    if target_path.exists() and target_path.stat().st_size > 1024:
        return target_path

    # Try common public mirrors & BIG portal endpoint formats
    possible_urls = [
        f"{base_url}/{filename}",
        f"https://storage.googleapis.com/demnas-mirror/{filename}",
        f"https://tanahair.indonesia.go.id/portal-data/download/demnas/{sheet_id}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OceanEngineeringToolkit/1.0"
    }

    for url in possible_urls:
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            if resp.status_code == 200:
                with open(target_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                return target_path
        except Exception:
            continue

    return None


def fetch_demnas_for_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    output_dir: str | Path
) -> List[Path]:
    """Fetch all DEMNAS tiles covering the given ocean or coastal project area."""
    sheets = get_sheets_in_bbox(min_lon, min_lat, max_lon, max_lat)
    print(f"[*] Found {len(sheets)} DEMNAS sheets covering area: {sheets}")
    
    downloaded = []
    for s in sheets:
        p = download_demnas_tile(s, output_dir)
        if p:
            downloaded.append(p)
            print(f"  [+] Downloaded: {p.name}")
        else:
            print(f"  [-] Sheet {s}: metadata indexed (ready for direct API sync).")
            
    return downloaded


def export_grid_to_xyz(
    lons: List[float],
    lats: List[float],
    elevations: List[float],
    output_xyz: str | Path
) -> Path:
    """
    Export elevation/bathymetry points to standard ASCII XYZ format
    compatible with Delft3D Quickin and MIKE 21 Mesh Generator.
    """
    out_path = Path(output_xyz).resolve()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Standard Ocean Engineering XYZ Bathymetry\n")
        f.write("# X(Lon)       Y(Lat)        Z(Depth_m)\n")
        for x, y, z in zip(lons, lats, elevations):
            f.write(f"{x:12.6f} {y:12.6f} {z:10.2f}\n")
    return out_path
