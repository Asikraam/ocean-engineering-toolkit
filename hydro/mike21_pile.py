"""
MIKE 21 Hydrodynamic Pile Resistance Automation
Generates structure and pile definition input cards for DHI MIKE 21 HD / SW simulations.
"""

from pathlib import Path
from typing import List
from .delft3d_pile import Pile


def generate_mike21_pile_input(
    piles: List[Pile],
    output_path: str | Path,
    vertical_datum_offset: float = 0.0
) -> Path:
    """
    Generates standard ASCII Pile Resistance input file for MIKE 21 Flow Model HD FM.
    Format includes pile ID, coordinates (X, Y), diameter, and drag coefficient (CD).
    """
    out_file = Path(output_path).resolve()
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("// MIKE 21 Hydrodynamic Pile Structure Specification\n")
        f.write(f"// Total Piles: {len(piles)}\n")
        f.write("// ID         X_Coordinate    Y_Coordinate    Diameter(m)    Drag_CD\n")
        
        for idx, p in enumerate(piles, start=1):
            f.write(f"{idx:6d}    {p.x:14.3f}    {p.y:14.3f}    {p.diameter_m:10.3f}    {p.drag_cd:8.3f}\n")
            
    return out_file
