"""
Funciones matemáticas puras para créditos. Sin estado, sin DB.
"""
from datetime import date
from dateutil.relativedelta import relativedelta

from config import parse_db_date


def calculate_mora(fecha_venc_str, hoy: date, valor_cuota: int, tasa_mora: float) -> int:
    """Retorna el monto de mora si hoy supera el período de gracia de 1 mes.

    `fecha_venc_str` puede venir como texto 'YYYY-MM-DD' (SQLite) o como objeto
    date/datetime (PostgreSQL); parse_db_date normaliza ambos.
    """
    f_venc = parse_db_date(fecha_venc_str)
    f_limite = f_venc + relativedelta(months=+1)
    return int(valor_cuota * tasa_mora) if hoy > f_limite else 0


def round_installments(capital: int, n_cuotas: int) -> tuple[int, int]:
    """
    Divide capital en n cuotas con redondeo inteligente.
    Retorna (cuota_base, cuota_final) donde cuota_final puede diferir ligeramente.
    """
    for redondeo in [10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]:
        posible = round((capital / n_cuotas) / redondeo) * redondeo
        ultima = capital - posible * (n_cuotas - 1)
        if 10000 <= ultima <= posible * 1.5:
            return posible, ultima
    cuota_base = capital // n_cuotas
    return cuota_base, capital - cuota_base * (n_cuotas - 1)


def build_manual_schedule(
    letra_id: int,
    capital: int,
    interes: float,
    n_cuotas: int,
    cuota_inicial: int,
    fecha_inicio: date,
) -> list[tuple]:
    """Tabla de amortización de un crédito manual/histórico a partir de una cuota dada.

    A diferencia del crédito clásico, aquí NO se calcula la cuota: se recibe
    `cuota_inicial` (la parte de capital de cada cuota). La última cuota absorbe
    el residuo (capital - cuota_inicial * (n_cuotas - 1)), de modo que la suma de
    capital de todas las cuotas = capital del crédito (invariante). El interés se
    calcula sobre el saldo de capital, igual que el crédito clásico.

    Retorna filas listas para INSERT INTO liquidaciones:
    (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes,
     cuota_mensual, saldo_capital)
    """
    cuota_final = capital - cuota_inicial * (n_cuotas - 1)
    rows = []
    saldo = capital
    for i in range(n_cuotas):
        nro = i + 1
        fecha_venc = fecha_inicio + relativedelta(months=+nro)
        cap_pago = cuota_final if i == n_cuotas - 1 else cuota_inicial
        int_mes = int(round(saldo * interes))
        cuota_mensual = int(cap_pago + int_mes)
        saldo_final = max(int(saldo - cap_pago), 0)
        rows.append((
            letra_id, nro, fecha_venc.strftime("%Y-%m-%d"),
            int(cap_pago), int_mes, cuota_mensual, saldo_final,
        ))
        saldo = saldo_final
    return rows


def build_amortization_schedule(
    letra_id: int,
    capital: int,
    interes: float,
    n_cuotas: int,
    fecha_inicio: date,
) -> list[tuple]:
    """
    Calcula la tabla de amortización completa.
    Retorna lista de tuplas listas para INSERT INTO liquidaciones:
    (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital)
    """
    cuota_base, cuota_final = round_installments(capital, n_cuotas)
    rows = []
    saldo = capital
    for i in range(n_cuotas):
        nro = i + 1
        fecha_venc = fecha_inicio + relativedelta(months=+nro)
        cap_pago = cuota_final if i == n_cuotas - 1 else cuota_base
        int_mes = int(round(saldo * interes))
        cuota_mensual = int(cap_pago + int_mes)
        saldo_final = max(int(saldo - cap_pago), 0)
        rows.append((
            letra_id, nro, fecha_venc.strftime("%Y-%m-%d"),
            int(cap_pago), int_mes, cuota_mensual, saldo_final,
        ))
        saldo = saldo_final
    return rows
