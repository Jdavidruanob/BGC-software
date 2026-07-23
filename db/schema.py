from db.connection import DBConnection


class SchemaManager:
    """Gestión de esquema DESACTIVADA para la base compartida en la nube.

    La estructura de la base (tablas, columnas, secuencias) la crea y mantiene
    la API. La app de escritorio se conecta a algo que YA existe: no crea ni
    altera tablas, no reinicializa la config ni toca las secuencias. Ejecutar
    esas operaciones podría borrar datos reales (saldo_en_caja, config, etc.).

    Estos métodos se conservan por compatibilidad de firma pero son no-ops.
    """

    def __init__(self, db: DBConnection):
        self.db = db

    def create_tables(self):
        print("ℹ️ create_tables() omitido: la estructura la administra la API.")

    def initialize_config_values(self):
        print("ℹ️ initialize_config_values() omitido: la config la administra la API.")

    def set_sequence_start_value(self, table_name: str, start_value: int):
        print(
            f"ℹ️ set_sequence_start_value('{table_name}') omitido: "
            "las secuencias las administra la API."
        )
