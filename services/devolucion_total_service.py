from config import get_hoy_str
from utils.recibo_generator_devolucion_total import generar_recibo_devolucion_total


class DevolucionTotalService:
    """Devolución/retiro TOTAL de un socio: le devuelve todo su saldo, lo
    descuenta de la caja y lo retira de la cooperativa (soft-delete: se marca
    inactivo, se conserva su historial).

    Valida antes de tocar nada: saldo > 0, sin créditos activos y caja
    suficiente. Lanza ValueError si algo no cuadra.
    """

    def __init__(self, db, config, auxiliar, socios, creditos):
        self._db = db          # DBConnection
        self._config = config
        self._auxiliar = auxiliar
        self._socios = socios
        self._creditos = creditos

    def register(self, socio_id: int, socio_data: dict):
        """Retorna (recibo_id, excel_path, nuevo_saldo_caja)."""
        saldo = socio_data["saldo"]

        if saldo <= 0:
            raise ValueError("El socio no tiene saldo para devolver.")

        activos = self._creditos.find_active_by_socio_id(socio_id)
        if activos:
            raise ValueError(
                "El socio tiene créditos activos; primero deben quedar saldados "
                "antes de la devolución total."
            )

        saldo_caja = self._config.get_int("saldo_en_caja")
        if saldo > saldo_caja:
            raise ValueError(
                "La caja no tiene suficiente dinero para devolver el saldo del socio."
            )

        cursor = self._db.conn.cursor()
        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (%s) RETURNING id", (socio_id,))
            recibo_id = cursor.fetchone()["id"]

            cursor.execute("""
                INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                VALUES (%s, 'devolucion_total', %s, %s)
            """, (recibo_id, socio_id, saldo))

            nuevo_saldo_caja = saldo_caja - saldo
            self._config.set("saldo_en_caja", str(nuevo_saldo_caja))

            # Soft-delete: saldo a 0 y socio inactivo.
            self._socios.deactivate(socio_id)

            fecha = get_hoy_str()
            nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
            self._auxiliar.add(
                fecha=fecha, tipo="Devolución total", socio=nombre,
                recibo=recibo_id, monto=-saldo, saldo=nuevo_saldo_caja,
            )

            self._db.conn.commit()

            excel_path = generar_recibo_devolucion_total(
                recibo_id=recibo_id,
                socio_data={"nombres": socio_data["nombres"], "apellidos": socio_data["apellidos"]},
                valor=saldo,
            )
            return recibo_id, excel_path, nuevo_saldo_caja

        except Exception:
            self._db.conn.rollback()
            raise
