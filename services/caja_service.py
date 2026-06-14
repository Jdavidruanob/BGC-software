from config import get_hoy_str


class CajaService:
    def __init__(self, config, auxiliar):
        self._config = config
        self._auxiliar = auxiliar

    def get_saldo_caja(self) -> int:
        return self._config.get_int("saldo_en_caja")

    def get_total_admin(self) -> int:
        return self._config.get_int("total_admin")

    def get_porcentaje_mora(self) -> float:
        value = self._config.get("porcentaje_mora")
        return float(value) if value else 0.02

    def adjust_caja(self, monto_ajuste: int, motivo: str, nuevo_saldo: int):
        """Registra un ajuste manual de caja en config y en auxiliar."""
        self._config.set("saldo_en_caja", str(nuevo_saldo))
        self._auxiliar.add(
            fecha=get_hoy_str(),
            tipo=motivo,
            socio="Administracion",
            recibo=None,
            monto=monto_ajuste,
            saldo=nuevo_saldo,
            cuota=None,
            id_credito=None,
        )

    def set_admin_config(self, new_papeleria: int, new_mora: float):
        """Actualiza el fondo de papelería y la tasa de mora."""
        self._config.set("total_admin", str(new_papeleria))
        self._config.set("porcentaje_mora", str(new_mora))
