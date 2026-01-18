import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

class BaseExporter:

    def _get_file_info(self, project):
        file_paths = [Path(src.file_path) for src in project.sources if hasattr(src, 'file_path')]
        if not file_paths:
            return datetime.date.today(), ["unknown_source"]
        
        mtime = max([p.stat().st_mtime for p in file_paths])
        file_date = datetime.datetime.fromtimestamp(mtime).date()
        file_names = [p.name for p in file_paths]
        return file_date, file_names

    def export(self, sources, target_epsg):
        raise NotImplementedError
    
    # 3. Logica di Merge e Riproiezione (come la tua versione originale)
    def _merge_sources(self, sources, target_epsg):
        layers_to_merge = {k: [] for k in ['BORDO', 'TESTO', 'SIMBOLO', 'FIDUCIALE', 'LINEA']}
        for src in sources:
            for l_name, gdf in src.layers.items():
                if gdf is not None and not gdf.empty:
                    if gdf.crs==target_epsg:
                        gdf_transformed = gdf
                    else:
                        gdf_transformed = gdf.to_crs(target_epsg)
                    layers_to_merge[l_name.upper()].append(gdf_transformed)

        # 4. Scrittura nuovi layer nel nuovo file
        for l_type, gdfs in layers_to_merge.items():
            if gdfs:
                merged_gdf = pd.concat(gdfs, ignore_index=True)
                table_name = l_type.lower()
                yield table_name, merged_gdf