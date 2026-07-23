from db.connection import DBConnection
from db.schema import SchemaManager


class MigrationService:
    """Migración anual DESACTIVADA.

    El concepto de "migración anual" (copiar el .db de un año a un archivo nuevo
    y arrastrar saldos) ya no aplica: ahora hay una única base compartida en la
    nube administrada por la API. Los saldos y el histórico viven siempre en la
    misma base. Este método se conserva por compatibilidad pero es un no-op.
    """

    def __init__(self, db: DBConnection, schema: SchemaManager):
        self.db = db
        self.schema = schema

    def run_annual_migration(self, prev_db_path=None):
        print(
            "ℹ️ run_annual_migration() desactivado: con la base compartida en la "
            "nube ya no existe la migración anual de archivos .db."
        )
