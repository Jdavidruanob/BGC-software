import os
import sys
import time

import psycopg
from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row


def _load_env():
    """Carga variables desde un archivo .env si python-dotenv está disponible.
    No falla si no está instalado ni si el archivo no existe.

    Busca en dos lugares: (1) la carpeta de trabajo hacia arriba (útil en
    desarrollo) y (2) junto al ejecutable. El (2) es clave para la app
    instalada: PyInstaller descomprime en una carpeta temporal, pero el .env
    del usuario queda junto al .exe (en la carpeta de instalación), así que hay
    que buscarlo ahí explícitamente."""
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    load_dotenv()  # búsqueda normal (carpeta de trabajo) — desarrollo

    try:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)  # app empaquetada: junto al .exe
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        env_junto_al_exe = os.path.join(base, ".env")
        if os.path.exists(env_junto_al_exe):
            load_dotenv(env_junto_al_exe, override=False)
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
        # Último error de conexión (para que app.py pueda mostrar algo más útil
        # que "no se pudo conectar" a secas). None si la última conexión sirvió.
        self.ultimo_error = None

    def connect(self, intentos=4, espera_seg=2.0, timeout_seg=8):
        """Conecta a Postgres, reintentando ante fallos transitorios.

        Un solo intento sin reintentos hacía que cualquier blip de red o un
        momento lento del proxy de Railway se viera como "no hay conexión",
        obligando a cerrar y volver a abrir la app (que casi siempre sí
        conectaba en el segundo intento). `timeout_seg` además hace que cada
        intento falle rápido si el host no responde, en vez de quedarse
        colgado con el timeout de red por defecto del sistema operativo.
        """
        _load_env()
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            print(
                "❌ Falta la variable de entorno DATABASE_URL. "
                "Defínela en un archivo .env (ver .env.example)."
            )
            self.ultimo_error = "Falta la variable de entorno DATABASE_URL."
            return False

        for intento in range(1, intentos + 1):
            try:
                self.conn = psycopg.connect(dsn, row_factory=dict_row, connect_timeout=timeout_seg)
                self.ultimo_error = None
                return True
            except psycopg.Error as e:
                self.ultimo_error = e
                print(f"⚠️ Intento {intento}/{intentos} de conexión falló: {e}")
                if intento < intentos:
                    time.sleep(espera_seg)

        print(f"❌ Error conectando a la base de datos tras {intentos} intentos: {self.ultimo_error}")
        return False

    def close(self):
        if self.conn:
            self.conn.close()

    def ensure_alive(self) -> bool:
        """Se llama antes de cada refresco de pantalla para que la app se
        recupere sola de una caída de internet, sin tener que reiniciarla.

        Si la conexión está cerrada (el internet se cayó y el socket murió),
        reconecta desde cero reusando el retry de connect(). Si sigue abierta
        pero quedó en una transacción abortada (una consulta anterior falló a
        medias), la limpia con rollback() — sin esto, TODAS las consultas
        siguientes seguirían fallando en silencio aunque el internet ya haya
        vuelto, que es justo el síntoma de "ni Refrescar lo arregla".

        `conn.closed` y `conn.info.transaction_status` son datos locales (no
        implican ida y vuelta a la red), así que este chequeo es barato.
        """
        if self.conn is None or self.conn.closed:
            return self.connect()
        try:
            if self.conn.info.transaction_status == TransactionStatus.INERROR:
                self.conn.rollback()
            return True
        except Exception:
            return self.connect()  # el rollback también falló: la conexión está muerta de verdad
