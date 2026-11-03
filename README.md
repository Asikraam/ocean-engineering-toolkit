# Ocean Engineering Toolkit

A modular Python automation toolkit developed for ocean, coastal, and offshore engineering workflows. Eliminates repetitive manual tasks across structural modeling, hydrodynamic boundary setup, metocean reanalysis extraction, and report graphic preparation.

---

## Capabilities

| Domain | Module | Description |
| :--- | :--- | :--- |
| **Graphics & Reporting** | `converters` | High-DPI rasterization (300+ DPI) for SACS vector graphics (`.wmf`/`.emf`) and multi-page technical report PDFs (`.pdf` to `.png`). |
| **Metocean & Bathymetry** | `metocean` | Headless DEMNAS bathymetry tile fetcher via geographic bounding boxes, and automated ECMWF ERA5 wave/wind reanalysis extraction via Copernicus CDS API. |
| **Hydrodynamic Modeling** | `hydro` | Automated marine pile layouts, porous plate loss coefficient calculation, and boundary cards for Delft3D FLOW (`.thd`) and DHI MIKE 21 HD. |
| **Offshore Structures** | `sacs` | Strictly compliant 80-column fixed-format card generation (`sacinp.*`), parametric jacket geometry synthesis, and detached process launcher for Bentley SACS Executive & Precede. |

---

## Project Structure

```
ocean-engineering-toolkit/
├── converters/
│   ├── wmf_converter.py      # Windows GDI+ / Pillow vector to PNG rasterizer
│   └── pdf_converter.py      # High-performance PDFium multi-page renderer
├── metocean/
│   ├── demnas.py             # Headless BIG DEMNAS tile downloader & XYZ exporter
│   └── ecmwf_era5.py         # Copernicus CDS API automated wave & wind fetcher
├── hydro/
│   ├── delft3d_pile.py       # Thin dam & porous plate loss generator
│   └── mike21_pile.py        # MIKE 21 ASCII pile resistance card generator
├── sacs/
│   ├── cards.py              # 80-column card generator (JOINT, MEMBER, SECT)
│   └── runner.py             # Detached WMI launcher for Precede & SACS Executive
├── cli.py                    # Unified command-line interface
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Asikraam/ocean-engineering-toolkit.git
cd ocean-engineering-toolkit
pip install -r requirements.txt
```

---

## Command Line Usage

All core modules are accessible through the unified `cli.py` interface.

### 1. Convert SACS Precede Vector Graphics (.wmf) to PNG
Converts `.wmf` graphics exported from Bentley SACS Precede to crisp 300 DPI PNG images for Word or LaTeX reports:

```bash
# Single file
python cli.py wmf2png sacs_plot.wmf --dpi 300 -o sacs_plot.png

# Batch convert an entire directory of plots
python cli.py wmf2png ./sacs_plots/ --dpi 300
```

### 2. Convert Calculation Sheets & Drawings (PDF to PNG)
```bash
python cli.py pdf2png structural_drawing.pdf --dpi 300 -o ./output_images/
```

### 3. Headless DEMNAS Bathymetry Downloader
Downloads all Indonesian National Elevation (DEMNAS) tiles intersecting a bounding box (`min_lon min_lat max_lon max_lat`) without manual web browser navigation:

```bash
python cli.py demnas --bbox 106.6 -6.1 107.0 -5.8 -o ./demnas_tiles/
```

### 4. Fetch ECMWF ERA5 Ocean Wave & Wind Reanalysis
Pulls significant wave height ($H_s$), peak wave period ($T_p$), and 10-meter wind fields directly via CDS API:

```bash
python cli.py era5 --years 2023 --months 1 2 --bbox 5.0 95.0 -11.0 141.0 -o era5_waves.nc
```
*(Requires `~/.cdsapirc` Copernicus API key).*

### 5. Generate Delft3D Pile Structure & Equivalent Head Loss
Calculates pile coordinates and the equivalent quadratic energy loss coefficient ($c_{loss}$) for porous plates:

```bash
python cli.py delft-pile --nx 4 --ny 6 --dx 5.0 --dy 5.0 --dia 1.2 -o jetty_piles.csv
```

### 6. Generate SACS Parametric 3-Leg Tripod Jacket Input
Synthesizes a complete 80-column fixed-format `sacinp.tripod` model file:

```bash
python cli.py sacs-tripod --depth 45.0 --airgap 12.0 --base-rad 14.0 --top-rad 6.5 -o sacinp.tripod
```

### 7. Launch Bentley SACS Precede (Detached)
Opens 3D Precede safely via Windows WMI to prevent process termination:

```bash
python cli.py sacs-precede
```

---

## Python API Example

```python
from hydro import calculate_porous_loss_coefficient, generate_pile_group_layout
from sacs import build_tripod_jacket_sacinp

# 1. Compute hydrodynamic loss for a row of piles (D=1.2m, Spacing=4.8m)
loss_coeff = calculate_porous_loss_coefficient(diameter_m=1.2, spacing_m=4.8)
print(f"Delft3D Porous Plate Loss Coefficient: {loss_coeff}")

# 2. Build SACS 3-Leg Tripod Model
build_tripod_jacket_sacinp(
    base_radius_m=15.0,
    top_radius_m=7.0,
    water_depth_m=50.0,
    air_gap_m=14.0,
    output_path="sacinp.tripod"
)
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
