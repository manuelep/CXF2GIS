from sqlmodel import Session, select, SQLModel
from sqlalchemy import text

from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select

class CXFMetadata(SQLModel, table=True):
    __tablename__: str = "cxf_metadata"
    
    schema_name: str = Field(primary_key=True)
    extraction_date: date
    import_timestamp: datetime = Field(default_factory=datetime.now)
    source_filenames: str
    record_status: str
    description: Optional[str] = None


class MetadataManager:

    metadata_description = 'Registry of CXF data imports managed by CXF2GIS.'

    def __init__(self, engine, target_schema='cadastre'):
        self.engine = engine
        self.target_schema = target_schema

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.commit()
        self.session.__exit__(exc_type, exc_value, traceback)
        del self.session

    def _set_description(self):
        raise NotImplementedError()

    def set_description(self):
        raise NotImplementedError()

    def _set_schema_description(self):
        raise NotImplementedError()

    def setup_database(self):
        """Crea le tabelle basate sui modelli SQLModel."""
        SQLModel.metadata.create_all(self.engine)
        self.set_description()

    def _update_record(self, data_dict: dict):
        """Inserisce o aggiorna un record (Upsert)."""
        # Cerchiamo il record esistente
        statement = select(CXFMetadata).where(CXFMetadata.schema_name == data_dict["schema_name"])
        results = self.session.exec(statement)
        record = results.first()
        
        if record:
            # Aggiornamento (SQLModel gestisce bene l'aggiornamento da dizionario)
            for key, value in data_dict.items():
                setattr(record, key, value)
        else:
            # Creazione
            record = CXFMetadata(**data_dict)
            
        self.session.add(record)


    def _register_archive(self, new_name):
        """Gestisce il cambio di nome e stato durante l'archiviazione."""
        statement = select(CXFMetadata).where(CXFMetadata.schema_name == self.target_schema)
        record = self.session.exec(statement).first()
        
        if record:
            # Creiamo il nuovo record per l'archivio (le PK non si cambiano facilmente)
            archive_data = record.dict()
            archive_data["schema_name"] =  new_name
            archive_data["record_status"] = "archived"
            
            self.session.delete(record)
            self.session.add(CXFMetadata(**archive_data))
