from config import get_hoy_str
from utils.recibo_generator_aporte import generar_recibo_solo_aportes

PAPELERIA_POR_APORTE = 3000


class AporteService:
    def __init__(self, db_manager):
        self._db = db_manager

    def register(self, recibi_de_id: int, recibi_data: dict,
                 aportes: list, count_cobrables: int):
        """
        aportes: list of (socio_data_dict, monto_int)
        Retorna (recibo_id, excel_path).
        """
        # Pre-computar saldos para el Excel antes de modificar DB
        aportes_for_recibo = []
        for socio_data, monto in aportes:
            saldo_antes = socio_data["saldo"]
            aportes_for_recibo.append((socio_data, monto, saldo_antes, saldo_antes + monto))

        cursor = self._db.conn.cursor()
        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi_de_id,))
            recibo_id = cursor.lastrowid
            fecha = get_hoy_str()

            saldo_caja = self._db.get_config_value_as_int("saldo_en_caja")
            saldo_admin = self._db.get_config_value_as_int("total_admin")

            for socio_data, monto in aportes:
                socio_id = socio_data["id"]
                cursor.execute("""
                    INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                    VALUES (?, 'aporte', ?, ?)
                """, (recibo_id, socio_id, monto))
                cursor.execute(
                    "UPDATE socios SET saldo = saldo + ? WHERE id = ?", (monto, socio_id)
                )
                saldo_caja += monto
                nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
                self._db.add_to_auxiliar(
                    fecha=fecha, tipo="Aporte", socio=nombre,
                    recibo=recibo_id, monto=monto, saldo=saldo_caja,
                )

            self._db.set_config_value("saldo_en_caja", str(saldo_caja))
            self._db.set_config_value(
                "total_admin", str(saldo_admin + PAPELERIA_POR_APORTE * count_cobrables)
            )
            self._db.conn.commit()

            excel_path = generar_recibo_solo_aportes(
                db_manager=self._db,
                recibo_id=recibo_id,
                recibi_de_data=recibi_data,
                aportes_info=aportes_for_recibo,
                num_aportes_cobrables=count_cobrables,
            )
            return recibo_id, excel_path

        except Exception:
            self._db.conn.rollback()
            raise
