r"""
# QGIS Shapefile (.shp) to DHI MIKE Zero Land Boundary (.xyz) Converter

A PyQGIS script designed to extract boundary polyline/polygon nodes and export them to DHI MIKE 21 ASCII boundary format (`.xyz`) with sub-meter coordinate precision and standard connection codes ($1 = \text{connect}, 0 = \text{close}$).

## Usage (Inside QGIS)
1. Open your project in **QGIS Desktop**.
2. Select your shoreline / island polygon or line layer in the **Layers Panel**.
3. Open the **Python Console** (`Ctrl + Alt + P`).
4. Copy & paste this script or load it into the editor, customize the `OUTPUT_XYZ` path, and click **Run**.

## Output Specification
Standard MIKE Zero XYZ ASCII:
```text
  X_Coordinate   Y_Coordinate   Z_Value   Connectivity_Code
  325100.450     9115200.820    0.000     1
  325120.300     9115250.100    0.000     1
  325100.450     9115200.820    0.000     0
```

## Author
**Aswal Ikraam Aritonang** ([@Asikraam](https://github.com/Asikraam))
"""

import os

try:
    from qgis.core import QgsWkbTypes, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
    is_qgis_env = True
except ImportError:
    is_qgis_env = False


def export_active_layer_to_mike_xyz(output_xyz_path=None, target_epsg="EPSG:32752"):
    if not is_qgis_env:
        print("Peringatan: Modul ini didesain untuk dijalankan di dalam PyQGIS Console (QGIS Desktop).")
        return

    layer = iface.activeLayer()
    if not layer:
        print("Error: Harap pilih layer vektor di panel Layers QGIS terlebih dahulu!")
        return

    if not output_xyz_path:
        output_xyz_path = os.path.join(os.path.expanduser("~"), "Downloads", "Land_Boundary_MIKE.xyz")

    crs_sumber = layer.crs()
    crs_tujuan = QgsCoordinateReferenceSystem(target_epsg)
    transform = QgsCoordinateTransform(crs_sumber, crs_tujuan, QgsProject.instance())

    total_nodes = 0
    os.makedirs(os.path.dirname(os.path.abspath(output_xyz_path)), exist_ok=True)
    with open(output_xyz_path, "w", encoding="utf-8") as f:
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if not geom:
                continue

            geom.transform(transform)

            if geom.isMultipart():
                lines = geom.asMultiPolyline() if geom.type() == QgsWkbTypes.LineGeometry else geom.asMultiPolygon()
            else:
                lines = [geom.asPolyline()] if geom.type() == QgsWkbTypes.LineGeometry else [geom.asPolygon()]

            for line in lines:
                ring = line[0] if geom.type() == QgsWkbTypes.PolygonGeometry else line
                n_pts = len(ring)
                for idx, pt in enumerate(ring):
                    code = 0 if idx == (n_pts - 1) else 1
                    f.write(f"{pt.x():.6f} {pt.y():.6f} 0.000000 {code}\n")
                    total_nodes += 1

    print(f"[+] Berhasil mengekspor {total_nodes} titik simpul batas ke: {output_xyz_path}")


if __name__ == "__main__":
    export_active_layer_to_mike_xyz()
