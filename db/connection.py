import os

import psycopg
from psycopg.rows import dict_row


def _load_env():
    """Carga variables desde un archivo .env si python-dotenv está disponible.
    No falla si no está instalado ni si el archivo no existe."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass


class DBConnection:
    """Conexión a PostgreSQL (base compartida en la nube).

    La URL de conexión se lee de la variable de entorno DATABASE_URL, definida
    en un archivo .env que NO se versiona (ver .env.example). La estructura de
    la base (tablas y columnas) la administra la API; esta app solo lee y
    escribe datos sobre lo que ya existe.
    """

    def __init__(self, db_path=None):
        # db_path se conserva por compatibilidad con el wiring existente, pero
        # ya no se usa: la conexión se hace por DATABASE_URL.
        self.db_path = db_path
        self.conn = None

    def connect(self):
        try:
            _load_env()
            dsn = os.environ.get("DATABASE_URL")
            if not dsn:
                print(
                    "❌ Falta la variable de entorno DATABASE_URL. "
                    "Defínela en un archivo .env (ver .env.example)."
                )
                return False
            self.conn = psycopg.connect(dsn, row_factory=dict_row)
            return True
        except psycopg.Error as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
