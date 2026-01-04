import argparse
import sys
from pathlib import Path
from cxf2gis.core import CXFProject
from cxf2gis.exporters.geopackage.base import GPKGExporter
# from cxf2gis.exporters.postgis import PostGISExporter # Sarà aggiunto dopo

def handle_gpkg(args, project):
    """Logica specifica per l'export GeoPackage."""
    print(f"Exporting to GeoPackage: {args.output}...")
    exporter = GPKGExporter(args.output)
    project.export(exporter, args.target_epsg)

def main():
    parser = argparse.ArgumentParser(
        prog="cxf2gis",
        description="CLI tool to parse Italian cadastral CXF files and export to GIS formats."
    )
    
    # Argomenti comuni a tutti i comandi (Global Options)
    subparsers = parser.add_subparsers(dest="command", help="Available output formats", required=True)

    # --- Sottocomando GPKG ---
    gpkg_parser = subparsers.add_parser("gpkg", help="Export to a GeoPackage file")
    gpkg_parser.add_argument("input", help="Source .cxf file or directory")
    gpkg_parser.add_argument("output", help="Output .gpkg file path")
    
    # --- Sottocomando POSTGIS (Placeholder per il futuro) ---
    pg_parser = subparsers.add_parser("postgis", help="Export to a PostGIS database")
    pg_parser.add_argument("input", help="Source .cxf file or directory")
    pg_parser.add_argument("-d", "--database", required=True, help="PostgreSQL connection string")

    # Opzioni comuni aggiunte a ogni parser (o gestite globalmente)
    for p in [gpkg_parser, pg_parser]:
        p.add_argument("-i", "--input-epsg", required=True, help="Input CRS (e.g. EPSG:3003)")
        p.add_argument("-t", "--target-epsg", default="EPSG:6704", help="Target CRS (default: EPSG:6704)")
        p.add_argument("-r", "--recursive", action="store_true", help="Recursive search")
        p.add_argument("-c", "--comune-info", default=False, action="store_true", help="Include comune info in output")
        p.add_argument("-e", "--extra-info", default=False, action="store_true", help="Include extra info from comuni database")

    args = parser.parse_args()
    
    # 1. Preparazione Progetto
    project = CXFProject(target_epsg=args.target_epsg)
    input_path = Path(args.input)

    # 2. Caricamento file (Logica unificata)
    if input_path.is_file():
        project.add_source(str(input_path), input_crs=args.input_epsg, extra_info=args.extra_info)
    elif input_path.is_dir():
        project.add_sources(str(input_path), input_crs=args.input_epsg, recursive=args.recursive, extra_info=args.extra_info)
    
    if not project.sources:
        print("No CXF files found.")
        sys.exit(0)

    # 3. Esecuzione Parsing
    print(f"Parsing {len(project.sources)} files...")
    for src in project:
        src.parse()

    # 4. Routing dell'esportazione
    if args.command == "gpkg":
        handle_gpkg(args, project)
    elif args.command == "postgis":
        # handle_postgis(args, project)
        print("PostGIS export not yet implemented.")

    print("Process completed successfully.")

if __name__ == "__main__":
    main()