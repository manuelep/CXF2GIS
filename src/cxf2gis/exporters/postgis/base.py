import os
import datetime
from pathlib import Path
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from sqlmodel import Session
from ..base import BaseExporter
from ..sql_common import MetadataManager, CXFMetadata


class PostGISMetadataManager(MetadataManager):
    """ """

    def _set_description(self):
        self.session.execute(
            text(f"COMMENT ON TABLE {CXFMetadata.__tablename__} IS :msg;"),
            {"msg": self.metadata_description}
        )
    
    def set_description(self):
        with self:
            self._set_description()

    def _set_schema_description(self, file_names, file_date):
        """ """
        comment_text = f"Schema catastale CXF. Estrazione: {file_date}. Fonti: {', '.join(file_names)}"
        self.session.execute(
            text(f"COMMENT ON SCHEMA {self.target_schema} IS :c"),
            {"c": comment_text}
        )

    def _check_schema_exists(self):
        result = self.session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :s)"),
            {"s": self.target_schema}
        ).scalar()
        return result

    def _check_table_exists(self):
        result = self.session.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t)"
        ), {"t": CXFMetadata.__tablename__}).scalar()
        return result

    def _check_entry_exists(self):
        result = self.session.execute(text(
            f"SELECT EXISTS (SELECT 1 FROM public.{CXFMetadata.__tablename__} WHERE schema_name = :s)"
        ), {"s": self.target_schema}).scalar()
        return result

    def _create_schema(self):
        self.session.execute(text(f'CREATE SCHEMA "{self.target_schema}"'))

    def _archive_schema(self):
        # Archiviazione
        archive_date = datetime.date.today().strftime("%Y_%m_%d")
        archive_name = f"{self.target_schema}_archived_{archive_date}"
        
        print(f"Archiviazione schema '{self.target_schema}' -> '{archive_name}'...")
        self.session.execute(text(f'DROP SCHEMA IF EXISTS "{archive_name}" CASCADE'))
        self.session.execute(text(f'ALTER SCHEMA "{self.target_schema}" RENAME TO "{archive_name}"'))
        return archive_name
        

class PostGISExporter(BaseExporter):

    def __init__(self, host, database, user, password, port=5432):
        # In SQLAlchemy 2.0 è buona norma usare l'URL di connessione esplicito
        connection_url = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        self.engine = create_engine(connection_url)

    def _get_file_info(self, project):
        file_paths = [Path(src.file_path) for src in project.sources if hasattr(src, 'file_path')]
        if not file_paths:
            return datetime.date.today(), ["unknown_source"]
        
        mtime = max([p.stat().st_mtime for p in file_paths])
        file_date = datetime.datetime.fromtimestamp(mtime).date()
        file_names = [p.name for p in file_paths]
        return file_date, file_names

    def prepare_schema(self, target_schema):
        with PostGISMetadataManager(self.engine, target_schema) as metadata_manager:
            # Verifica esistenza schema
            schema_exists = metadata_manager._check_schema_exists()
            
            # Verifica esistenza tabella metadati
            meta_table_exists = metadata_manager._check_table_exists()

            if schema_exists:
                has_entry = False
                if meta_table_exists:
                    has_entry = metadata_manager._check_entry_exists()
                
                if not meta_table_exists or not has_entry:
                    raise RuntimeError(
                        f"SICUREZZA: Lo schema '{target_schema}' non è gestito da CXF2GIS. Operazione annullata."
                    )
            
                archive_name = metadata_manager._archive_schema()
                metadata_manager._register_archive(archive_name)
            metadata_manager._create_schema()

        metadata_manager.setup_database()

    def _prepare_schema_OLD(self, conn, target_schema):
        # --- BLOCCO TRANSAZIONALE 1: SICUREZZA E PREPARAZIONE ---
        # engine.begin() apre la connessione e inizia una transazione automaticamente

        with self.engine.begin() as conn:
            # Verifica esistenza schema
            schema_exists = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :s)"
            ), {"s": target_schema}).scalar()
            
            # Verifica esistenza tabella metadati
            meta_table_exists = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'cxf_metadata')"
            )).scalar()

            if schema_exists:
                has_entry = False
                if meta_table_exists:
                    has_entry = conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM public.cxf_metadata WHERE schema_name = :s)"
                    ), {"s": target_schema}).scalar()

                if not meta_table_exists or not has_entry:
                    raise RuntimeError(
                        f"SICUREZZA: Lo schema '{target_schema}' non è gestito da CXF2GIS. Operazione annullata."
                    )
                
                # Archiviazione
                archive_date = datetime.date.today().strftime("%Y_%m_%d")
                archive_name = f"{target_schema}_archived_{archive_date}"
                
                print(f"Archiviazione schema '{target_schema}' -> '{archive_name}'...")
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{archive_name}" CASCADE'))
                conn.execute(text(f'ALTER SCHEMA "{target_schema}" RENAME TO "{archive_name}"'))
                
                conn.execute(text(
                    "UPDATE public.cxf_metadata SET stato = 'archived', schema_name = :new_name "
                    "WHERE schema_name = :old_name"
                ), {"new_name": archive_name, "old_name": target_schema})
            
            # Inizializzazione nuovo schema
            self._init_metadata_table(conn)
            conn.execute(text(f'CREATE SCHEMA "{target_schema}"'))
            # Il commit avviene qui automaticamente alla chiusura del blocco 'with'

    def export(self, project, target_epsg, target_schema="catasto"):
    
        file_date, file_names = self._get_file_info(project)
        
        self.prepare_schema(target_schema)

        # 2. Scrittura layer nel database
        for table_name, merged_gdf in self._merge_sources(project.sources, target_epsg):
            print(f"Scrittura tabella: {target_schema}.{table_name}")
            merged_gdf.to_postgis(
                name=table_name,
                con=self.engine, # to_postgis accetta direttamente l'engine
                schema=target_schema,
                if_exists='replace',
                index=False
            )

        # --- BLOCCO TRANSAZIONALE 2: METADATI E DOCUMENTAZIONE ---
        with PostGISMetadataManager(self.engine, target_schema) as metadata_manager:
            metadata_manager.update_record({
                "schema_name": target_schema,
                "extraction_date": file_date,
                # "import_timestamp": ,
                "source_filenames": ", ".join(file_names),
                "record_status": "production",
                "description": f"Importazione CXF2GIS - {len(project.sources)} file"
            })
            metadata_manager._set_schema_description(file_names, file_date)
        pass
