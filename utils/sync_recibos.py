"""Sincroniza a la PC los recibos generados por el bot/API.

El bot (y la API) guardan cada recibo en la tabla `recibos_archivos` de la base
compartida (xlsx + pdf). Esta utilidad los baja a la carpeta de recibos del
computador para que el usuario los tenga y los pueda abrir/imprimir, sin volver
a bajar los que ya tiene.
"""

import os


def sincronizar_recibos(conn, output_dir):
    """Descarga los recibos que aún no estén en `output_dir`.

    Devuelve cuántos archivos nuevos se bajaron. Nunca lanza: cualquier fallo se
    reporta por consola y no interrumpe el arranque ni el refresco de la app.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        cur = conn.cursor()

        # 1) IDs remotos (barato: sin traer los binarios).
        cur.execute("SELECT recibo_id FROM recibos_archivos ORDER BY recibo_id")
        ids_remotos = [row["recibo_id"] for row in cur.fetchall()]

        # 2) Solo los que no estén ya en disco.
        faltantes = [
            rid for rid in ids_remotos
            if not os.path.exists(os.path.join(output_dir, f"Recibo_{rid}.xlsx"))
        ]
        if not faltantes:
            return 0

        # 3) Traer los binarios solo de los faltantes y guardarlos.
        cur.execute(
            "SELECT recibo_id, xlsx_bytes, pdf_bytes FROM recibos_archivos "
            "WHERE recibo_id = ANY(%s)",
            (faltantes,),
        )
        nuevos = 0
        for row in cur.fetchall():
            rid = row["recibo_id"]
            try:
                with open(os.path.join(output_dir, f"Recibo_{rid}.xlsx"), "wb") as f:
                    f.write(bytes(row["xlsx_bytes"]))
                if row["pdf_bytes"]:
                    with open(os.path.join(output_dir, f"Recibo_{rid}.pdf"), "wb") as f:
                        f.write(bytes(row["pdf_bytes"]))
                nuevos += 1
            except Exception as e:
                print(f"❌ No se pudo guardar el recibo {rid}: {e}")

        if nuevos:
            print(f"📥 {nuevos} recibo(s) nuevo(s) descargado(s) a {output_dir}")
        return nuevos

    except Exception as e:
        print(f"❌ Error sincronizando recibos: {e}")
        return 0
