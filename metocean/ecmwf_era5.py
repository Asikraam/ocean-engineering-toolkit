"""
Headless ECMWF ERA5 Ocean & Atmospheric Reanalysis Downloader
Pulls hourly offshore wind and wave parameters using the Copernicus CDS API
without manual interaction or browser downloads.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import os


def verify_cds_credentials() -> bool:
    """Verify if the Copernicus CDS API key file (~/.cdsapirc) is configured."""
    home_rc = Path.home() / ".cdsapirc"
    env_url = os.environ.get("CDSAPI_URL")
    env_key = os.environ.get("CDSAPI_KEY")
    return home_rc.exists() or bool(env_url and env_key)


def create_sample_cdsapirc(url: str, key: str) -> Path:
    """Helper to initialize ~/.cdsapirc config file."""
    rc_path = Path.home() / ".cdsapirc"
    with open(rc_path, "w", encoding="utf-8") as f:
        f.write(f"url: {url.strip()}\n")
        f.write(f"key: {key.strip()}\n")
    return rc_path


def download_era5_waves_and_wind(
    years: List[int],
    months: List[int],
    days: List[int],
    hours: List[int],
    area_bbox: Tuple[float, float, float, float],  # (North, West, South, East)
    output_netcdf: str | Path,
    dataset: str = "reanalysis-era5-single-levels"
) -> Path:
    """
    Downloads offshore wave and wind fields from ECMWF ERA5 via CDS API.

    Parameters:
        years: List of target years (e.g., [2023])
        months: List of months (e.g., [1, 2, 3])
        days: List of days (e.g., list(range(1, 32)))
        hours: List of UTC hours (e.g., [0, 6, 12, 18])
        area_bbox: Bounding box tuple (North, West, South, East) in degrees
        output_netcdf: Target .nc file path
    """
    try:
        import cdsapi
    except ImportError:
        raise ImportError("Package 'cdsapi' is required. Install via: pip install cdsapi")

    if not verify_cds_credentials():
        raise PermissionError(
            "CDS credentials missing. Please create ~/.cdsapirc containing:\n"
            "url: https://cds.climate.copernicus.eu/api\n"
            "key: <YOUR-PERSONAL-CDS-API-KEY>"
        )

    out_file = Path(output_netcdf).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    c = cdsapi.Client()

    request_payload = {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "significant_height_of_combined_wind_waves_and_swell",
            "mean_wave_period",
            "peak_wave_period",
            "mean_wave_direction",
        ],
        "year": [str(y) for y in years],
        "month": [f"{m:02d}" for m in months],
        "day": [f"{d:02d}" for d in days],
        "time": [f"{h:02d}:00" for h in hours],
        "area": [
            area_bbox[0],  # North
            area_bbox[1],  # West
            area_bbox[2],  # South
            area_bbox[3],  # East
        ],
    }

    print(f"[*] Submitting ECMWF CDS request for area N:{area_bbox[0]} W:{area_bbox[1]} S:{area_bbox[2]} E:{area_bbox[3]}...")
    c.retrieve(dataset, request_payload, str(out_file))
    print(f"[+] Download complete: {out_file}")
    return out_file
