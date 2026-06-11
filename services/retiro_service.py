from config import get_hoy_str
from utils.recibo_generator_retiro import generar_recibo_retiro


class RetiroService:
    def __init__(self, db_manager):
        self._db = db_manager

    def register(self, socio_id: int, socio_data: dict, monto: int):
        """
        Retorna (recibo_id, excel_path, nuevo_saldo_caja).
        Lanza ValueError si el saldo del socio es insuficiente.
        """
        if monto > socio_data["saldo"]:
            raise ValueError("El socio no tiene saldo suficiente para este retiro.")

        cursor = self._db.conn.cursor()
        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (socio_id,))
            recibo_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                VALUES (?, 'retiro', ?, ?)
            """, (recibo_id, socio_id, monto))

            cursor.execute(
                "UPDATE socios SET saldo = saldo - ? WHERE id = ?", (monto, socio_id)
            )

            saldo_caja = self._db.get_config_value_as_int("saldo_en_caja")
            nuevo_saldo_caja = saldo_caja - monto
            self._db.set_config_value("saldo_en_caja", str(nuevo_saldo_caja))

            fecha = get_hoy_str()
            nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
            self._db.add_to_auxiliar(
                fecha=fecha, tipo="Retiro", socio=nombre,
                recibo=recibo_id, monto=-monto, saldo=nuevo_saldo_caja,
            )

            self._db.conn.commit()

            excel_path = generar_recibo_retiro(
                recibo_id=recibo_id,
                socio_data={"nombres": socio_data["nombres"], "apellidos": socio_data["apellidos"]},
                monto_retiro=monto,
            )
            return recibo_id, excel_path, nuevo_saldo_caja

        except Exception:
            self._db.conn.rollback()
            raise
