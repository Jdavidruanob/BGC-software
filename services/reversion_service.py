"""Eliminación de un recibo deshaciendo todo lo que hizo.

Pensado para cuando el operador se equivoca al crear un recibo: en vez de
corregir a mano cada efecto (saldo del socio, caja, cuotas marcadas como
pagadas, fondo de administración, libro auxiliar), se elimina el recibo
completo y el sistema revierte cada movimiento.

Efectos que revierte, según `detalle_recibo.tipo_operacion`:

- `aporte`            → resta el monto al saldo del socio y a la caja, y
                        devuelve la papelería al fondo de administración.
- `retiro`            → devuelve el monto al saldo del socio y lo saca de caja.
- `devolucion_total`  → devuelve el saldo al socio, lo reactiva y saca el
                        dinero de la caja.
- `pago_credito` con nro_cuota > 0 → deja la cuota como no pagada, quita la
                        mora del fondo de administración y saca de caja el
                        capital + interés cobrados.
- `pago_credito` con nro_cuota = 0 (abono a capital) → saca el abono de caja y
                        marca la letra para recalcular su plan de cuotas.

Antes de tocar nada valida que la reversión sea coherente (ver `preview`); si
no lo es, no elimina y explica por qué.
"""


class ReversionService:
    def __init__(self, db, liquidaciones):
        self._db = db                    # DBConnection
        self._liquidaciones = liquidaciones

    # --- API pública ------------------------------------------------------

    def preview(self, recibo_id: int) -> dict:
        """Analiza el recibo sin modificar nada.

        Retorna un dict con:
          - `existe`: si el recibo existe.
          - `lineas`: descripción legible de lo que se va a revertir.
          - `caja_delta`: cuánto cambiará el saldo en caja (negativo = sale).
          - `letras_recalculo`: letras cuyo plan de cuotas se recalculará.
          - `bloqueos`: motivos por los que NO se puede revertir (si hay
            alguno, `delete` se niega a ejecutar).
        """
        cursor = self._db.conn.cursor()
        cursor.execute("SELECT id, socio_id, fecha FROM recibos WHERE id = %s", (recibo_id,))
        recibo = cursor.fetchone()
        if not recibo:
            return {"existe": False, "lineas": [], "caja_delta": 0,
                    "letras_recalculo": [], "bloqueos": ["El recibo no existe."]}

        detalles = self._detalles(cursor, recibo_id)
        if not detalles:
            return {"existe": True, "lineas": [], "caja_delta": 0,
                    "letras_recalculo": [],
                    "bloqueos": ["El recibo no tiene operaciones registradas."]}

        lineas = []
        bloqueos = []
        caja_delta = 0
        letras_recalculo = []
        # Saldos proyectados por socio, para detectar si alguno queda negativo.
        saldo_proyectado = {}

        for d in detalles:
            tipo = d["tipo_operacion"]
            monto = d["monto"]
            socio = self._nombre_socio(cursor, d["socio_id"])

            if tipo == "aporte":
                caja_delta -= monto
                papeleria = d["papeleria"] or 0
                saldo_proyectado.setdefault(
                    d["socio_id"], self._saldo_socio(cursor, d["socio_id"])
                )
                saldo_proyectado[d["socio_id"]] -= monto
                extra = f" (+ ${papeleria:,} de papelería)" if papeleria else ""
                lineas.append(f"Aporte de {socio}: se le restan ${monto:,}{extra}")

            elif tipo == "retiro":
                caja_delta += monto
                lineas.append(f"Retiro de {socio}: se le devuelven ${monto:,}")

            elif tipo == "devolucion_total":
                caja_delta += monto
                lineas.append(
                    f"Devolución total de {socio}: se le devuelven ${monto:,} "
                    "y vuelve a quedar activo"
                )

            elif tipo == "pago_credito":
                letra = d["credito_letra"]
                nro = d["nro_cuota"]
                mora = d["abono_mora"] or 0
                if nro and nro > 0:
                    caja_delta -= (monto - mora)
                    posterior = self._cuota_pagada_posterior(cursor, letra, nro, recibo_id)
                    if posterior:
                        bloqueos.append(
                            f"La letra {letra} tiene la cuota #{posterior} pagada "
                            f"después de la #{nro}. Elimina primero el recibo más "
                            "reciente de esa letra."
                        )
                    extra = f" (se quitan ${mora:,} de mora)" if mora else ""
                    lineas.append(
                        f"Letra {letra}, cuota #{nro} de {socio}: vuelve a quedar "
                        f"pendiente{extra}"
                    )
                else:
                    caja_delta -= monto
                    if letra not in letras_recalculo:
                        letras_recalculo.append(letra)
                    lineas.append(
                        f"Letra {letra}: se deshace el abono a capital de "
                        f"${monto:,} de {socio}"
                    )
            else:
                bloqueos.append(f"Operación desconocida '{tipo}': no se sabe cómo revertirla.")

        for socio_id, saldo in saldo_proyectado.items():
            if saldo < 0:
                bloqueos.append(
                    f"{self._nombre_socio(cursor, socio_id)} quedaría con saldo "
                    f"negativo (${saldo:,}). Es probable que ya haya retirado ese dinero."
                )

        saldo_caja = self._saldo_caja(cursor)
        if saldo_caja + caja_delta < 0:
            bloqueos.append(
                f"La caja quedaría en ${saldo_caja + caja_delta:,}. "
                f"Hoy hay ${saldo_caja:,} y esta reversión saca ${-caja_delta:,}."
            )

        return {
            "existe": True,
            "fecha": recibo["fecha"],
            "lineas": lineas,
            "caja_delta": caja_delta,
            "letras_recalculo": letras_recalculo,
            "bloqueos": bloqueos,
        }

    def delete(self, recibo_id: int) -> dict:
        """Elimina el recibo revirtiendo sus efectos. Lanza ValueError si la
        reversión no es válida (ver `preview`)."""
        info = self.preview(recibo_id)
        if info["bloqueos"]:
            raise ValueError("\n".join(f"• {b}" for b in info["bloqueos"]))

        cursor = self._db.conn.cursor()
        try:
            detalles = self._detalles(cursor, recibo_id)
            papeleria_total = 0
            mora_total = 0

            for d in detalles:
                tipo = d["tipo_operacion"]
                monto = d["monto"]

                if tipo == "aporte":
                    cursor.execute(
                        "UPDATE socios SET saldo = saldo - %s WHERE id = %s",
                        (monto, d["socio_id"]),
                    )
                    papeleria_total += d["papeleria"] or 0

                elif tipo == "retiro":
                    cursor.execute(
                        "UPDATE socios SET saldo = saldo + %s WHERE id = %s",
                        (monto, d["socio_id"]),
                    )

                elif tipo == "devolucion_total":
                    cursor.execute(
                        "UPDATE socios SET saldo = saldo + %s, activo = 1 WHERE id = %s",
                        (monto, d["socio_id"]),
                    )

                elif tipo == "pago_credito" and d["nro_cuota"] and d["nro_cuota"] > 0:
                    # La cuota vuelve a quedar pendiente. `mora_exenta` no se
                    # toca: es una decisión del operador, no un efecto del pago.
                    cursor.execute("""
                        UPDATE liquidaciones
                        SET fecha_pago = NULL, interes_mora = 0, mora_aplicada = 0
                        WHERE credito_letra = %s AND nro_cuota = %s
                    """, (d["credito_letra"], d["nro_cuota"]))
                    mora_total += d["abono_mora"] or 0

            # Caja y fondo de administración.
            saldo_caja = self._saldo_caja(cursor)
            self._set_config(cursor, "saldo_en_caja", saldo_caja + info["caja_delta"])

            if papeleria_total:
                total_admin = self._get_config_int(cursor, "total_admin")
                self._set_config(cursor, "total_admin", max(0, total_admin - papeleria_total))
            if mora_total:
                fondo_mora = self._get_config_int(cursor, "total_mora")
                self._set_config(cursor, "total_mora", max(0, fondo_mora - mora_total))

            # Libro auxiliar: se borran las filas del recibo y se corrige el
            # saldo corrido de las posteriores (mismo criterio que al eliminar
            # una operación suelta).
            cursor.execute(
                "SELECT id, monto FROM auxiliar WHERE recibo = %s ORDER BY id ASC",
                (recibo_id,),
            )
            for fila in cursor.fetchall():
                cursor.execute(
                    "UPDATE auxiliar SET saldo = saldo - %s WHERE id > %s",
                    (fila["monto"], fila["id"]),
                )
            cursor.execute("DELETE FROM auxiliar WHERE recibo = %s", (recibo_id,))

            # Notificaciones aún no enviadas: se cancelan para que el socio no
            # reciba un recibo que ya no existe. Las ya enviadas quedan como
            # historial (guardan su propio texto).
            cursor.execute("""
                DELETE FROM notificaciones_whatsapp
                WHERE documento_tipo = 'recibo' AND documento_id = %s
                  AND estado = 'pendiente'
            """, (recibo_id,))

            cursor.execute("DELETE FROM recibos_archivos WHERE recibo_id = %s", (recibo_id,))
            cursor.execute("DELETE FROM detalle_recibo WHERE recibo_id = %s", (recibo_id,))
            cursor.execute("DELETE FROM recibos WHERE id = %s", (recibo_id,))

            self._db.conn.commit()
        except Exception:
            self._db.conn.rollback()
            raise

        # El recálculo del plan de cuotas maneja su propia transacción, así que
        # va después de confirmar la reversión.
        recalculadas, fallidas = [], []
        for letra in info["letras_recalculo"]:
            try:
                self._liquidaciones.recalculate_amortization(letra, 0)
                recalculadas.append(letra)
            except Exception as e:
                print(f"❌ Error recalculando la letra {letra}: {e}")
                fallidas.append(letra)

        return {
            "recibo_id": recibo_id,
            "lineas": info["lineas"],
            "caja_delta": info["caja_delta"],
            "letras_recalculadas": recalculadas,
            "letras_fallidas": fallidas,
        }

    # --- Helpers privados -------------------------------------------------

    def _detalles(self, cursor, recibo_id):
        cursor.execute("""
            SELECT id, tipo_operacion, socio_id, credito_letra, nro_cuota,
                   monto, abono_mora, papeleria
            FROM detalle_recibo WHERE recibo_id = %s ORDER BY id ASC
        """, (recibo_id,))
        return cursor.fetchall()

    def _cuota_pagada_posterior(self, cursor, letra, nro_cuota, recibo_id):
        """Nro de una cuota posterior que siga pagada por OTRO recibo, si la hay.

        Revertir una cuota dejando pagada una posterior deja el crédito con un
        hueco, así que se exige eliminar primero el recibo más reciente.
        """
        cursor.execute("""
            SELECT l.nro_cuota
            FROM liquidaciones l
            WHERE l.credito_letra = %s AND l.nro_cuota > %s
              AND l.fecha_pago IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM detalle_recibo d
                  WHERE d.recibo_id = %s AND d.credito_letra = l.credito_letra
                    AND d.nro_cuota = l.nro_cuota
              )
            ORDER BY l.nro_cuota ASC LIMIT 1
        """, (letra, nro_cuota, recibo_id))
        row = cursor.fetchone()
        return row["nro_cuota"] if row else None

    def _nombre_socio(self, cursor, socio_id):
        cursor.execute("SELECT nombres, apellidos FROM socios WHERE id = %s", (socio_id,))
        row = cursor.fetchone()
        return f"{row['nombres']} {row['apellidos']}" if row else f"socio {socio_id}"

    def _saldo_socio(self, cursor, socio_id):
        cursor.execute("SELECT saldo FROM socios WHERE id = %s", (socio_id,))
        row = cursor.fetchone()
        return row["saldo"] if row else 0

    def _saldo_caja(self, cursor):
        return self._get_config_int(cursor, "saldo_en_caja")

    def _get_config_int(self, cursor, key):
        cursor.execute("SELECT value FROM config WHERE key = %s", (key,))
        row = cursor.fetchone()
        return int(row["value"]) if row else 0

    def _set_config(self, cursor, key, value):
        cursor.execute("""
            INSERT INTO config (key, value) VALUES (%s, %s)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
