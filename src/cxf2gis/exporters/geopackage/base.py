import os
import datetime
from pathlib import Path
from sqlalchemy import text
from sqlmodel import create_engine, select
from ..sql_common import MetadataManager, CXFMetadata

import sqlite3
import pandas as pd
from ..base import BaseExporter


class GeoPackageMetadataManager(MetadataManager):
    """
    Gestore metadati per GeoPackage. 
    In SQLite/GPKG la logica di 'schema' viene traslata sulla gestione del file fisico.
    -> https://gemini.google.com/share/34588b97d858
    """

    def __init__(self, engine, gpkg_path: str):
        super().__init__(engine, target_schema='main') # SQLite usa 'main' come schema predefinito
        self.gpkg_path = Path(gpkg_path)

    def __exit__(self, exc_type, exc_value, traceback):
        MetadataManager.__exit__(self, exc_type, exc_value, traceback)
        # Non disporre l'engine qui perché potrebbe essere riutilizzato dal chiamante
        # self.engine.dispose()

    def _set_description(self):
        """SQLite non supporta i commenti SQL standard come PostgreSQL."""
        pass
    
    def set_description(self):
        """Mantenuto per compatibilità, non esegue azioni su SQLite."""
        pass

    def _set_schema_description(self, file_names, file_date):
        """Mantenuto per compatibilità, i metadati sono salvati nella tabella CXFMetadata."""
        pass

    def _check_schema_exists(self):
        """Verifica se il file fisico esiste."""
        return self.gpkg_path.exists()

    def _check_table_exists(self):
        """Verifica l'esistenza della tabella metadati nel GeoPackage."""
        result = self.session.execute(text(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=:t"
        ), {"t": CXFMetadata.__tablename__}).scalar()
        return result > 0

    def _create_schema(self):
        """In SQLite il database (schema) viene creato all'apertura della connessione."""
        pass

    def _archive_schema(self):
        """
        Archiviazione tramite rinomina del file fisico.
        Chiude la sessione attiva per permettere al sistema operativo di rinominare il file.
        """
        archive_date = datetime.date.today().strftime("%Y_%m_%d")
        # Genera il nuovo nome: "nome_dati.gpkg" -> "nome_dati_archived_2024_01_01.gpkg"
        archive_path = self.gpkg_path.with_name(
            f"{self.gpkg_path.stem}_archived_{archive_date}{self.gpkg_path.suffix}"
        )

        print(f"Archiviazione file '{self.gpkg_path.name}' -> '{archive_path.name}'...")

        # Importante: Per rinominare un file SQLite/GPKG, non devono esserci connessioni attive
        # La sessione del MetadataManager deve essere gestita con attenzione
        if self.session:
            self.session.close()
        
        if archive_path.exists():
            archive_path.unlink()
            
        if self.gpkg_path.exists():
            self.gpkg_path.rename(archive_path)
            
        return str(archive_path)

    def _query_for_metadata(self):
        """Recupera il record unico di metadati per questo specifico GeoPackage."""
        statement = select(CXFMetadata)
        return statement

    def update_metadata(self, file_names: list, file_date: datetime.date):
        """
        Popola il record unico di metadati per questo specifico GeoPackage.
        """
        data = {
            "schema_name": self.gpkg_path.stem,
            "extraction_date": file_date,
            "source_filenames": ", ".join(file_names),
            "record_status": "production",
            "description": self.metadata_description
        }
        self._update_record(data)


class GPKGExporter(BaseExporter):
    """ TO DO """
    
    def __init__(self, output_path):
        # In SQLAlchemy 2.0 è buona norma usare l'URL di connessione esplicito
        self.output_path = Path(output_path)
        self.connection_url = f'sqlite:///{self.output_path}'
        self.engine = create_engine(self.connection_url)

    def prepare_schema(self):
            """
            Sostituisce la logica di 'prepare_schema' di PostGIS.
            Gestisce l'archiviazione del file esistente e la creazione del nuovo.
            """
            with GeoPackageMetadataManager(self.engine, self.output_path) as metadata_manager:
            
                # 1. Verifica se il file esiste già
                if metadata_manager._check_schema_exists():
                    
                    # 2. Verifica sicurezza: esiste la tabella metadati?
                    # Se il file esiste ma non ha i metadati CXF, per sicurezza non lo tocchiamo
                    if not metadata_manager._check_table_exists():
                        raise RuntimeError(
                            f"SICUREZZA: Il file '{self.output_path.name}' esiste ma non è gestito da CXF2GIS. "
                            "Operazione annullata per evitare sovrascritture accidentali."
                        )
                    
                    # 3. Archiviazione: rinomina il file esistente (es. dati.gpkg -> dati_archived_2024_01_01.gpkg)
                    # Il metodo _archive_schema gestisce internamente la chiusura della sessione
                    metadata_manager._archive_schema()

                # 4. Setup del nuovo database (crea tabelle metadati e estensioni GPKG se necessario)
                # Nota: SQLite crea il file automaticamente alla prima connessione/operazione
                # metadata_manager.setup_database()
                # metadata_manager.session.commit()
            pass
    
    def export(self, project, target_epsg):
        """
        Esegue l'integrazione dei sorgenti e la scrittura nel GeoPackage.
        """
        # Recupero info dai file sorgenti tramite la classe base
        file_date, file_names = self._get_file_info(project)
        
        # Preparazione dell'output (archiviazione eventuale file precedente)
        self.prepare_schema()

        # 1. Ciclo sui layer processati dalla logica comune di merge
        for table_name, merged_gdf in self._merge_sources(project.sources, target_epsg):
            print(f"Scrittura layer GeoPackage: {table_name} -> {self.output_path.name}")
            
            # 2. Scrittura del GeoDataFrame come layer del file GPKG
            # Usiamo to_file con driver GPKG, che è lo standard per GeoPandas
            # mode='a' (append) previene la ricreazione del file, preservando le tabelle esistenti (es. cxf_metadata)
            merged_gdf.to_file(
                self.output_path, 
                layer=table_name, 
                driver="GPKG", 
                engine="pyogrio",  # Consigliato per performance se disponibile
                mode='a'  # Append mode: non ricrea il file, aggiunge solo il layer
            )

        with GeoPackageMetadataManager(self.engine, self.output_path) as metadata_manager:
            metadata_manager.setup_database()
            metadata_manager.session.commit()
        # 3. Aggiornamento dei metadati nel file appena creato
        # Nota: Usiamo il context manager per garantire il commit della sessione
        self.engine = create_engine(self.connection_url)  # Riapriamo l'engine per sicurezza
        with GeoPackageMetadataManager(self.engine, self.output_path) as metadata_manager:
            metadata_manager._update_record({
                "schema_name": self.output_path.stem,
                "extraction_date": file_date,
                "source_filenames": ", ".join(file_names),
                "record_status": "production",
                "description": f"Export GPKG - {len(project.sources)} sorgenti"
            })
            # Metodi mantenuti per compatibilità con l'interfaccia PostGIS
            # metadata_manager.set_description()
        pass