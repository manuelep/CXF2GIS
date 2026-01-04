import requests, json

class ComuneProvider:
    def fetch(self):
        raise NotImplementedError

class ContriniProvider(ComuneProvider):
    URL = "https://raw.githubusercontent.com/matteocontrini/comuni-json/refs/heads/master/comuni.json"
    
    def fetch(self):
        response = requests.get(self.URL)
        response.raise_for_status()
        return response.json()

class LocalJsonProvider(ComuneProvider):
    def __init__(self, path):
        self.path = path

    def fetch(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)