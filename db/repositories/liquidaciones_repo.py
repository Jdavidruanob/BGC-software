from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from db.connection import DBConnection
from config import get_hoy_str, parse_db_date, fecha_limite_vencida
from services.amortization import rebalance_schedule


class LiquidacionesRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def save_all(self, lista_cuotas):
        try:
            cursor = self.db.conn.cursor()
            cursor.executemany("""
                INSERT INTO liquidaciones (
                    credito_letra, nro_cuota, fecha_vencimiento, valor_cuota,
                    interes_mes, cuota_mensual, saldo_capital, fecha_pago
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, lista_cuotas)
            self.db.conn.commit()
            print("✅ Liquidaciones guardadas.")
        except Exception as e:
            print(f"❌ Error guardando liquidaciones: {e}")

    def get_total_cuotas(self, credito_letra):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT no_cuotas FROM creditos WHERE letra = %s", (credito_letra,))
            result = cursor.fetchone()
            return result["no_cuotas"] if result else 0
        except Exception as e:
            print(f"Error al obtener el total de cuotas para la letra {credito_letra}: {e}")
            return 0

    def find_pending(self, letra_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual,
                       saldo_capital, mora_exenta
                FROM liquidaciones
                WHERE credito_letra = %s AND fecha_pago IS NULL
                ORDER BY nro_cuota ASC
            """, (letra_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo cuotas pendientes: {e}")
            return []

    def find_pending_with_reference(self, letra_id):
        """Como find_pending, pero agrega `fecha_referencia`: la fecha de
        vencimiento de la cuota ANTERIOR (o la fecha de inicio del crédito si
        es la cuota #1). Los DIAS_GRACIA_VENCIDA de plazo para considerar una
        cuota vencida se cuentan desde esa fecha de referencia, no desde el
        vencimiento de la cuota misma (ver `config.esta_vencida`): si la
        cuota anterior venció el 25 de junio, la siguiente (venza cuando
        venza) ya se toma como vencida el 6 de julio.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT l.nro_cuota, l.fecha_vencimiento, l.valor_cuota, l.interes_mes,
                       l.cuota_mensual, l.saldo_capital, l.mora_exenta,
                       COALESCE(prev.fecha_vencimiento, c.fecha_inicio) AS fecha_referencia
                FROM liquidaciones l
                JOIN creditos c ON c.letra = l.credito_letra
                LEFT JOIN liquidaciones prev
                  ON prev.credito_letra = l.credito_letra AND prev.nro_cuota = l.nro_cuota - 1
                WHERE l.credito_letra = %s AND l.fecha_pago IS NULL
                ORDER BY l.nro_cuota ASC
            """, (letra_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo cuotas pendientes con referencia: {e}")
            return []

    def set_mora_exenta(self, letra_id, nro_cuota, exenta: bool):
        """Marca/desmarca una cuota como PENDIENTE forzada.

        Si exenta=True la cuota nunca cuenta como vencida, sin importar su
        fecha: no se muestra como VENCIDA en la liquidación, no aparece en el
        panel de cuotas en mora y un abono a capital no la cobra. Manda la
        marca del operador, no la fecha.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE liquidaciones SET mora_exenta = %s
                WHERE credito_letra = %s AND nro_cuota = %s
            """, (1 if exenta else 0, letra_id, nro_cuota))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"❌ Error actualizando mora_exenta: {e}")
            return False

    def get_current_debt(self, letra_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT valor_cuota, saldo_capital FROM liquidaciones
                WHERE credito_letra = %s AND fecha_pago IS NULL
                ORDER BY nro_cuota ASC LIMIT 1
            """, (letra_id,))
            row = cursor.fetchone()
            if row:
                return row["saldo_capital"] + row["valor_cuota"]
            cursor.execute(
                "SELECT saldo_capital FROM liquidaciones WHERE credito_letra = %s ORDER BY nro_cuota DESC LIMIT 1",
                (letra_id,),
            )
            last = cursor.fetchone()
            return last["saldo_capital"] if last else 0
        except Exception as e:
            print(f"Error calculando deuda actual: {e}")
            return 0

    def find_upcoming(self, hoy_str, hasta_str, limit=5):
        """Próximas cuotas por vencer (no pagadas) entre hoy y `hasta_str`."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT l.credito_letra, l.nro_cuota, l.fecha_vencimiento, l.cuota_mensual,
                       STRING_AGG(s.nombres || ' ' || s.apellidos, ', ') AS socios
                FROM liquidaciones l
                JOIN socio_credito sc ON sc.credito_letra = l.credito_letra
                JOIN socios s ON s.id = sc.socio_id
                WHERE l.fecha_pago IS NULL
                  AND l.fecha_vencimiento >= %s AND l.fecha_vencimiento <= %s
                GROUP BY l.credito_letra, l.nro_cuota, l.fecha_vencimiento, l.cuota_mensual
                ORDER BY l.fecha_vencimiento ASC, l.credito_letra ASC
                LIMIT %s
            """, (hoy_str, hasta_str, limit))
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error obteniendo próximos vencimientos: {e}")
            return []

    def find_overdue(self, hoy_str, limit=5):
        """Cuotas en mora: no pagadas y ya vencidas, dando
        `config.DIAS_GRACIA_VENCIDA` días de plazo desde el vencimiento de la
        cuota ANTERIOR (o la fecha de inicio del crédito si es la cuota #1),
        no desde el vencimiento de la cuota misma.

        Las cuotas marcadas a mano como pendientes (`mora_exenta`) quedan fuera:
        el operador decidió que no cuentan como vencidas.
        """
        try:
            limite = fecha_limite_vencida(parse_db_date(hoy_str))
            cursor = self.db.conn.cursor()
            cursor.execute("""
                WITH ref AS (
                    SELECT l.credito_letra, l.nro_cuota, l.fecha_vencimiento, l.cuota_mensual,
                           l.fecha_pago, l.mora_exenta,
                           COALESCE(prev.fecha_vencimiento, c.fecha_inicio) AS fecha_referencia
                    FROM liquidaciones l
                    JOIN creditos c ON c.letra = l.credito_letra
                    LEFT JOIN liquidaciones prev
                      ON prev.credito_letra = l.credito_letra AND prev.nro_cuota = l.nro_cuota - 1
                )
                SELECT r.credito_letra, r.nro_cuota, r.fecha_vencimiento, r.cuota_mensual,
                       STRING_AGG(s.nombres || ' ' || s.apellidos, ', ') AS socios
                FROM ref r
                JOIN socio_credito sc ON sc.credito_letra = r.credito_letra
                JOIN socios s ON s.id = sc.socio_id
                WHERE r.fecha_pago IS NULL AND r.fecha_referencia <= %s
                  AND COALESCE(r.mora_exenta, 0) = 0
                GROUP BY r.credito_letra, r.nro_cuota, r.fecha_vencimiento, r.cuota_mensual
                ORDER BY r.fecha_vencimiento ASC, r.credito_letra ASC
                LIMIT %s
            """, (limite, limit))
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error obteniendo cuotas en mora: {e}")
            return []

    def rebalance_installments(self, letra_id, overrides):
        """Reajusta las cuotas pendientes fijando algunas (overrides: {nro: valor}).

        Distribuye el capital pendiente restante entre las cuotas libres, respeta
        las cuotas ya pagadas y mantiene el invariante (suma de capital = capital).
        Lanza ValueError con un mensaje claro si los valores no cuadran.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT capital, interes FROM creditos WHERE letra = %s", (letra_id,))
            credito = cursor.fetchone()
            if not credito:
                raise ValueError("Crédito no encontrado.")

            cursor.execute("""
                SELECT nro_cuota, valor_cuota, fecha_pago
                FROM liquidaciones WHERE credito_letra = %s ORDER BY nro_cuota ASC
            """, (letra_id,))
            cuotas = [
                {"nro_cuota": r["nro_cuota"], "valor_cuota": r["valor_cuota"],
                 "pagada": r["fecha_pago"] is not None}
                for r in cursor.fetchall()
            ]

            updates = rebalance_schedule(credito["capital"], credito["interes"], cuotas, overrides)
            for u in updates:
                cursor.execute("""
                    UPDATE liquidaciones
                    SET valor_cuota = %s, interes_mes = %s, cuota_mensual = %s, saldo_capital = %s
                    WHERE credito_letra = %s AND nro_cuota = %s
                """, (u["valor_cuota"], u["interes_mes"], u["cuota_mensual"],
                      u["saldo_capital"], letra_id, u["nro_cuota"]))

            self.db.conn.commit()
            print(f"✅ Cuotas del crédito {letra_id} reajustadas.")
            return True
        except ValueError:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            print(f"❌ Error reajustando cuotas: {e}")
            raise

    def recalculate_amortization(self, letra_id, abono_capital_recien_registrado):
        try:
            cursor = self.db.conn.cursor()
            # Debe ser la MISMA fecha con la que se registró el pago: si el
            # operador está en modo viaje en el tiempo y aquí se usara la fecha
            # real, se tomarían como vencidas cuotas que aún no lo están y el
            # plan quedaría sin recalcular.
            hoy = get_hoy_str()
            limite = fecha_limite_vencida(parse_db_date(hoy))

            cursor.execute(
                "SELECT capital, interes, no_cuotas, fecha_inicio FROM creditos WHERE letra = %s",
                (letra_id,),
            )
            credito = cursor.fetchone()
            if not credito:
                return

            capital_original = credito["capital"]
            tasa_interes = credito["interes"]
            no_cuotas_originales = credito["no_cuotas"]

            cursor.execute(
                "SELECT SUM(valor_cuota) AS total FROM liquidaciones WHERE credito_letra = %s AND fecha_pago IS NOT NULL",
                (letra_id,),
            )
            pagado_cuotas = int(cursor.fetchone()["total"] or 0)

            cursor.execute("""
                SELECT SUM(monto) AS total FROM detalle_recibo
                WHERE credito_letra = %s AND (
                    (tipo_operacion = 'pago_credito' AND nro_cuota = 0) OR
                    tipo_operacion = 'abono_capital'
                )
            """, (letra_id,))
            pagado_abonos = int(cursor.fetchone()["total"] or 0)

            saldo_real_nuevo = capital_original - pagado_cuotas - pagado_abonos

            def _update_no_cuotas():
                cursor.execute(
                    "SELECT MAX(nro_cuota) AS m FROM liquidaciones WHERE credito_letra = %s", (letra_id,)
                )
                ultima = cursor.fetchone()["m"] or 0
                cursor.execute(
                    "UPDATE creditos SET no_cuotas = %s WHERE letra = %s", (ultima, letra_id)
                )

            if saldo_real_nuevo <= 0:
                cursor.execute(
                    "DELETE FROM liquidaciones WHERE credito_letra = %s AND fecha_pago IS NULL",
                    (letra_id,),
                )
                _update_no_cuotas()
                self.db.conn.commit()
                return

            cursor.execute(
                "SELECT valor_cuota FROM liquidaciones WHERE credito_letra = %s AND nro_cuota = 1",
                (letra_id,),
            )
            row_base = cursor.fetchone()
            amortizacion_fija = (
                row_base["valor_cuota"] if row_base else capital_original // no_cuotas_originales
            )

            # El plazo de DIAS_GRACIA_VENCIDA se cuenta desde el vencimiento de
            # la cuota ANTERIOR (o fecha_inicio si es la #1), no desde el de
            # la cuota misma (ver config.esta_vencida).
            cursor.execute("""
                SELECT l.id, l.valor_cuota,
                       COALESCE(prev.fecha_vencimiento, c.fecha_inicio) AS fecha_referencia
                FROM liquidaciones l
                JOIN creditos c ON c.letra = l.credito_letra
                LEFT JOIN liquidaciones prev
                  ON prev.credito_letra = l.credito_letra AND prev.nro_cuota = l.nro_cuota - 1
                WHERE l.credito_letra = %s AND l.fecha_pago IS NULL
            """, (letra_id,))
            pendientes_ref = cursor.fetchall()
            vencidas = [r for r in pendientes_ref if str(r["fecha_referencia"]) <= limite]
            futuras_ids = [r["id"] for r in pendientes_ref if str(r["fecha_referencia"]) > limite]
            capital_en_vencidas = sum(v["valor_cuota"] for v in vencidas)
            capital_para_futuro = max(saldo_real_nuevo - capital_en_vencidas, 0)

            if futuras_ids:
                cursor.execute(
                    "DELETE FROM liquidaciones WHERE id = ANY(%s)", (futuras_ids,)
                )

            if capital_para_futuro == 0:
                _update_no_cuotas()
                self.db.conn.commit()
                return

            cursor.execute(
                "SELECT nro_cuota, fecha_vencimiento FROM liquidaciones WHERE credito_letra = %s ORDER BY nro_cuota DESC LIMIT 1",
                (letra_id,),
            )
            ultimo_reg = cursor.fetchone()

            nro_start = ultimo_reg["nro_cuota"] + 1 if ultimo_reg else 1
            fecha_ref = (
                parse_db_date(ultimo_reg["fecha_vencimiento"])
                if ultimo_reg
                else parse_db_date(credito["fecha_inicio"])
            )
            fecha_start = datetime.combine(fecha_ref, datetime.min.time())

            nuevas_cuotas = []
            saldo_iter = capital_para_futuro
            while saldo_iter > 0:
                fecha_start = fecha_start + relativedelta(months=+1)
                cap_pago = min(saldo_iter, amortizacion_fija)
                int_mes = int((saldo_iter + capital_en_vencidas) * tasa_interes)
                cuota_total = cap_pago + int_mes
                saldo_final_row = (saldo_iter - cap_pago) + capital_en_vencidas
                nuevas_cuotas.append((
                    letra_id, nro_start, fecha_start.strftime("%Y-%m-%d"),
                    int(cap_pago), int(int_mes), int(cuota_total), int(saldo_final_row),
                ))
                saldo_iter -= cap_pago
                nro_start += 1

            cursor.executemany("""
                INSERT INTO liquidaciones
                (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes,
                 cuota_mensual, saldo_capital, interes_mora, mora_aplicada,
                 notif_prev_enviada, notif_venc_enviada, fecha_pago)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 0, NULL)
            """, nuevas_cuotas)

            cursor.execute(
                "SELECT MAX(nro_cuota) AS m FROM liquidaciones WHERE credito_letra = %s", (letra_id,)
            )
            nueva_ultima = cursor.fetchone()["m"]
            if nueva_ultima:
                cursor.execute(
                    "UPDATE creditos SET no_cuotas = %s WHERE letra = %s", (nueva_ultima, letra_id)
                )

            self.db.conn.commit()
            print("✅ Tabla recalculada y cuotas actualizadas correctamente.")

        except Exception as e:
            print(f"❌ Error recalculando tabla: {e}")
            self.db.conn.rollback()
