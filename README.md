# cxf2gis

## 🇮🇹 ITA

**Libreria Python per il parsing di file CXF catastali e l'integrazione in ambienti GIS e database spaziali.**

### Descrizione

`cxf2gis` è uno strumento progettato per semplificare la gestione dei dati cartografici dell'Agenzia delle Entrate (formato CXF). A differenza degli approcci tradizionali, la libreria permette di:
* **Caricamento Massivo**: Gestire interi archivi o cartelle in modo ricorsivo.
* **Armonizzazione Coordinate**: Gestire sistemi di coordinate eterogenei, inclusi i sistemi catastali nativi Cassini-Soldner con lookup automatico via PRGCloud.
* **Integrazione GIS**: Unificare i layer in formati standard (GeoPackage) e database spaziali (PostGIS).

### 🚀 Installazione

```sh
pip install git+https://github.com/manuelep/CXF2GIS.git
```

Oppure per lo sviluppo:

```sh
git clone https://github.com/manuelep/CXF2GIS.git
cd CXF2GIS
pip install -e ".[dev]"
```

### 📦 Dipendenze

Le dipendenze principali includono:
- `geopandas`, `shapely` per la manipolazione dei dati geografici
- `SQLAlchemy`, `sqlmodel` per l'interazione con database
- `pyogrio` per l'esportazione veloce in GeoPackage
- `requests` per il lookup dei comuni

Per PostGIS: `pip install "CXF2GIS[postgis]"` aggiunge `psycopg2-binary` e dipendenze correlate.

### 🛠 Utilizzo

La libreria fornisce un'interfaccia a riga di comando chiamata `cxf2gis`.

#### Help

```sh
cxf2gis -h
```

```sh
cxf2gis gpkg -h
```

#### Esempi

- Export dei file CXF contenuti nella cartella `input_folder` nel file `output_map.gpkg`.
    È importante specificare il corretto CRS associato ai file di input (nell'esempio ETRF2000)

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i EPSG:6707
```

- Export con lookup automatico Cassini-Soldner via PRGCloud (richiede credenziali):

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i PRGCLOUD
```

- Export a PostGIS (richiede dipendenze PostGIS):

```sh
pip install "CXF2GIS[postgis]"
cxf2gis postgis ./input_folder "postgresql://user:password@localhost:5432/database" -i EPSG:6707
```

- Con informazioni aggiuntive sui comuni:

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i EPSG:6707 -c -e
```

---

### 🗺 Svilippi futuri

- [x] **Esportatore GeoPackage**: Gestione dei layer unificati (`bordo`, `testo`, ecc.).
- [x] **Esportatore PostGIS**: Integrazione nativa con database spaziali.
- [x] **Lookup Cassini-Soldner**: Generatore automatico di stringhe Proj4 per i centri di emanazione via PRGCloud.
- [ ] **Monitoraggio Avanzamento**: Integrazione di `tqdm` per gestire i caricamenti massivi.

## 🤝 Contribuisci

I contributi sono benvenuti! Se hai parametri per nuovi centri di emanazione o miglioramenti al parser, apri una Issue o una Pull Request.

---

## 🇬🇧 ENG

**Python library for parsing Italian cadastral CXF files and integrating them into GIS environments and spatial databases.**

### Description

`cxf2gis` is a Python toolkit designed to streamline the management of Italian cadastral data (CXF format). Key features include:
* **Bulk Processing**: Handle individual files or entire directory trees recursively.
* **Coordinate Harmonization**: Unified management of diverse CRS, including native Cassini-Soldner cadastral systems with automatic lookup via PRGCloud.
* **GIS Ready**: Export unified layers to industry-standard formats like GeoPackage and spatial databases like PostGIS.

## 🚀 Installation

```sh
pip install git+https://github.com/manuelep/CXF2GIS.git
```

Or for development:

```sh
git clone https://github.com/manuelep/CXF2GIS.git
cd CXF2GIS
pip install -e ".[dev]"
```

### 📦 Dependencies

Main dependencies include:
- `geopandas`, `shapely` for geographic data manipulation
- `SQLAlchemy`, `sqlmodel` for database interaction
- `pyogrio` for fast GeoPackage export
- `requests` for comune lookup

For PostGIS: `pip install "CXF2GIS[postgis]"` adds `psycopg2-binary` and related dependencies.

## 🛠 Usage

The library provides a command-line interface (CLI) named cxf2gis.

#### Help

```sh
cxf2gis -h
```

```sh
cxf2gis gpkg -h
```

#### Examples
- Export CXF files from `input_folder` to the `output_map.gpkg` file.
  It is important to specify the correct CRS associated with the input files (ETRF2000 in this example).

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i EPSG:6707
```

- Export with automatic Cassini-Soldner lookup via PRGCloud (requires credentials):

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i PRGCLOUD
```

- Export to PostGIS (requires PostGIS dependencies):

```sh
pip install "CXF2GIS[postgis]"
cxf2gis postgis ./input_folder "postgresql://user:password@localhost:5432/database" -i EPSG:6707
```

- With additional comune information:

```sh
cxf2gis gpkg ./input_folder output_map.gpkg -i EPSG:6707 -c -e
```

## 🤝 Contributing

Contributions are welcome! If you have parameters for new emission centers or improvements to the parser, open an Issue or a Pull Request.

---

## 📄 License

This project is licensed under the GPL-3.0-or-later License - see the [LICENSE](LICENSE) file for details.
