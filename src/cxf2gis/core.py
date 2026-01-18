from pathlib import Path
import asyncio
from concurrent.futures import ProcessPoolExecutor
from .models import CXFSource
from .exporters.base import BaseExporter
from .exporters.projtools.prgcloud import ProjDictLike
from typing import Union

class CXFProject:
    def __init__(self, target_epsg):
        """
        Inizializza il progetto con un sistema di riferimento unico per l'output.
        :param target_epsg: Sistema di destinazione (es. 'EPSG:6707').
        """
        self.target_epsg = target_epsg
        self.sources = []

    def add_source(self, file_path: str, input_crs: Union[str, ProjDictLike], extra_info: bool=False):
        """
        Aggiunge un file richiedendo obbligatoriamente il CRS.
        input_crs può essere un codice EPSG o una stringa Proj4 per i sistemi Cassini.
        """
        if not input_crs:
            raise ValueError(f"Dichiarazione CRS obbligatoria per: {file_path}")
        elif isinstance(input_crs, ProjDictLike):
            crs = input_crs[Path(file_path).stem]['proj4']
        else:
            crs = input_crs
        
        # L'istanza riceve sia il CRS sorgente che quello di destinazione
        source = CXFSource(file_path, crs, extra_info=extra_info)
        self.sources.append(source)

    def add_directory(self, folder_path: Path, input_crs: Union[str, ProjDictLike], recursive=False, extra_info=False):
        """
        Carica tutti i file .cxf da un percorso con CRS dichiarato.
        """
        p = Path(folder_path)
        pattern = "**/*.cxf" if recursive else "*.cxf"
        
        for file in p.glob(pattern):
            self.add_source(str(file), input_crs, extra_info=extra_info)

    add_sources = add_directory  # Alias per compatibilità

    async def load_all(self, max_workers: int = 4):
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

    def export(self, exporter: BaseExporter, target_epsg: str):
        """L'esportatore ora riceve l'intero progetto (self)"""
        exporter.export(self, target_epsg)