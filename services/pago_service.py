from datetime import datetime
from config import get_hoy, get_hoy_str
from services.amortization import calculate_mora
from utils.recibo_generator_pago import generar_recibo_solo_pagos


class PagoService:
    def __init__(self, db_manager):
        self._db = db_manager

    def register(self, recibi_de_id: int, recibi_data: dict, pagos_input: list):
        """
        pagos_input: list de dicts {socio_data, letra_id, n_cuotas, abono_capital}
          - n_cuotas > 0 → modo cuotas manual (excluyente con abono_capital)
          - abono_capital > 0 → modo abono cascada
        Retorna (recibo_id, excel_path, reporte_global).
        Lanza ValueError con mensaje descriptivo para errores de validación.
        """
        tasa_mora = float(self._db.get_config_value("porcentaje_mora") or 0.02)
        hoy = get_hoy()
        fecha = get_hoy_str()

        # --- Fase 1: Validación y preparación ---
        ops_pendientes = []
        pagos_para_recibo = {}

        for item in pagos_input:
            socio_data = item["socio_data"]
            letra_id = item["letra_id"]
            n_cuotas = item.get("n_cuotas", 0)
            abono_capital = item.get("abono_capital", 0)
            nombre_socio = f"{socio_data['nombres']} {socio_data['apellidos']}"

            if n_cuotas > 0 and abono_capital > 0:
                raise ValueError(
                    f"En el pago de {nombre_socio} (Letra {letra_id}) "
                    "seleccione solo una opción: cuotas O abono."
                )
            if n_cuotas == 0 and abono_capital == 0:
                continue

            if letra_id not in pagos_para_recibo:
                saldo_ini = self._db.get_deuda_capital_actual(letra_id)
                pagos_para_recibo[letra_id] = {
                    "socio_data": socio_data, "letra_id": letra_id,
                    "nro_cuotas_pagadas_start": 0, "nro_cuotas_pagadas_end": 0,
                    "valor_capital_consolidado": 0, "interes_consolidado": 0,
                    "mora_consolidada": 0,
                    "saldo_capital_antes_pago": saldo_ini, "saldo_capital_despues_pago": 0,
                }

            if n_cuotas > 0:
                ops_pendientes.append(
                    self._prepare_cuotas(socio_data, letra_id, n_cuotas, hoy, tasa_mora)
                )
            else:
                ops_pendientes.append(
                    self._prepare_abono(socio_data, letra_id, abono_capital, hoy, tasa_mora)
                )

        if not ops_pendientes:
            raise ValueError("No hay operaciones válidas para registrar.")

        # --- Fase 2: Ejecución ---
        cursor = self._db.conn.cursor()
        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi_de_id,))
            recibo_id = cursor.lastrowid

            saldo_caja = self._db.get_config_value_as_int("saldo_en_caja")
            total_admin = self._db.get_config_value_as_int("total_admin")
            mora_total = 0
            reporte_global = {}

            for op in ops_pendientes:
                saldo_caja, mora_total = self._execute_op(
                    cursor, op, recibo_id, fecha, saldo_caja, mora_total,
                    pagos_para_recibo, reporte_global,
                )

            self._db.set_config_value("saldo_en_caja", str(saldo_caja))
            if mora_total > 0:
                self._db.set_config_value("total_admin", str(total_admin + mora_total))

            self._db.conn.commit()

            excel_path = generar_recibo_solo_pagos(
                db_manager=self._db,
                recibo_id=recibo_id,
                recibi_de_data=recibi_data,
                pagos_credito_info=list(pagos_para_recibo.values()),
            )
            return recibo_id, excel_path, reporte_global

        except Exception:
            self._db.conn.rollback()
            raise

    # --- Helpers privados ---

    def _prepare_cuotas(self, socio_data, letra_id, n_cuotas, hoy, tasa_mora):
        cursor = self._db.conn.cursor()
        cursor.execute(
            "SELECT nro_cuota, valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_vencimiento "
            "FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL "
            "ORDER BY nro_cuota LIMIT ?",
            (letra_id, n_cuotas),
        )
        filas = cursor.fetchall()
        nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
        if len(filas) < n_cuotas:
            raise ValueError(
                f"No hay suficientes cuotas pendientes en la letra {letra_id} "
                f"para {nombre}."
            )
        items = []
        mensajes = []
        for fila in filas:
            mora = calculate_mora(fila["fecha_vencimiento"], hoy, fila["valor_cuota"], tasa_mora)
            costo_base = fila["valor_cuota"] + fila["interes_mes"]
            items.append({
                "nro": fila["nro_cuota"], "monto_total": costo_base + mora,
                "monto_base": costo_base, "mora": mora,
                "cap": fila["valor_cuota"], "int": fila["interes_mes"],
            })
            mensajes.append(f"Cuota #{fila['nro_cuota']}")
        return {"tipo": "CUOTAS_MANUAL", "socio_data": socio_data,
                "letra_id": letra_id, "items": items, "mensajes": mensajes}

    def _prepare_abono(self, socio_data, letra_id, dinero_abono, hoy, tasa_mora):
        nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
        pendientes = self._db.get_pending_installments(letra_id)
        vencidas = []
        for cuota in pendientes:
            f_venc = datetime.strptime(cuota["fecha_vencimiento"], "%Y-%m-%d").date()
            if f_venc >= hoy:
                break
            mora = calculate_mora(cuota["fecha_vencimiento"], hoy, cuota["valor_cuota"], tasa_mora)
            base = cuota["valor_cuota"] + cuota["interes_mes"]
            vencidas.append({"data": cuota, "costo_total": base + mora,
                             "monto_base": base, "mora": mora})

        temp = dinero_abono
        pagables = 0
        for v in vencidas:
            if temp >= v["costo_total"]:
                temp -= v["costo_total"]
                pagables += 1
            else:
                if pagables == 0:
                    raise ValueError(
                        f"Abono insuficiente para {nombre} (Letra {letra_id}): "
                        "no cubre la primera cuota vencida."
                    )
                raise ValueError(
                    f"Abono incompleto en letra {letra_id} para {nombre}. "
                    "El monto no alcanza para cubrir las cuotas vencidas parcialmente."
                )

        remanente = 0
        if temp > 0:
            deuda = self._db.get_deuda_capital_actual(letra_id)
            cap_vencidas = sum(v["data"]["valor_cuota"] for v in vencidas[:pagables])
            deuda_futura = deuda - cap_vencidas
            remanente = min(temp, deuda_futura)

        mensajes = [f"Vencida #{v['data']['nro_cuota']}" for v in vencidas[:pagables]]
        if remanente > 0:
            mensajes.append("Abono Capital")
        return {"tipo": "ABONO_CASCADA", "socio_data": socio_data,
                "letra_id": letra_id, "vencidas": vencidas[:pagables],
                "capital_puro": remanente, "mensajes": mensajes}

    def _execute_op(self, cursor, op, recibo_id, fecha, saldo_caja, mora_total,
                    pagos_para_recibo, reporte_global):
        letra_id = op["letra_id"]
        socio_data = op["socio_data"]
        nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
        if nombre not in reporte_global:
            reporte_global[nombre] = []
        reporte_global[nombre].extend(op["mensajes"])

        dict_recibo = pagos_para_recibo[letra_id]

        if op["tipo"] == "CUOTAS_MANUAL":
            items = op["items"]
            dict_recibo["nro_cuotas_pagadas_start"] = items[0]["nro"]
            dict_recibo["nro_cuotas_pagadas_end"] = items[-1]["nro"]
            for it in items:
                cursor.execute("""
                    INSERT INTO detalle_recibo
                        (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                    VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                """, (recibo_id, socio_data["id"], letra_id, it["nro"], it["monto_total"], it["mora"]))
                cursor.execute("""
                    UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ?
                    WHERE credito_letra = ? AND nro_cuota = ?
                """, (it["mora"], 1 if it["mora"] > 0 else 0, letra_id, it["nro"]))
                saldo_caja += it["monto_base"]
                mora_total += it["mora"]
                dict_recibo["valor_capital_consolidado"] += it["cap"]
                dict_recibo["interes_consolidado"] += it["int"]
                dict_recibo["mora_consolidada"] += it["mora"]
                self._db.add_to_auxiliar(
                    fecha=fecha, tipo="Pago Credito", socio=nombre,
                    monto=it["monto_base"], saldo=saldo_caja,
                    recibo=recibo_id, cuota=it["nro"], id_credito=str(letra_id),
                )

        elif op["tipo"] == "ABONO_CASCADA":
            vencidas = op["vencidas"]
            capital_puro = op["capital_puro"]
            for v in vencidas:
                nro = v["data"]["nro_cuota"]
                cursor.execute("""
                    INSERT INTO detalle_recibo
                        (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                    VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                """, (recibo_id, socio_data["id"], letra_id, nro, v["costo_total"], v["mora"]))
                cursor.execute("""
                    UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ?
                    WHERE credito_letra = ? AND nro_cuota = ?
                """, (v["mora"], 1 if v["mora"] > 0 else 0, letra_id, nro))
                saldo_caja += v["monto_base"]
                mora_total += v["mora"]
                dict_recibo["valor_capital_consolidado"] += v["data"]["valor_cuota"]
                dict_recibo["interes_consolidado"] += v["data"]["interes_mes"]
                dict_recibo["mora_consolidada"] += v["mora"]
                self._db.add_to_auxiliar(
                    fecha=fecha, tipo="Pago Credito", socio=nombre,
                    monto=v["monto_base"], saldo=saldo_caja,
                    recibo=recibo_id, cuota=nro, id_credito=str(letra_id),
                )
            if capital_puro > 0:
                cursor.execute("""
                    INSERT INTO detalle_recibo
                        (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto)
                    VALUES (?, 'pago_credito', ?, ?, 0, ?)
                """, (recibo_id, socio_data["id"], letra_id, capital_puro))
                saldo_caja += capital_puro
                self._db.recalcular_tabla_amortizacion(letra_id, capital_puro)
                dict_recibo["valor_capital_consolidado"] += capital_puro
                self._db.add_to_auxiliar(
                    fecha=fecha, tipo="Abono Capital", socio=nombre,
                    monto=capital_puro, saldo=saldo_caja,
                    recibo=recibo_id, cuota=0, id_credito=str(letra_id),
                )
            if vencidas:
                dict_recibo["nro_cuotas_pagadas_start"] = vencidas[0]["data"]["nro_cuota"]
                dict_recibo["nro_cuotas_pagadas_end"] = (
                    "ABONO" if capital_puro > 0 else vencidas[-1]["data"]["nro_cuota"]
                )
            else:
                dict_recibo["nro_cuotas_pagadas_start"] = "ABONO"
                dict_recibo["nro_cuotas_pagadas_end"] = "CAPITAL"

        deuda = dict_recibo["saldo_capital_antes_pago"] - dict_recibo["valor_capital_consolidado"]
        dict_recibo["saldo_capital_despues_pago"] = max(0, int(deuda))
        return saldo_caja, mora_total
