"""
Delft3D Flow & Wave Structure Automation
Generates thin dam (.thd), dry point (.dep), and porous plate definitions
for representing pile groups (jetty piles, jacket legs, dolphins) in Delft3D meshes.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import math


@dataclass
class Pile:
    name: str
    x: float
    y: float
    diameter_m: float
    drag_cd: float = 1.0


def calculate_porous_loss_coefficient(diameter_m: float, spacing_m: float) -> float:
    """
    Computes the hydrodynamic quadratic energy head loss coefficient (c_loss)
    for a row of piles acting as a porous plate in Delft3D:
        c_loss = ((1 / (1 - D/S)) - 1)^2
    """
    if spacing_m <= diameter_m:
        raise ValueError(f"Pile spacing ({spacing_m}m) must be greater than diameter ({diameter_m}m)")
    
    porosity = 1.0 - (diameter_m / spacing_m)
    c_loss = ((1.0 / porosity) - 1.0) ** 2
    return round(c_loss, 4)


def generate_delft3d_thindam(
    segments: List[Tuple[int, int, int, int, str]],
    output_path: str | Path
) -> Path:
    """
    Generate Delft3D Thin Dam (.thd) file.

    Parameters:
        segments: List of tuples (M1, N1, M2, N2, direction) where direction is 'U' or 'V'.
        output_path: Destination .thd file path.
    """
    out_file = Path(output_path).resolve()
    with open(out_file, "w", encoding="utf-8") as f:
        for seg in segments:
            m1, n1, m2, n2, uv = seg
            f.write(f"{m1:5d}{n1:5d}{m2:5d}{n2:5d} '{uv.upper()}'\n")
    return out_file


def generate_pile_group_layout(
    origin_x: float,
    origin_y: float,
    nx: int,
    ny: int,
    dx: float,
    dy: float,
    diameter_m: float,
    prefix: str = "P"
) -> List[Pile]:
    """
    Generates a regular grid layout of marine piles (e.g. offshore platform or jetty foundation).
    """
    piles = []
    idx = 1
    for i in range(nx):
        for j in range(ny):
            px = origin_x + i * dx
            py = origin_y + j * dy
            piles.append(Pile(
                name=f"{prefix}_{idx:03d}",
                x=round(px, 3),
                y=round(py, 3),
                diameter_m=diameter_m
            ))
            idx += 1
    return piles


def export_piles_to_csv(piles: List[Pile], output_csv: str | Path) -> Path:
    """Exports pile list to CSV for GIS / Delft3D coordinate referencing."""
    out_path = Path(output_csv).resolve()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("pile_name,x_coord,y_coord,diameter_m,drag_cd\n")
        for p in piles:
            f.write(f"{p.name},{p.x},{p.y},{p.diameter_m},{p.drag_cd}\n")
    return out_path
