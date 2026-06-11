import sqlite3
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from db.connection import DBConnection


class LiquidacionesRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def save_all(self, lista_cuotas):
        try:
            self.db.conn.executemany("""
                INSERT INTO liquidaciones (
                    credito_letra, nro_cuota, fecha_vencimiento, valor_cuota,
                    interes_mes, cuota_mensual, saldo_capital, fecha_pago
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, lista_cuotas)
            self.db.conn.commit()
            print("✅ Liquidaciones guardadas.")
        except sqlite3.Error as e:
            print(f"❌ Error guardando liquidaciones: {e}")

    def get_total_cuotas(self, credito_letra):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT no_cuotas FROM creditos WHERE letra = ?", (credito_letra,))
            result = cursor.fetchone()
            return result["no_cuotas"] if result else 0
        except sqlite3.Error as e:
            print(f"Error al obtener el total de cuotas para la letra {credito_letra}: {e}")
            return 0

    def find_pending(self, letra_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital
                FROM liquidaciones
                WHERE credito_letra = ? AND fecha_pago IS NULL
                ORDER BY nro_cuota ASC
            """, (letra_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo cuotas pendientes: {e}")
            return []

    def get_current_debt(self, letra_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT valor_cuota, saldo_capital FROM liquidaciones
                WHERE credito_letra = ? AND fecha_pago IS NULL
                ORDER BY nro_cuota ASC LIMIT 1
            """, (letra_id,))
            row = cursor.fetchone()
            if row:
                return row["saldo_capital"] + row["valor_cuota"]
            cursor.execute(
                "SELECT saldo_capital FROM liquidaciones WHERE credito_letra = ? ORDER BY nro_cuota DESC LIMIT 1",
                (letra_id,),
            )
            last = cursor.fetchone()
            return last["saldo_capital"] if last else 0
        except Exception as e:
            print(f"Error calculando deuda actual: {e}")
            return 0

    def recalculate_amortization(self, letra_id, abono_capital_recien_registrado):
        try:
            cursor = self.db.conn.cursor()
            hoy = date.today().strftime("%Y-%m-%d")

            cursor.execute(
                "SELECT capital, interes, no_cuotas, fecha_inicio FROM creditos WHERE letra = ?",
                (letra_id,),
            )
            credito = cursor.fetchone()
            if not credito:
                return

            capital_original = credito["capital"]
            tasa_interes = credito["interes"]
            no_cuotas_originales = credito["no_cuotas"]

            cursor.execute(
                "SELECT SUM(valor_cuota) FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NOT NULL",
                (letra_id,),
            )
            pagado_cuotas = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT SUM(monto) FROM detalle_recibo
                WHERE credito_letra = ? AND (
                    (tipo_operacion = 'pago_credito' AND nro_cuota = 0) OR
                    tipo_operacion = 'abono_capital'
                )
            """, (letra_id,))
            pagado_abonos = cursor.fetchone()[0] or 0

            saldo_real_nuevo = capital_original - pagado_cuotas - pagado_abonos

            def _update_no_cuotas():
                cursor.execute(
                    "SELECT MAX(nro_cuota) FROM liquidaciones WHERE credito_letra = ?", (letra_id,)
                )
                ultima = cursor.fetchone()[0] or 0
                cursor.execute(
                    "UPDATE creditos SET no_cuotas = ? WHERE letra = ?", (ultima, letra_id)
                )

            if saldo_real_nuevo <= 0:
                cursor.execute(
                    "DELETE FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL",
                    (letra_id,),
                )
                _update_no_cuotas()
                self.db.conn.commit()
                return

            cursor.execute(
                "SELECT valor_cuota FROM liquidaciones WHERE credito_letra = ? AND nro_cuota = 1",
                (letra_id,),
            )
            row_base = cursor.fetchone()
            amortizacion_fija = (
                row_base["valor_cuota"] if row_base else capital_original // no_cuotas_originales
            )

            cursor.execute("""
                SELECT id, valor_cuota FROM liquidaciones
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento < ?
            """, (letra_id, hoy))
            vencidas = cursor.fetchall()
            capital_en_vencidas = sum(v["valor_cuota"] for v in vencidas)
            capital_para_futuro = max(saldo_real_nuevo - capital_en_vencidas, 0)

            cursor.execute("""
                DELETE FROM liquidaciones
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento >= ?
            """, (letra_id, hoy))

            if capital_para_futuro == 0:
                _update_no_cuotas()
                self.db.conn.commit()
                return

            cursor.execute(
                "SELECT nro_cuota, fecha_vencimiento FROM liquidaciones WHERE credito_letra = ? ORDER BY nro_cuota DESC LIMIT 1",
                (letra_id,),
            )
            ultimo_reg = cursor.fetchone()

            nro_start = ultimo_reg["nro_cuota"] + 1 if ultimo_reg else 1
            fecha_start = (
                datetime.strptime(ultimo_reg["fecha_vencimiento"], "%Y-%m-%d")
                if ultimo_reg
                else datetime.strptime(credito["fecha_inicio"][:10], "%Y-%m-%d")
            )

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
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, NULL)
            """, nuevas_cuotas)

            cursor.execute(
                "SELECT MAX(nro_cuota) FROM liquidaciones WHERE credito_letra = ?", (letra_id,)
            )
            nueva_ultima = cursor.fetchone()[0]
            if nueva_ultima:
                cursor.execute(
                    "UPDATE creditos SET no_cuotas = ? WHERE letra = ?", (nueva_ultima, letra_id)
                )

            self.db.conn.commit()
            print("✅ Tabla recalculada y cuotas actualizadas correctamente.")

        except Exception as e:
            print(f"❌ Error recalculando tabla: {e}")
            self.db.conn.rollback()
