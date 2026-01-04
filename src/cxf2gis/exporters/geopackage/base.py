import sqlite3
from pathlib import Path
import pandas as pd
from ..base import BaseExporter

class GPKGExporter(BaseExporter):
    def __init__(self, output_path):
        self.output_path = Path(output_path)

    def export(self, sources, target_epsg):
        """
        Crea un unico layer per ogni tipologia di entità (es. un unico layer 'bordo').
        """
        # Dizionario per accumulare i GeoDataFrame di tutte le sorgenti
        layers_to_merge = {
            'BORDO': [], 'TESTO': [], 'SIMBOLO': [], 
            'FIDUCIALE': [], 'LINEA': []
        }

        for src in sources:
            for l_name, gdf in src.layers.items():
                if gdf is not None and not gdf.empty:
                    # Riproiettiamo al volo al CRS di destinazione unico
                    gdf_transformed = gdf.to_crs(target_epsg)
                    layers_to_merge[l_name].append(gdf_transformed)

        # Per ogni tipo, uniamo i pezzi e scriviamo un solo layer nel GPKG
        for l_type, gdfs in layers_to_merge.items():
            if gdfs:
                # pandas.concat funziona perfettamente con i GeoDataFrame
                merged_gdf = pd.concat(gdfs, ignore_index=True)
                
                # Scrittura di un unico layer 'bordo', 'testo', ecc.
                merged_gdf.to_file(
                    self.output_path, 
                    layer=l_type.lower(), 
                    driver="GPKG",
                    engine="pyogrio" # Molto più veloce per file grandi
                )