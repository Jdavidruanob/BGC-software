"""Pago del salario del administrador.

Equivalente en la app al endpoint `POST /operaciones/salario` de la API, para
que el salario se pueda pagar desde cualquiera de los dos lados y quede
registrado igual.

Es la única operación que no involucra a un socio concreto: el dinero sale de
la caja y va al administrador. El recibo se emite a nombre del socio tesorero
(`config.tesorero_socio_id`) porque `recibos.socio_id` es obligatorio.

Dos valores se guardan en `config`:

- `salario_minimo`: el último monto pagado. No es un acumulado, es memoria para
  proponer el mismo valor la próxima vez.
- `total_salarios`: la suma de todo lo pagado en salarios. Es lo que permite
  saber a fin de año cuánto se destinó a esto sin tener que recorrer el
  histórico. Al eliminar un recibo de salario se descuenta (ver
  `services/reversion_service.py`).

El salario **sale de la caja**: que se lleve una cuenta aparte no cambia que
`saldo_en_caja` se reduce, porque de ahí sale la plata.
"""

from config import get_hoy_str
from utils.archivos_db import guardar_recibo
from utils.recibo_generator_salario import generar_recibo_salario, nombre_mes


class SalarioService:
    def __init__(self, db, config, auxiliar, socios):
        self._db = db              # DBConnection
        self._config = config
        self._auxiliar = auxiliar
        self._socios = socios

    def register(self, monto: int, mes: str = None):
        """Paga el salario del administrador.

        Retorna (recibo_id, excel_path, nuevo_saldo_caja).
        Lanza ValueError si el monto no es válido, si no hay caja suficiente o
        si el socio tesorero configurado no existe.
        """
        monto = int(monto or 0)
        if monto <= 0:
            raise ValueError("El valor del salario debe ser mayor que cero.")

        saldo_caja = self._config.get_int("saldo_en_caja")
        if monto > saldo_caja:
            raise ValueError(
                f"No hay suficiente dinero en caja. "
                f"Disponible: ${saldo_caja:,}, salario: ${monto:,}."
            )

        tesorero_id = self._config.get_int("tesorero_socio_id")
        tesorero = self._socios.find_by_id(tesorero_id)
        if tesorero is None:
            raise ValueError(
                f"No existe el socio tesorero configurado (ID {tesorero_id}). "
                "Revisa 'tesorero_socio_id' en la configuración."
            )

        mes = mes or nombre_mes()

        cursor = self._db.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO recibos (socio_id) VALUES (%s) RETURNING id", (tesorero_id,)
            )
            recibo_id = cursor.fetchone()["id"]
            fecha = get_hoy_str()

            # El detalle es lo que permite revertir el recibo si se elimina.
            cursor.execute("""
                INSERT INTO detalle_recibo
                    (recibo_id, tipo_operacion, socio_id, monto, papeleria)
                VALUES (%s, 'salario', %s, %s, 0)
            """, (recibo_id, tesorero_id, monto))

            nuevo_saldo_caja = saldo_caja - monto
            self._config.set("saldo_en_caja", str(nuevo_saldo_caja))
            self._config.set("salario_minimo", str(monto))
            self._config.set(
                "total_salarios", str(self._config.get_int("total_salarios") + monto)
            )

            self._auxiliar.add(
                fecha=fecha, tipo="Pago Salario", socio="Administracion",
                recibo=recibo_id, monto=-monto, saldo=nuevo_saldo_caja,
            )

            self._db.conn.commit()

            excel_path = generar_recibo_salario(recibo_id=recibo_id, valor=monto, mes=mes)
            guardar_recibo(self._db.conn, recibo_id, "salario", excel_path)
            return recibo_id, excel_path, nuevo_saldo_caja

        except Exception:
            self._db.conn.rollback()
            raise

    # --- Lecturas para la interfaz -------------------------------------------

    def get_ultimo_salario(self) -> int:
        """Último salario pagado, para proponerlo como valor por defecto."""
        return self._config.get_int("salario_minimo")

    def get_total_salarios(self) -> int:
        """Acumulado de todo lo pagado en salarios."""
        return self._config.get_int("total_salarios")
