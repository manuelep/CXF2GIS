import requests
import xml.etree.ElementTree as ET
import time
from sqlitedict import SqliteDict
import html
import re, os

class ProjDictLike:
    """ """

    def get_foglio_data(self, foglio_id):
        """Da implementare nelle sottoclassi."""
        raise NotImplementedError()

    def __getitem__(self, *args, **kwargs):
        return self.get_foglio_data(*args, **kwargs)
    

class PrgCloudCache(ProjDictLike):
    def __init__(self, 
        username=os.getenv("PRGCLOUD_USERNAME"),
        password=os.getenv("PRGCLOUD_PASSWORD"),
        cache_file='coords_cache.sqlite',
        ttl_seconds=14515200
    ):
        """
        Initializes the PRGCloud service helper with persistent local caching.

        Args:
            username (str): The username for authenticating with the prgcloud.com service.
            password (str): The password associated with the account for API access.
            cache_file (str, optional): The file system path to the SQLite database used for 
                persistent storage. Defaults to 'coords_cache.sqlite'.
            ttl_seconds (int, optional): Cache validity duration in seconds (Time To Live). 
                Once expired, data is re-fetched from the remote service. 
                Defaults to 14515200 (24 weeks).
        """
        self.username = username
        self.password = password
        self.cache_file = cache_file
        self.ttl_seconds = ttl_seconds
        self.base_url = "https://www.prgcloud.com/auth/gettransform.php"

    def get_foglio_data(self, foglio_id):
        """
        Recupera tutte le informazioni del foglio.
        Ritorna un dizionario con i parametri o None se non trovato.
        """
        now = time.time()
        
        with SqliteDict(self.cache_file, autocommit=True) as cache:
            if foglio_id in cache:
                data, timestamp = cache[foglio_id]
                if now - timestamp < self.ttl_seconds:
                    return data
            
            # Se non in cache o scaduto, scarica i dati
            print(f"Richiesta remota per foglio: {foglio_id}...")
            full_data = self._fetch_from_service(foglio_id)
            
            if full_data:
                cache[foglio_id] = (full_data, now)
                return full_data
        
        return None

    def _fetch_from_service(self, foglio_id):
        """Esegue la chiamata HTTP, decodifica le entità HTML e fa il parsing."""
        params = {
            'username': self.username,
            'password': self.password,
            'foglio': foglio_id
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 1. Decodifica le entità (es: da &lt; a <)
            raw_text = html.unescape(response.text)
            
            # 2. Pulizia opzionale: il servizio sembra mettere spazi extra nei tag (es: <foglio >)
            # Rimuoviamo gli spazi prima della chiusura del tag per evitare problemi di parsing
            clean_xml = re.sub(r'\s+>', '>', raw_text)

            # 3. Parsing dell'XML pulito
            root = ET.fromstring(clean_xml)
            
            info = {
                'numero': getattr(root.find("numero"), 'text', None),
                'proj4': getattr(root.find(".//SRID"), 'text', None),
                'metodo': getattr(root.find(".//metodo"), 'text', None),
                'origine': getattr(root.find(".//origine"), 'text', None),
                'eseguire': getattr(root.find(".//eseguire"), 'text', None)
            }
            
            return {k: (v.strip() if v else v) for k, v in info.items()}
            
        except Exception as e:
            print(f"Errore durante il recupero o il parsing dei dati: {e}")
            # Se vuoi vedere cosa è arrivato davvero in caso di errore:
            # print(f"Raw response: {response.text[:200]}...")
        
        return None

# # --- ESEMPIO D'USO ---
# if __name__ == "__main__":
#     api = PrgCloudCache("myuser", "mypassword")
    
#     print(f"api è di tipo giusto: {isinstance(api, ProjDictLike)}")
    
#     risultato = api.get_foglio_data("C660A000100")
    
#     if risultato:
#         print(f"Numero Foglio: {risultato['numero']}")
#         print(f"Stringa Proj: {risultato['proj4']}")
#         print(f"Metodo:       {risultato['metodo']}")
#         print(f"Origine:      {risultato['origine']}")
#         print(f"Eseguire:     {risultato['eseguire']}")