from db.connection import DBConnection


class RecibosRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def create_aporte(self, recibi_de_id, aportes):
        """
        recibi_de_id: socio que entrega el dinero.
        aportes: lista de tuplas [(socio_id, monto), ...].
        Retorna el id del recibo creado.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi_de_id,))
            recibo_id = cursor.lastrowid

            for socio_id, monto in aportes:
                cursor.execute("""
                    INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                    VALUES (?, 'aporte', ?, ?)
                """, (recibo_id, socio_id, monto))
                cursor.execute(
                    "UPDATE socios SET saldo = saldo + ? WHERE id = ?",
                    (monto, socio_id),
                )

            self.db.conn.commit()
            return recibo_id
        except Exception as e:
            self.db.conn.rollback()
            print(f"❌ Error creando recibo de aporte: {e}")
            return None
