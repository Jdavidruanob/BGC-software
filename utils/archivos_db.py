"""Guarda en la base el Excel de los recibos y liquidaciones que crea la app.

El bot ya guardaba sus archivos en `recibos_archivos` / `liquidaciones_archivos`,
pero la app de escritorio solo los dejaba en disco. El resultado era que la
carpeta `Archivos_BGC` de cada computador tenía un contenido distinto según
dónde se hubiera creado cada recibo. Guardando siempre en la base, la carpeta
pasa a ser un reflejo de la base (ver `utils/sync_recibos.py`).

La app no genera PDF, solo Excel: `pdf_bytes` queda en NULL para estas filas.

Ninguna de estas funciones lanza excepción. Se llaman DESPUÉS de que la
operación ya está confirmada en la base; si fallara el guardado del archivo, lo
correcto es que el operador conserve su recibo y se entere del problema por
consola, no perder una operación financiera ya registrada.
"""

import os


def _leer(excel_path):
    """Bytes del Excel, o None si no hay ruta o no se puede leer."""
    if not excel_path or not os.path.exists(excel_path):
        return None
    with open(excel_path, "rb") as f:
        return f.read()


def guardar_recibo(conn, recibo_id, tipo, excel_path):
    """Sube el Excel del recibo a `recibos_archivos`. Devuelve True si quedó.

    `tipo` es el tipo de operación ('aporte', 'retiro', 'pago', 'combinado',
    'devolucion_total'), el mismo vocabulario que usa la API.
    """
    try:
        contenido = _leer(excel_path)
        if contenido is None:
            print(f"⚠️ Recibo #{recibo_id}: no se encontró el Excel para guardar en la base.")
            return False

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO recibos_archivos (recibo_id, tipo, xlsx_bytes, pdf_bytes)
            VALUES (%s, %s, %s, NULL)
            ON CONFLICT (recibo_id) DO UPDATE SET
                tipo = EXCLUDED.tipo,
                xlsx_bytes = EXCLUDED.xlsx_bytes,
                created_at = CURRENT_TIMESTAMP
        """, (recibo_id, tipo, contenido))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ No se pudo guardar en la base el Excel del recibo #{recibo_id}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def guardar_liquidacion(conn, letra_id, excel_path):
    """Sube el Excel de la liquidación a `liquidaciones_archivos`."""
    try:
        contenido = _leer(excel_path)
        if contenido is None:
            print(f"⚠️ Letra {letra_id}: no se encontró el Excel para guardar en la base.")
            return False

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO liquidaciones_archivos (letra_id, xlsx_bytes, pdf_bytes)
            VALUES (%s, %s, NULL)
            ON CONFLICT (letra_id) DO UPDATE SET
                xlsx_bytes = EXCLUDED.xlsx_bytes,
                created_at = CURRENT_TIMESTAMP
        """, (letra_id, contenido))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ No se pudo guardar en la base el Excel de la letra {letra_id}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
