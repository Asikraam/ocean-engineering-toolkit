"""
Bentley SACS Offshore 80-Column Card Generator
Strictly format-compliant card generator for SACS input models (sacinp.*).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SacsJoint:
    name: str        # Max 4 chars (cols 8-11)
    x: float         # cols 12-18 (F7.2 or F7.3)
    y: float         # cols 19-25 (F7.2 or F7.3)
    z: float         # cols 26-32 (F7.2 or F7.3)
    fixity: str = "" # cols 34-39 (e.g., '111111' for fixed base)

    def to_card(self) -> str:
        name_str = f"{self.name:>4}"[:4]
        x_str = f"{self.x:7.2f}"
        y_str = f"{self.y:7.2f}"
        z_str = f"{self.z:7.2f}"
        fix_str = f"{self.fixity:>6}"[:6] if self.fixity else "      "
        card = f"JOINT  {name_str}{x_str}{y_str}{z_str} {fix_str}"
        return card.ljust(80)


@dataclass
class SacsMember:
    joint_a: str     # cols 8-11
    joint_b: str     # cols 12-15
    group: str       # cols 17-19 (Max 3 chars)

    def to_card(self) -> str:
        ja = f"{self.joint_a:>4}"[:4]
        jb = f"{self.joint_b:>4}"[:4]
        grp = f"{self.group:>3}"[:3]
        card = f"MEMBER {ja}{jb} {grp}"
        return card.ljust(80)


@dataclass
class SacsTubularSection:
    group: str       # cols 8-10 (3 chars)
    outer_dia_cm: float  # Outer diameter in cm or inches
    wall_thk_cm: float   # Wall thickness in cm or inches

    def to_card(self) -> str:
        grp = f"{self.group:>3}"[:3]
        od_str = f"{self.outer_dia_cm:7.2f}"
        wt_str = f"{self.wall_thk_cm:7.3f}"
        card = f"SECT   {grp}  {od_str}{wt_str}"
        return card.ljust(80)


def build_tripod_jacket_sacinp(
    base_radius_m: float,
    top_radius_m: float,
    water_depth_m: float,
    air_gap_m: float,
    leg_od_cm: float = 120.0,
    leg_wt_cm: float = 3.5,
    output_path: str | Path = "sacinp.tripod"
) -> Path:
    """
    Generates a complete parametric 3-Leg Tripod Jacket SACS input file.
    """
    out_file = Path(output_path).resolve()
    import math

    z_mud = -water_depth_m
    z_top = air_gap_m
    
    joints: List[SacsJoint] = []
    # Bottom joints (mudline)
    for i, angle_deg in enumerate([0, 120, 240], start=1):
        rad = math.radians(angle_deg)
        jx = base_radius_m * math.cos(rad)
        jy = base_radius_m * math.sin(rad)
        joints.append(SacsJoint(name=f"10{i}", x=jx, y=jy, z=z_mud, fixity="111111"))

    # Top joints (deck connection)
    for i, angle_deg in enumerate([0, 120, 240], start=1):
        rad = math.radians(angle_deg)
        jx = top_radius_m * math.cos(rad)
        jy = top_radius_m * math.sin(rad)
        joints.append(SacsJoint(name=f"20{i}", x=jx, y=jy, z=z_top))

    members: List[SacsMember] = []
    # Main legs
    members.append(SacsMember(joint_a="101", joint_b="201", group="LEG"))
    members.append(SacsMember(joint_a="102", joint_b="202", group="LEG"))
    members.append(SacsMember(joint_a="103", joint_b="203", group="LEG"))

    # Top horizontals
    members.append(SacsMember(joint_a="201", joint_b="202", group="HOR"))
    members.append(SacsMember(joint_a="202", joint_b="203", group="HOR"))
    members.append(SacsMember(joint_a="203", joint_b="201", group="HOR"))

    # Mudline horizontals
    members.append(SacsMember(joint_a="101", joint_b="102", group="HOR"))
    members.append(SacsMember(joint_a="102", joint_b="103", group="HOR"))
    members.append(SacsMember(joint_a="103", joint_b="101", group="HOR"))

    sections = [
        SacsTubularSection(group="LEG", outer_dia_cm=leg_od_cm, wall_thk_cm=leg_wt_cm),
        SacsTubularSection(group="HOR", outer_dia_cm=leg_od_cm * 0.5, wall_thk_cm=leg_wt_cm * 0.5),
    ]

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("SACS 2025 PARAMETRIC TRIPOD JACKET AUTOMATION".ljust(80) + "\n")
        f.write("OPTIONS MN  CD     DY           YES                                     ".ljust(80) + "\n")
        f.write("LDOPT   METRIC                                                          ".ljust(80) + "\n")
        f.write("PGRP   LEG    STEEL                                                     ".ljust(80) + "\n")
        f.write("PGRP   HOR    STEEL                                                     ".ljust(80) + "\n")
        for s in sections:
            f.write(s.to_card() + "\n")
        for j in joints:
            f.write(j.to_card() + "\n")
        for m in members:
            f.write(m.to_card() + "\n")
        f.write("END                                                                             \n")

    return out_file
