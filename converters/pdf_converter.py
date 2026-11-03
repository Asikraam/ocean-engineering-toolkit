"""
High-Performance PDF to PNG Rasterizer
Converts engineering reports, calculation sheets, drawings, and bathymetry maps
from PDF into publication-ready PNG images (300+ DPI).
"""

from pathlib import Path
from typing import Optional, List
import pypdfium2 as pdfium


def convert_pdf_to_png(
    pdf_path: str | Path,
    output_dir: Optional[str | Path] = None,
    dpi: int = 300,
    prefix: Optional[str] = None,
    pages: Optional[List[int]] = None
) -> List[Path]:
    """
    Renders pages from a PDF file into high-resolution PNG images.

    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Destination folder. Defaults to same folder as PDF.
        dpi: Target resolution (default 300 DPI for crystal clear text/drawings).
        prefix: Filename prefix. Defaults to PDF stem.
        pages: Optional list of 0-indexed page numbers to convert. None converts all.

    Returns:
        List of Path objects for the saved PNG images.
    """
    src = Path(pdf_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"PDF file not found: {src}")

    out_folder = Path(output_dir).resolve() if output_dir else src.parent
    out_folder.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(src)
    scale = dpi / 72.0  # 72 points per inch standard

    total_pages = len(pdf)
    target_indices = pages if pages is not None else list(range(total_pages))
    base_name = prefix or src.stem

    saved_images = []
    for idx in target_indices:
        if idx < 0 or idx >= total_pages:
            continue
        page = pdf.get_page(idx)
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        
        out_file = out_folder / f"{base_name}_page_{idx + 1:03d}.png"
        pil_image.save(out_file, "PNG", dpi=(dpi, dpi))
        saved_images.append(out_file)

    return saved_images
