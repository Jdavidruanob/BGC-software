from config import get_hoy_str
from utils.credit_liquidation_generator import generar_liquidacion_credito


class CreditoService:
    def __init__(self, db_manager):
        self._db = db_manager

    def create(self, socio_ids: list, capital: int, interes_tasa: float,
               n_cuotas: int, socios_data: list):
        """
        socios_data: lista de dicts con 'nombres' y 'apellidos' (para auxiliar y Excel).
        Retorna (letra_id, excel_path).
        """
        letra_id, nuevo_saldo_caja = self._db.registrar_credito_completo(
            socio_ids, capital, interes_tasa, n_cuotas
        )

        try:
            fecha = get_hoy_str()
            nombres_str = ", ".join(
                f"{s['nombres']} {s['apellidos']}" for s in socios_data
            )
            self._db.add_to_auxiliar(
                fecha=fecha,
                tipo="Nuevo Credito",
                socio=nombres_str,
                recibo=None,
                id_credito=letra_id,
                monto=-capital,
                saldo=nuevo_saldo_caja,
                cuota=None,
            )
            self._db.set_config_value("saldo_en_caja", str(nuevo_saldo_caja))
            self._db.conn.commit()

            credit_data = self._db.get_credit_by_letra(letra_id)
            excel_path = generar_liquidacion_credito(
                credit_data=credit_data,
                socios_list=socios_data,
            )
            return letra_id, excel_path

        except Exception:
            self._db.conn.rollback()
            raise
