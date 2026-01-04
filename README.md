# cxf2gis: Libreria Python per il parsing di file CXF catastali e l'integrazione in ambienti GIS e database spaziali.

## Descrizione

cxf2gis è uno strumento progettato per semplificare la gestione dei dati cartografici dell'Agenzia delle Entrate (formato CXF). A differenza degli approcci tradizionali, la libreria permette di gestire il caricamento massivo di interi archivi, armonizzare sistemi di coordinate eterogenei (inclusi i sistemi catastali nativi Cassini-Soldner) e unificare i layer tramite viste SQL su database come PostGIS.

## Contribuisci

I contributi sono benvenuti! Se hai parametri per nuovi centri di emanazione o miglioramenti al parser, apri una Issue o una Pull Request.




# cxf2gis

## 🇮🇹 ITA

**Libreria Python per il parsing di file CXF catastali e l'integrazione in ambienti GIS e database spaziali.**

### Descrizione

`cxf2gis` è uno strumento progettato per semplificare la gestione dei dati cartografici dell'Agenzia delle Entrate (formato CXF). A differenza degli approcci tradizionali, la libreria permette di:
* **Caricamento Massivo**: Gestire interi archivi o cartelle in modo ricorsivo.
* **Armonizzazione Coordinate**: Gestire sistemi di coordinate eterogenei, inclusi i sistemi catastali nativi Cassini-Soldner.
* **Integrazione GIS**: Unificare i layer in formati standard (GeoPackage) e database spaziali (PostGIS - NON ANCORA).

### 🚀 Installazione

```sh
git clone https://github.com/manuelep/CXF2GIS.git
pip install CXF2GIS
```

### 🛠 Utilizzo

La libreria fornisce un'interfaccia a riga di comando chiamata `cxf2gis`.

#### Help

```sh
cxf2gis -h
```

```sh
cxf2gis gpkg -h
```

---

### 🗺 Svilippi futuri

- [x] **Esportatore GeoPackage**: Gestione dei layer unificati (`bordo`, `testo`, ecc.).
- [ ] **Esportatore PostGIS**: Integrazione nativa con database spaziali.
- [ ] **Lookup Cassini-Soldner**: Generatore automatico di stringhe Proj4 per i centri di emanazione.
- [ ] **Monitoraggio Avanzamento**: Integrazione di `tqdm` per gestire i caricamenti massivi.

## 🤝 Contribuisci

I contributi sono benvenuti! Se hai parametri per nuovi centri di emanazione o miglioramenti al parser, apri una Issue o una Pull Request.

---

## 🇬🇧 ENG

**Python library for parsing Italian cadastral CXF files and integrating them into GIS environments and spatial databases.**

### Description

`cxf2gis` is a Python toolkit designed to streamline the management of Italian cadastral data (CXF format). Key features include:
* **Bulk Processing**: Handle individual files or entire directory trees recursively.
* **Coordinate Harmonization**: Unified management of diverse CRS, including native Cassini-Soldner cadastral systems.
* **GIS Ready**: Export unified layers to industry-standard formats like GeoPackage and spatial databases like PostGIS.

## 🚀 Installation

```sh
git clone https://github.com/manuelep/CXF2GIS.git
pip install CXF2GIS
```

## 🛠 Usage

The library provides a command-line interface (CLI) named cxf2gis.

#### Help

```sh
cxf2gis -h
```

```sh
cxf2gis gpkg -h
```

## 🤝 Contributing

Contributions are welcome! If you have parameters for new cadastral origin centers or parser improvements, feel free to open a Issue or a Pull Request.
