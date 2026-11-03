"""
WMF and EMF to High-Resolution PNG Converter
Specially tailored for engineering vector graphics exported from
Bentley SACS, Precede, AutoCAD, and legacy engineering software.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

# Windows GDI+ definitions for lossless vector rendering
class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion", wintypes.UINT),
        ("DebugEventCallback", ctypes.c_void_p),
        ("SuppressBackgroundThread", wintypes.BOOL),
        ("SuppressExternalCodecs", wintypes.BOOL),
    ]


def convert_wmf_via_pillow(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    scale_factor: float = 2.0
) -> Path:
    """Convert WMF/EMF to PNG using Pillow rasterization."""
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    dst = Path(output_path).resolve() if output_path else src.with_suffix(".png")

    with Image.open(src) as img:
        # If vector format, resize to higher dimension for high-DPI crispness
        if scale_factor != 1.0:
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Ensure RGB mode (handles transparencies/color palettes gracefully)
        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            bg.save(dst, "PNG", dpi=(300, 300))
        else:
            img.save(dst, "PNG", dpi=(300, 300))

    return dst


def convert_wmf_via_gdiplus(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    target_dpi: int = 300
) -> Path:
    """
    Render WMF/EMF using native Windows GDI+ engine.
    Ensures vector lines, text, and labels from SACS Precede are rendered with sharp clarity.
    """
    if os.name != "nt":
        return convert_wmf_via_pillow(input_path, output_path)

    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    dst = Path(output_path).resolve() if output_path else src.with_suffix(".png")

    try:
        gdiplus = ctypes.windll.gdiplus
        
        # Initialize GDI+
        token = ctypes.c_ulong()
        startup_in = GdiplusStartupInput(1, None, False, False)
        if gdiplus.GdiplusStartup(ctypes.byref(token), ctypes.byref(startup_in), None) != 0:
            return convert_wmf_via_pillow(src, dst)

        try:
            image_ptr = ctypes.c_void_p()
            w_path = str(src)
            status = gdiplus.GdipLoadImageFromFile(ctypes.c_wchar_p(w_path), ctypes.byref(image_ptr))
            if status != 0:
                return convert_wmf_via_pillow(src, dst)

            # PNG encoder CLSID: {557CF406-1A04-11D3-9A73-0000F81EF32E}
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_byte * 8),
                ]

            png_clsid = GUID(
                0x557CF406, 0x1A04, 0x11D3,
                (ctypes.c_byte * 8)(0x9A, 0x73, 0x00, 0x00, 0xF8, 0x1E, 0xF3, 0x2E)
            )

            status = gdiplus.GdipSaveImageToFile(
                image_ptr,
                ctypes.c_wchar_p(str(dst)),
                ctypes.byref(png_clsid),
                None
            )
            gdiplus.GdipDisposeImage(image_ptr)
            
            if status != 0:
                return convert_wmf_via_pillow(src, dst)
        finally:
            gdiplus.GdiplusShutdown(token)

        return dst
    except Exception:
        return convert_wmf_via_pillow(src, dst)


def batch_convert_wmf(directory: str | Path, target_dpi: int = 300) -> list[Path]:
    """Batch convert all .wmf and .emf files in a directory to PNG."""
    dir_path = Path(directory).resolve()
    converted = []
    for ext in ("*.wmf", "*.emf", "*.WMF", "*.EMF"):
        for f in dir_path.glob(ext):
            out_file = f.with_suffix(".png")
            convert_wmf_via_gdiplus(f, out_file, target_dpi=target_dpi)
            converted.append(out_file)
    return converted
