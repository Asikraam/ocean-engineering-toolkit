r"""
# Hydrodynamic Numerical Model Validation & Skill Metrics Engine

Computes quantitative accuracy and error metrics between numerical hydrodynamic model predictions (MIKE 21 / Delft3D) and in-situ field survey observations (ADCP current meter, tide gauges, wave buoys).

## Statistical Metrics Formulated
- **Mean Bias**: $\frac{1}{n} \sum (y_{sim} - y_{obs})$
- **Dimensional Error (MAE)**: $\text{MAE} = \frac{1}{n} \sum |y_{sim} - y_{obs}|$
- **Root Mean Square Error (RMSE)**: $\text{RMSE} = \sqrt{\frac{1}{n} \sum (y_{sim} - y_{obs})^2}$
- **Scatter Index (SI)**: $\text{SI} = \frac{\text{RMSE}}{\bar{y}_{obs}}$
- **Non-Dimensional Normalized Error**: $\text{Error}_{\%} = \frac{\text{MAE}}{R} \times 100\%$ (where $R$ is normalization range)
- **Correlation Coefficient ($R$ & $R^2$)**: Pearson product-moment linear correlation.
- **Nash-Sutcliffe Efficiency (NSE)**: Standard hydrological/hydrodynamic predictive skill score.

## Usage
```bash
python hydro/HydroModelValidation.py --input Data_Validation.xlsx
```

## Dependencies
```bash
pip install pandas numpy openpyxl
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np


def compute_skill_metrics(series_model, series_ref, r_normalization=None):
    valid_mask = ~(np.isnan(series_model) | np.isnan(series_ref))
    m = np.array(series_model)[valid_mask]
    o = np.array(series_ref)[valid_mask]
    n = len(m)

    if n == 0:
        return {}

    diff = m - o
    mae = np.mean(np.abs(diff))
    rmse = np.sqrt(np.mean(diff**2))
    bias = np.mean(diff)
    si = (rmse / np.mean(o)) if np.mean(o) != 0 else np.nan

    # Pearson Correlation R
    r_val = np.corrcoef(m, o)[0, 1] if n > 1 else np.nan

    # Nash-Sutcliffe Efficiency (NSE)
    var_o = np.sum((o - np.mean(o))**2)
    nse = 1.0 - (np.sum(diff**2) / var_o) if var_o != 0 else np.nan

    # Normalized error percentage
    r_norm = r_normalization if r_normalization else (np.max(o) - np.min(o))
    err_pct = (mae / r_norm) * 100.0 if r_norm and r_norm != 0 else np.nan

    return {
        "Count": n,
        "MAE": mae,
        "RMSE": rmse,
        "Bias": bias,
        "Scatter_Index": si,
        "Pearson_R": r_val,
        "R_Squared": r_val**2 if not np.isnan(r_val) else np.nan,
        "NSE": nse,
        "Normalized_Error_Pct": err_pct
    }


def main():
    parser = argparse.ArgumentParser(description="Hydrodynamic Model Skill Validation")
    parser.add_argument("--input", default="Data_Validation.xlsx", help="Path file data Excel validasi")
    parser.add_argument("--r-norm", type=float, default=None, help="Nilai referensi normalisasi (misal Tidal Range)")

    args = parser.parse_args()
    if not os.path.exists(args.input):
        print(f"Info: File '{args.input}' tidak ditemukan. Menampilkan formulasi rumus validasi modul.")
        return

    df = pd.read_excel(args.input)
    print("=" * 70)
    print("ANALISIS VALIDASI KINERJA SIMULASI NUMERIK MODEL HIDRO-OSEANOGRAFI")
    print("=" * 70)


if __name__ == "__main__":
    main()
