"""Mantiene la carpeta de recibos del computador igual a lo que hay en la base.

La base es la fuente de verdad. Todo recibo —lo cree el bot o lo cree la app—
guarda su Excel en `recibos_archivos`, así que esta carpeta es un reflejo de esa
tabla y no un almacén aparte:

  - Recibo en la base que no está en disco  → se descarga.
  - Archivo en disco cuyo recibo ya no está → se borra.

Lo segundo es lo que evita que un recibo eliminado siga apareciendo en la
carpeta como si existiera. Solo se tocan los archivos con el nombre que genera
el sistema (`Recibo_<n>.xlsx`); cualquier otro archivo que el usuario haya
dejado ahí se respeta.
"""

import os
import re

# Solo se administran los archivos que genera el propio sistema.
_PATRON_RECIBO = re.compile(r"^Recibo_(\d+)\.xlsx$", re.IGNORECASE)


def sincronizar_recibos(conn, output_dir):
    """Deja `output_dir` igual a la tabla `recibos_archivos`.

    Devuelve (descargados, borrados). Nunca lanza: cualquier fallo se reporta
    por consola y no interrumpe el arranque ni el refresco de la app.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        cur = conn.cursor()

        # 1) IDs que hay en la base (barato: sin traer los binarios).
        cur.execute("SELECT recibo_id FROM recibos_archivos ORDER BY recibo_id")
        ids_remotos = {row["recibo_id"] for row in cur.fetchall()}

        # 2) Lo que hay en disco, solo archivos con nombre de recibo.
        en_disco = {}
        for nombre in os.listdir(output_dir):
            m = _PATRON_RECIBO.match(nombre)
            if m:
                en_disco[int(m.group(1))] = os.path.join(output_dir, nombre)

        # 3) Descargar los que faltan.
        faltantes = sorted(ids_remotos - set(en_disco))
        descargados = 0
        if faltantes:
            cur.execute(
                "SELECT recibo_id, xlsx_bytes FROM recibos_archivos WHERE recibo_id = ANY(%s)",
                (faltantes,),
            )
            for row in cur.fetchall():
                rid = row["recibo_id"]
                if row["xlsx_bytes"] is None:
                    continue
                try:
                    destino = os.path.join(output_dir, f"Recibo_{rid}.xlsx")
                    with open(destino, "wb") as f:
                        f.write(bytes(row["xlsx_bytes"]))
                    descargados += 1
                except Exception as e:
                    print(f"❌ No se pudo guardar el recibo {rid}: {e}")

        # 4) Borrar los que ya no existen en la base.
        sobrantes = sorted(set(en_disco) - ids_remotos)
        borrados = 0
        for rid in sobrantes:
            try:
                os.remove(en_disco[rid])
                borrados += 1
            except Exception as e:
                print(f"❌ No se pudo borrar el recibo {rid} de la carpeta: {e}")

        if descargados:
            print(f"📥 {descargados} recibo(s) nuevo(s) descargado(s) a {output_dir}")
        if borrados:
            print(f"🗑️ {borrados} recibo(s) eliminado(s) de la carpeta (ya no están en la base)")
        return descargados, borrados

    except Exception as e:
        print(f"❌ Error sincronizando recibos: {e}")
        return 0, 0
