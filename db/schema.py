import sqlite3
from db.connection import DBConnection


class SchemaManager:
    def __init__(self, db: DBConnection):
        self.db = db

    def create_tables(self):
        try:
            cursor = self.db.conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socios (
                    id INTEGER PRIMARY KEY,
                    cc TEXT,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    saldo INTEGER DEFAULT 0,
                    celular TEXT,
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creditos (
                    letra INTEGER PRIMARY KEY AUTOINCREMENT,
                    capital INTEGER NOT NULL,
                    interes REAL NOT NULL,
                    no_cuotas INTEGER NOT NULL,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socio_credito (
                    socio_id INTEGER NOT NULL,
                    credito_letra INTEGER NOT NULL,
                    PRIMARY KEY (socio_id, credito_letra),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liquidaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credito_letra INTEGER NOT NULL,
                    nro_cuota INTEGER NOT NULL,
                    fecha_vencimiento DATE NOT NULL,
                    valor_cuota INTEGER NOT NULL,
                    interes_mes INTEGER NOT NULL,
                    cuota_mensual INTEGER NOT NULL,
                    saldo_capital INTEGER NOT NULL,
                    fecha_pago DATE,
                    interes_mora INTEGER DEFAULT 0,
                    mora_aplicada INTEGER DEFAULT 0,
                    notif_prev_enviada INTEGER DEFAULT 0,
                    notif_venc_enviada INTEGER DEFAULT 0,
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recibos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socio_id INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archivo_path TEXT,
                    FOREIGN KEY (socio_id) REFERENCES socios(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_recibo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recibo_id INTEGER NOT NULL,
                    tipo_operacion TEXT NOT NULL CHECK (tipo_operacion IN ('aporte', 'pago_credito', 'retiro', 'abono_capital')),
                    socio_id INTEGER NOT NULL,
                    credito_letra INTEGER,
                    nro_cuota INTEGER,
                    monto INTEGER NOT NULL,
                    abono_mora INTEGER DEFAULT 0,
                    FOREIGN KEY (recibo_id) REFERENCES recibos(id),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auxiliar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    socio TEXT NOT NULL,
                    recibo INTEGER,
                    monto INTEGER NOT NULL,
                    saldo INTEGER NOT NULL,
                    cuota INTEGER,
                    id_credito TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            self.db.conn.commit()
            print("✅ Tablas creadas con estructura actualizada.")
        except sqlite3.Error as e:
            print(f"❌ Error creando tablas: {e}")

    def initialize_config_values(self):
        cursor = self.db.conn.cursor()
        default_values = {
            "saldo_en_caja": "0",
            "total_admin": "0",
            "porcentaje_mora": "0.02",
        }
        for key, default_val in default_values.items():
            cursor.execute(
                "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
                (key, default_val),
            )
        self.db.conn.commit()
        print("✅ Configuración inicial verificada.")

    def set_sequence_start_value(self, table_name: str, start_value: int):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                (table_name, start_value),
            )
            self.db.conn.commit()
            print(f"✅ Secuencia de '{table_name}' establecida a {start_value}. Siguiente ID será {start_value + 1}.")
        except Exception as e:
            print(f"❌ Error al establecer la secuencia para '{table_name}': {e}")
            self.db.conn.rollback()
