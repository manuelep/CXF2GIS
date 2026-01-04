import json
import os
from pathlib import Path
import pandas as pd
from .providers import ContriniProvider, LocalJsonProvider

class ComuniManager:
    def __init__(self, cache_path=None):
        # Default cache in ~/.cache/cxf2gis/comuni.json
        self.cache_path = Path(cache_path or Path.home() / ".cache" / "cxf2gis" / "comuni.json")
        self.provider = None

    def setup_provider(self, source_type="remote", local_path=None):
        """Configura la sorgente dei dati."""
        if source_type == "remote":
            self.provider = ContriniProvider()
        elif source_type == "local":
            self.provider = LocalJsonProvider(local_path)

    def update_cache(self):
        """Scarica i dati dal provider e li salva localmente."""
        if not self.provider:
            self.setup_provider("remote")
        
        data = self.provider.fetch()
        
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Cache aggiornata in: {self.cache_path}")

    def get_all_as_dataframe(self):
        """
        Legge la cache locale e restituisce un Pandas DataFrame 
        con tutti i comuni italiani e i relativi codici.
        """
        if not self.cache_path.exists():
            # Se la cache non esiste, prova a crearla prima di fallire
            self.update_cache()

        try:
            df_raw = pd.read_json(self.cache_path)
        except Exception as e:
            print(f"Errore nel recupero dei dati comuni: {e}")
            return None
        else:
            # Estraiamo le informazioni richieste:
            # Il dataset contiene oggetti annidati per provincia e regione
            df_comuni = pd.DataFrame({
                'codice_catastale': df_raw['codiceCatastale'],
                'comune_nome': df_raw['nome'],
                'provincia_sigla': df_raw['sigla'],
                'provincia_nome': df_raw['provincia'].apply(lambda x: x['nome']),
                'regione_nome': df_raw['regione'].apply(lambda x: x['nome'])
            })
            
            # Rimuoviamo eventuali duplicati o righe senza codice catastale
            df_comuni = df_comuni.dropna(subset=['codice_catastale']).drop_duplicates('codice_catastale')
            
            return df_comuni

    def get_comune(self, codice_catastale):
        """Recupera le info di un comune dalla cache."""
        if not self.cache_path.exists():
            self.update_cache()
            
        with open(self.cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Cerca nel JSON (assumendo il formato di Contrini)
        for c in data:
            if c.get('codiceCatastale') == codice_catastale.upper():
                return c
        return None