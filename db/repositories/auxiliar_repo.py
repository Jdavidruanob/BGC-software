from db.connection import DBConnection


class AuxiliarRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def add(self, fecha, tipo, socio, monto, saldo, recibo=None, cuota=None, id_credito=None):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO auxiliar (fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito))
            self.db.conn.commit()
        except Exception as e:
            print(f"❌ Error al añadir al auxiliar: {e}")
            self.db.conn.rollback()

    def find_all(self, limit=10, offset=0, start_date=None, end_date=None,
                 operation_type=None, socio_name=None, numero=None, letra_credito=None):
        query = """
            SELECT id, fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito
            FROM auxiliar WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND fecha >= ?"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= ?"
            params.append(end_date)
        if operation_type:
            query += " AND tipo = ?"
            params.append(operation_type)
        if socio_name:
            query += " AND LOWER(socio) LIKE ?"
            params.append(f"%{socio_name.lower()}%")
        if numero is not None:
            query += " AND recibo = ?"
            params.append(numero)
        if letra_credito:
            query += " AND id_credito = ?"
            params.append(letra_credito)

        query += " ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor = self.db.conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, row)) for row in rows]
        except Exception as e:
            print(f"❌ Error obteniendo operaciones del auxiliar: {e}")
            return []

    def delete(self, op_id):
        try:
            cursor = self.db.conn.cursor()

            cursor.execute("SELECT monto FROM auxiliar WHERE id = ?", (op_id,))
            row = cursor.fetchone()
            if not row:
                return False
            monto_eliminado = row["monto"]

            cursor.execute("DELETE FROM auxiliar WHERE id = ?", (op_id,))
            cursor.execute(
                "UPDATE auxiliar SET saldo = saldo - ? WHERE id > ?",
                (monto_eliminado, op_id),
            )

            cursor.execute("SELECT value FROM config WHERE key = 'saldo_en_caja'")
            config_row = cursor.fetchone()
            saldo_actual = int(config_row["value"]) if config_row else 0
            cursor.execute("""
                INSERT INTO config (key, value) VALUES ('saldo_en_caja', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (str(saldo_actual - monto_eliminado),))

            self.db.conn.commit()
            print(f"🗑️ Operación ID {op_id} eliminada. Saldos recalculados.")
            return True
        except Exception as e:
            print(f"❌ Error eliminando operación auxiliar: {e}")
            self.db.conn.rollback()
            return False
