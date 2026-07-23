from datetime import date
from dateutil.relativedelta import relativedelta
from db.connection import DBConnection


class CreditosRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def save(self, socio_ids, capital, interes, no_cuotas):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO creditos (capital, interes, no_cuotas, fecha_inicio)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP) RETURNING letra
            """, (capital, interes, no_cuotas))
            new_letra = cursor.fetchone()["letra"]
            for socio_id in socio_ids:
                cursor.execute(
                    "INSERT INTO socio_credito (socio_id, credito_letra) VALUES (%s, %s)",
                    (socio_id, new_letra),
                )
            self.db.conn.commit()
            print(f"✅ Crédito #{new_letra} creado exitosamente.")
            return new_letra
        except Exception as e:
            print(f"❌ Error al crear crédito: {e}")
            self.db.conn.rollback()
            return None

    def find_active_by_socio_id(self, socio_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT c.letra, c.capital, c.interes, c.no_cuotas
                FROM creditos c
                JOIN socio_credito sc ON c.letra = sc.credito_letra
                WHERE sc.socio_id = %s
            """, (socio_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo créditos activos: {e}")
            return []

    def find_by_letra(self, letra):
        query = """
            SELECT c.*, STRING_AGG(s.nombres || ' ' || s.apellidos, ', ') AS socios
            FROM creditos c
            JOIN socio_credito sc ON sc.credito_letra = c.letra
            JOIN socios s ON s.id = sc.socio_id
            WHERE c.letra = %s
            GROUP BY c.letra
        """
        cursor = self.db.conn.cursor()
        cursor.execute(query, (letra,))
        return cursor.fetchone()

    def update_installments(self, letra_id, new_total_cuotas):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE creditos SET no_cuotas = %s WHERE letra = %s",
                (new_total_cuotas, letra_id),
            )
            print(f"ℹ️ Crédito {letra_id} actualizado a {new_total_cuotas} cuotas.")
            return True
        except Exception as e:
            print(f"❌ Error actualizando número de cuotas: {e}")
            return False

    def save_historical(self, letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data):
        """Inserta un crédito histórico especificando la letra manualmente."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO creditos (letra, capital, interes, no_cuotas, fecha_inicio)
                VALUES (%s, %s, %s, %s, %s) RETURNING letra
            """, (letra, capital, interes, no_cuotas, fecha_inicio))
            fila_letra = cursor.fetchone()
            nueva_letra = letra if letra is not None else fila_letra["letra"]
            print(f"✅ Crédito histórico #{nueva_letra} creado.")

            for socio_id in socios_ids:
                cursor.execute(
                    "INSERT INTO socio_credito (socio_id, credito_letra) VALUES (%s, %s)",
                    (socio_id, nueva_letra),
                )

            for cuota in cuotas_data:
                cursor.execute("""
                    INSERT INTO liquidaciones (
                        credito_letra, nro_cuota, fecha_vencimiento, valor_cuota,
                        interes_mes, cuota_mensual, saldo_capital, fecha_pago
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nueva_letra,
                    cuota["nro_cuota"],
                    cuota["fecha_vencimiento"],
                    cuota["valor_cuota"],
                    cuota["interes_mes"],
                    cuota["cuota_mensual"],
                    cuota["saldo_capital"],
                    cuota["fecha_pago"],
                ))

            self.db.conn.commit()
            return nueva_letra
        except Exception as e:
            self.db.conn.rollback()
            print(f"❌ Error al crear crédito histórico letra {letra}: {e}")
            return None

    def register_complete(self, socio_ids, capital, interes_tasa, n_cuotas):
        """Crea crédito + liquidación + descuenta caja. Retorna (letra_id, nuevo_saldo_caja)."""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute("""
                INSERT INTO creditos (capital, interes, no_cuotas, fecha_inicio)
                VALUES (%s, %s, %s, %s) RETURNING letra
            """, (capital, interes_tasa, n_cuotas, date.today().strftime("%Y-%m-%d")))
            letra_id = cursor.fetchone()["letra"]

            for sid in socio_ids:
                cursor.execute(
                    "INSERT INTO socio_credito (socio_id, credito_letra) VALUES (%s, %s)",
                    (sid, letra_id),
                )

            cuota_base = None
            cuota_final = None
            for redondeo in [10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]:
                posible_cuota = round((capital / n_cuotas) / redondeo) * redondeo
                total_normales = posible_cuota * (n_cuotas - 1)
                ultima_cuota = capital - total_normales
                if 10000 <= ultima_cuota <= posible_cuota * 1.5:
                    cuota_base = posible_cuota
                    cuota_final = ultima_cuota
                    break

            if cuota_base is None:
                cuota_base = capital // n_cuotas
                cuota_final = capital - cuota_base * (n_cuotas - 1)

            cuotas_db = []
            saldo_temp = capital
            fecha_inicio_dt = date.today()
            for i in range(n_cuotas):
                nro = i + 1
                fecha_venc = fecha_inicio_dt + relativedelta(months=+nro)
                cuota_cap = cuota_final if i == n_cuotas - 1 else cuota_base
                interes_val = int(round(saldo_temp * interes_tasa))
                cuota_mensual = int(cuota_cap + interes_val)
                saldo_final = max(int(saldo_temp - cuota_cap), 0)
                cuotas_db.append((
                    letra_id, nro, fecha_venc.strftime("%Y-%m-%d"),
                    int(cuota_cap), interes_val, cuota_mensual, saldo_final,
                ))
                saldo_temp = saldo_final

            cursor.executemany("""
                INSERT INTO liquidaciones
                (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, cuotas_db)

            cursor.execute("SELECT value FROM config WHERE key = 'saldo_en_caja'")
            row = cursor.fetchone()
            saldo_actual = int(row["value"]) if row else 0
            nuevo_saldo = saldo_actual - capital

            self.db.conn.commit()
            return letra_id, nuevo_saldo

        except Exception as e:
            self.db.conn.rollback()
            raise e
