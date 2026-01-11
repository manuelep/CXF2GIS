import os
import sqlite3
import datetime
import pandas as pd
from pathlib import Path
from ..base import BaseExporter

class GPKGExporter(BaseExporter):
    def __init__(self, output_path):
        """
        output_path: percorso del file principale (es. 'dati/catasto.gpkg')
        """
        self.output_path = Path(output_path)

    def _write_internal_metadata(self, file_date, file_names, desc):
        """Scrive la tabella dei metadati all'interno del file GeoPackage."""
        with sqlite3.connect(self.output_path) as conn:
            cursor = conn.cursor()
            # Crea la tabella se non esiste
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cxf_metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1), -- Garantisce record unico
                    data_estrazione TEXT,
                    data_import TEXT,
                    fonti_files TEXT,
                    stato TEXT,
                    descrizione TEXT
                )
            """)
            
            # Inserisce o aggiorna l'unico record di metadati
            cursor.execute("""
                INSERT OR REPLACE INTO cxf_metadata (id, data_estrazione, data_import, fonti_files, stato, descrizione)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (
                file_date.isoformat(),
                datetime.datetime.now().isoformat(),
                ", ".join(file_names),
                "production",
                desc
            ))
            conn.commit()

    def export(self, sources, target_epsg):
        # 1. Recupero informazioni dai file sorgente
        file_paths = [Path(s.filepath) for s in sources if hasattr(s, 'filepath')]
        file_names = [p.name for p in file_paths]
        # Data di estrazione (max tra i file CXF)
        mtime = max([p.stat().st_mtime for p in file_paths]) if file_paths else datetime.datetime.now().timestamp()
        file_date = datetime.datetime.fromtimestamp(mtime).date()

        # 2. Gestione Archiviazione del file esistente
        if self.output_path.exists():
            # Recuperiamo la data dal vecchio file per la rinomina
            old_mtime = self.output_path.stat().st_mtime
            old_date_str = datetime.datetime.fromtimestamp(old_mtime).strftime("%Y-%m-%d")
            
            # Costruiamo il nome dell'archivio: catasto-archived-2024-05-20.gpkg
            archive_name = self.output_path.stem + f"-archived-{old_date_str}" + self.output_path.suffix
            archive_path = self.output_path.parent / archive_name
            
            print(f"Archiviazione file esistente in: {archive_path}")
            
            # Se l'archivio esiste già, lo rimuoviamo o lo sovrascriviamo
            if archive_path.exists():
                archive_path.unlink()
            
            # Rinomina fisica
            self.output_path.rename(archive_path)
            
            # Aggiornamento dello stato nel file appena archiviato
            with sqlite3.connect(archive_path) as conn:
                conn.execute("UPDATE cxf_metadata SET stato = 'archived' WHERE id = 1")
                conn.commit()

        for table_name, merged_gdf in self._merge_sources(sources, target_epsg):
            # Scrittura nuovi layer nel nuovo file
            merged_gdf.to_file(
                self.output_path, 
                layer=table_name, 
                driver="GPKG",
                engine="pyogrio"
            )

        # 5. Scrittura Metadati Interni
        desc = f"Esportazione catastale prodotta da CXF2GIS"
        self._write_internal_metadata(file_date, file_names, desc)
        print(f"Esportazione completata: {self.output_path}")