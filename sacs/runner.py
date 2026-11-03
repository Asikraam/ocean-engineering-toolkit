"""
Bentley SACS Offshore Process Runner & Modeler Launcher
Implements detached WMI launching protocols to ensure Precede and SACS Executive
stay alive without being auto-terminated by command job-objects.
"""

import subprocess
import os
from pathlib import Path


SACS_DIR = Path(r"C:\Program Files\Bentley\Offshore\SACS 2025")
PRECEDE_EXE = SACS_DIR / "Precede.exe"
EXECUTIVE_EXE = SACS_DIR / "SACSExecutive.exe"


def launch_precede_detached() -> bool:
    """Launch SACS Precede (3D Modeler) detached via PowerShell WMI."""
    if not PRECEDE_EXE.exists():
        print(f"[-] Precede not found at {PRECEDE_EXE}")
        return False

    cmd = f"""
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{
        CommandLine = '"{PRECEDE_EXE}"'
        CurrentDirectory = "{SACS_DIR}"
    }}
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return res.returncode == 0


def launch_sacs_executive_detached() -> bool:
    """Launch SACS Executive detached via PowerShell WMI."""
    if not EXECUTIVE_EXE.exists():
        print(f"[-] SACS Executive not found at {EXECUTIVE_EXE}")
        return False

    cmd = f"""
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{
        CommandLine = '"{EXECUTIVE_EXE}"'
        CurrentDirectory = "{SACS_DIR}"
    }}
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return res.returncode == 0
