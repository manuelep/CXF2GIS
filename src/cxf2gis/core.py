from pathlib import Path
import asyncio
from concurrent.futures import ProcessPoolExecutor
from .models import CXFSource

class CXFProject:
    def __init__(self, target_epsg):
        """
        Inizializza il progetto con un sistema di riferimento unico per l'output.
        :param target_epsg: Sistema di destinazione (es. 'EPSG:6707').
        """
        self.target_epsg = target_epsg
        self.sources = []

    def add_source(self, file_path, input_crs):
        """
        Aggiunge un file richiedendo obbligatoriamente il CRS.
        input_crs può essere un codice EPSG o una stringa Proj4 per i sistemi Cassini.
        """
        if not input_crs:
            raise ValueError(f"Dichiarazione CRS obbligatoria per: {file_path}")
        
        # L'istanza riceve sia il CRS sorgente che quello di destinazione
        source = CXFSource(file_path, input_crs=input_crs, target_epsg=self.target_epsg)
        self.sources.append(source)

    def add_directory(self, folder_path, input_crs, recursive=False):
        """
        Carica tutti i file .cxf da un percorso con CRS dichiarato.
        """
        p = Path(folder_path)
        pattern = "**/*.cxf" if recursive else "*.cxf"
        
        for file in p.glob(pattern):
            self.add_source(str(file), input_crs)

    add_sources = add_directory  # Alias per compatibilità

    async def load_all(self, max_workers=4):
        """Gestione asincrona del parsing parallelo."""
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            tasks = [loop.run_in_executor(pool, s.parse) for s in self.sources]
            await asyncio.gather(*tasks)

    def __iter__(self):
        """Permette di ciclare direttamente sulle sorgenti del progetto: for src in project:"""
        for source in self.sources:
            # Restituiamo la sorgente solo se ha dei dati caricati
            if source.layers:
                yield source

    def export(self, exporter):
        """L'esportatore ora riceve l'intero progetto (self)"""
        exporter.export(self)