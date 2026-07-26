from config import get_hoy_str
from utils.archivos_db import guardar_recibo
from utils.recibo_generator_aporte import generar_recibo_solo_aportes

PAPELERIA_POR_APORTE = 3000


class AporteService:
    def __init__(self, db, config, auxiliar):
        self._db = db        # DBConnection
        self._config = config
        self._auxiliar = auxiliar

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
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (%s) RETURNING id", (recibi_de_id,))
            recibo_id = cursor.fetchone()["id"]
            fecha = get_hoy_str()

            saldo_caja = self._config.get_int("saldo_en_caja")
            saldo_admin = self._config.get_int("total_admin")

            # Se deja registrada la papelería cobrada para poder devolverla al
            # fondo si luego se elimina el recibo. El formulario solo informa
            # cuántos aportes la pagan, así que se marca en los primeros: lo que
            # importa es que el total del recibo cuadre con lo cobrado.
            cobrables_restantes = count_cobrables

            for socio_data, monto in aportes:
                socio_id = socio_data["id"]
                papeleria = PAPELERIA_POR_APORTE if cobrables_restantes > 0 else 0
                cobrables_restantes -= 1
                cursor.execute("""
                    INSERT INTO detalle_recibo
                        (recibo_id, tipo_operacion, socio_id, monto, papeleria)
                    VALUES (%s, 'aporte', %s, %s, %s)
                """, (recibo_id, socio_id, monto, papeleria))
                cursor.execute(
                    "UPDATE socios SET saldo = saldo + %s WHERE id = %s", (monto, socio_id)
                )
                saldo_caja += monto
                nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
                self._auxiliar.add(
                    fecha=fecha, tipo="Aporte", socio=nombre,
                    recibo=recibo_id, monto=monto, saldo=saldo_caja,
                )

            self._config.set("saldo_en_caja", str(saldo_caja))
            self._config.set(
                "total_admin", str(saldo_admin + PAPELERIA_POR_APORTE * count_cobrables)
            )
            self._db.conn.commit()

            excel_path = generar_recibo_solo_aportes(
                recibo_id=recibo_id,
                recibi_de_data=recibi_data,
                aportes_info=aportes_for_recibo,
                num_aportes_cobrables=count_cobrables,
            )
            guardar_recibo(self._db.conn, recibo_id, "aporte", excel_path)
            return recibo_id, excel_path

        except Exception:
            self._db.conn.rollback()
            raise
