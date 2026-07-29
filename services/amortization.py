"""
Funciones matemáticas puras para créditos. Sin estado, sin DB.
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from config import parse_db_date

DIAS_GRACIA_MORA = 5


def calculate_mora(fecha_venc_str, hoy: date, valor_cuota: int, tasa_mora: float,
                    dias_gracia: int = DIAS_GRACIA_MORA) -> int:
    """Calcula la mora acumulada de una cuota, cobrada por cada mes de atraso.

    Se dan `dias_gracia` días desde el vencimiento antes de empezar a cobrar
    (por defecto 5: la cuota vence el 1, el 6 ya cobra mora). Pasado ese
    plazo, la mora es `tasa_mora` del valor de la cuota MULTIPLICADA por los
    meses completos de atraso, no un cobro único: si vence el 1 de enero y se
    paga el 6 de julio, van 7 meses de atraso (si se paga antes del 6 de
    julio, son 6).

    `fecha_venc_str` puede venir como texto 'YYYY-MM-DD' (SQLite) o como objeto
    date/datetime (PostgreSQL); parse_db_date normaliza ambos.
    """
    f_venc = parse_db_date(fecha_venc_str)
    f_limite = f_venc + timedelta(days=dias_gracia)
    if hoy < f_limite:
        return 0
    rd = relativedelta(hoy, f_limite)
    meses_atraso = rd.years * 12 + rd.months + 1
    return int(valor_cuota * tasa_mora * meses_atraso)


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


def rebalance_schedule(capital: int, interes: float, cuotas: list, overrides: dict) -> list:
    """Reajusta las cuotas PENDIENTES de un crédito manteniendo el invariante
    (la suma de capital de todas las cuotas = capital del crédito).

    `cuotas`: lista ordenada por nro_cuota de dicts con al menos
        {'nro_cuota', 'valor_cuota', 'pagada' (bool)}.
    `overrides`: {nro_cuota: nuevo_valor_capital} para las cuotas que el usuario
        fija ("ancladas"). Deben ser cuotas pendientes.

    El capital pendiente que no queda anclado se reparte en partes iguales entre
    las cuotas pendientes libres (la última libre absorbe el residuo). Las cuotas
    pagadas no se tocan. El interés de cada cuota pendiente se recalcula sobre el
    saldo de capital, igual que el crédito clásico.

    Retorna la lista de actualizaciones para las cuotas pendientes:
        [{'nro_cuota','valor_cuota','interes_mes','cuota_mensual','saldo_capital'}]
    Lanza ValueError si los valores no permiten cuadrar el crédito.
    """
    capital_pagado = sum(c["valor_cuota"] for c in cuotas if c["pagada"])
    pend_total = capital - capital_pagado
    pendientes = [c for c in cuotas if not c["pagada"]]
    pend_nros = {c["nro_cuota"] for c in pendientes}

    for nro, val in overrides.items():
        if nro not in pend_nros:
            raise ValueError("Solo se pueden editar cuotas pendientes (no pagadas).")
        if val < 0:
            raise ValueError("El valor de una cuota no puede ser negativo.")

    anclado = sum(overrides.values())
    restante = pend_total - anclado
    if restante < 0:
        raise ValueError("Los valores fijados superan el capital pendiente del crédito.")

    libres = [c for c in pendientes if c["nro_cuota"] not in overrides]
    nuevos_cap = dict(overrides)
    if libres:
        base = restante // len(libres)
        for c in libres:
            nuevos_cap[c["nro_cuota"]] = base
        # La última cuota libre absorbe el residuo para cuadrar exacto.
        nuevos_cap[libres[-1]["nro_cuota"]] = restante - base * (len(libres) - 1)
    elif restante != 0:
        raise ValueError("Con todas las cuotas fijadas, la suma no cuadra con el capital.")

    saldo = capital
    updates = []
    for c in cuotas:
        if c["pagada"]:
            saldo = saldo - c["valor_cuota"]
            continue
        cap = int(nuevos_cap[c["nro_cuota"]])
        int_mes = int(round(saldo * interes))
        cuota_mensual = int(cap + int_mes)
        saldo_cap = max(int(saldo - cap), 0)
        updates.append({
            "nro_cuota": c["nro_cuota"], "valor_cuota": cap,
            "interes_mes": int_mes, "cuota_mensual": cuota_mensual,
            "saldo_capital": saldo_cap,
        })
        saldo = saldo_cap

    suma = capital_pagado + sum(u["valor_cuota"] for u in updates)
    if suma != capital:
        raise ValueError("La suma de las cuotas no coincide con el capital del crédito.")
    return updates


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
