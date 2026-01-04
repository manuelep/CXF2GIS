from sqlalchemy import create_engine, text

class BaseExporter:
    def export(self, sources, target_epsg):
        raise NotImplementedError