import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, LineString

from cxf2gis.comuni import ComuniManager

# Inizializzazione
mgr = ComuniManager()
mgr.update_cache()

class CXFSource:

    def __init__(self, file_path, input_epsg="EPSG:6707", exclude_types=None, extra_info=False):

        self.file_path = file_path

        
        self.exclude_types = exclude_types or []
        self.input_epsg = input_epsg
        # Contenitori per i diversi tipi di geometria
        self.layers = {
            'BORDO': [],   # Poligoni (Particelle, Fabbricati, ecc.)
            'TESTO': [],   # Punti con attributo testo
            'SIMBOLO': [], # Punti con codice simbolo
            'FIDUCIALE': [], # Punti fiduciali
            'LINEA': []    # Linee (archi, bordi di foglio, ecc.)
        }
        
        self.df_comuni = None
        # Caricamento opzionale della tabella comuni (CSV ISTAT)
        try:
            assert extra_info is True
            self.df_comuni = mgr.get_all_as_dataframe()
        except AssertionError:
            pass
        except Exception as error:
            print(f"Errore caricamento tabella comuni: {error}")

    def _decripta_nome_file(self, filename):
        """ Estrae Comune, Sezione, Foglio e Allegato dal nome standard C660A000100 del file CXF """
        name = os.path.splitext(os.path.basename(filename))[0].upper()
        meta = {
            'comune': name[0:4],
            'sezione': name[4:5] if len(name) > 4 else '',
            'foglio': name[5:9] if len(name) >= 9 else '0',
            'allegato': name[9:11] if len(name) >= 11 else '00',
            'file_nome': filename
        }
        # Pulizia zeri iniziali per il foglio (es: 0001 -> 1)
        try:
            meta['foglio'] = str(int(meta['foglio']))
        except: pass

        return meta

    def _sup2gdf(self, file_path):
        """
        Cerca e parsa il file .SUP associato al file .CXF.
        Ritorna un DataFrame con colonne ['codice', 'area_sup']
        """
        # Il file SUP ha solitamente lo stesso base-name del CXF
        base_path = os.path.splitext(file_path)[0]
        sup_path = base_path + ".SUP"
        
        if not os.path.exists(sup_path):
            # print(f"Nota: File SUP non trovato in {sup_path}. Procedo senza dati di superficie.")
            return None

        records = []
        with open(sup_path, 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    # parts[0] è l'identificativo (es. 101, STRADA, ACQUA)
                    # parts[1] è l'area in mq
                    try:
                        records.append({
                            'codice': parts[0],
                            'area_nominale': float(parts[1])
                        })
                    except ValueError:
                        continue # Salta righe di intestazione non numeriche se presenti
        
        return pd.DataFrame(records)

    def _parse(self):
        # for file_cxf in self.files_to_process:
            
        df_sup = self._sup2gdf(self.file_path)
        meta = self.meta
        
        with open(self.file_path, 'r', encoding='latin-1') as f:
            lines = [line.strip() for line in f if line.strip()]

        i = 0
        while i < len(lines):
            tag = lines[i]

            # Salto l'elemento se incluso nella lista di esclusione
            if tag in self.exclude_types:
                i += 1
                continue

            if tag == "BORDO":
                i = self._handle_bordo(lines, i, df_sup, meta)
            elif tag == "TESTO":
                i = self._handle_testo(lines, i, meta)
            elif tag == "SIMBOLO":
                i = self._handle_simbolo(lines, i, meta)
            elif tag == "FIDUCIALE":
                i = self._handle_fiduciale(lines, i, meta)
            elif tag == "LINEA":
                i = self._handle_linea(lines, i, meta)
            else:
                i += 1

        # Dopo il parsing, trasformiamo le liste in GeoDataFrame riproiettati
        self._finalize_layers()

    def _finalize_layers(self):
        """ 
        Converte le liste di dizionari in GeoDataFrames, 
        imposta il CRS sorgente e riproietta al CRS target.
        """
        for layer_name in self.layers.keys():
            data = self.layers[layer_name]
            if not data:
                self.layers[layer_name] = None
                continue
            
            # 1. Crea il GeoDataFrame con il CRS di input (es. Cassini o Gauss-Boaga)
            gdf = gpd.GeoDataFrame(data, crs=self.input_epsg)
            
            # 2. Se richiesto extra_info, arricchiamo il GDF con i dati del comune
            if self.info_comune:
                for key, value in self.info_comune.items():
                    gdf[f"comune_{key}"] = value

            # 3. Trasformazione CRS: il momento cruciale
            if self.target_epsg and self.input_epsg != self.target_epsg:
                gdf = gdf.to_crs(self.target_epsg)
            
            self.layers[layer_name] = gdf

    def _handle_bordo(self, lines, i, df_sup, meta):
        codice = lines[i+1]
        num_isole = int(lines[i+8])
        num_tot_v = int(lines[i+9])
        cursor = i + 10
        isole_v = [int(lines[cursor+j]) for j in range(num_isole)]
        cursor += num_isole
        coords = [(float(lines[cursor+j*2]), float(lines[cursor+j*2+1])) for j in range(num_tot_v)]
        cursor += (num_tot_v * 2)

        if num_isole == 0:
            geom = Polygon(coords)
        else:
            ext_idx = num_tot_v - sum(isole_v)
            geom = Polygon(shell=coords[:ext_idx], holes=[coords[ext_idx:ext_idx+v] for v in isole_v])

        classe = "PARTICELLA"
        if codice.endswith('+'): classe = "FABBRICATO"
        elif "STRADA" in codice.upper(): classe = "STRADA"
        elif "ACQUA" in codice.upper(): classe = "ACQUA"

        data = {
            'geometry': geom, 'codice': codice, 'classe': classe,
            'comune': meta['comune'], 'foglio': meta['foglio'], 
            'sezione': meta['sezione'], 'allegato': meta['allegato']
        }
        
        if df_sup is not None:
            sup_match = df_sup[df_sup['codice'] == codice]
            if not sup_match.empty:
                data['area_nominale'] = sup_match.iloc[0]['area_nominale']
                data['area_grafica'] = geom.area

        self.layers['BORDO'].append(data)
        return cursor

    def _handle_testo(self, lines, i, meta):
        self.layers['TESTO'].append({
            'geometry': Point(float(lines[i+4]), float(lines[i+5])),
            'testo': lines[i+1], 
            'angolo': float(lines[i+3]),
            'foglio': meta['foglio'],
            'comune': meta['comune']  # <-- AGGIUNGI QUESTO
        })
        return i + 8

    def _handle_simbolo(self, lines, i, meta):
        cod = lines[i+1]
        self.layers['SIMBOLO'].append({
            'geometry': Point(float(lines[i+3]), float(lines[i+4])),
            'codice_simbolo': cod,
            'angolo': float(lines[i+2]),
            'foglio': meta['foglio'],
            'comune': meta['comune']  # <-- AGGIUNGI QUESTO
        })
        return i + 6

    def _handle_fiduciale(self, lines, i, meta):
        self.layers['FIDUCIALE'].append({
            'geometry': Point(float(lines[i+3]), float(lines[i+4])),
            'id_fid': lines[i+1], 'foglio': meta['foglio']
        })
        return i + 5

    def _handle_linea(self, lines, i, meta):
        num_v = int(lines[i+2])
        cursor = i + 3
        coords = [(float(lines[cursor+j*2]), float(lines[cursor+j*2+1])) for j in range(num_v)]
        self.layers['LINEA'].append({'geometry': LineString(coords), 'foglio': meta['foglio']})
        return cursor + (num_v * 2)