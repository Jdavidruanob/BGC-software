from config import get_hoy, get_hoy_str, esta_vencida
from services.amortization import calculate_mora
from utils.archivos_db import guardar_recibo
from utils.recibo_generator_pago import generar_recibo_solo_pagos


class PagoService:
    def __init__(self, db, liquidaciones, auxiliar, config):
        self._db = db                # DBConnection
        self._liquidaciones = liquidaciones
        self._auxiliar = auxiliar
        self._config = config

    def preview(self, pagos_input: list) -> dict:
        """Calcula (sin escribir nada) qué se va a cobrar, incluida la mora
        exacta de cada cuota. Úsalo para mostrarle al operador un resumen
        antes de confirmar el registro del recibo."""
        ops_pendientes, _ = self._preparar_operaciones(pagos_input)
        reporte = {}
        for op in ops_pendientes:
            nombre = f"{op['socio_data']['nombres']} {op['socio_data']['apellidos']}"
            reporte.setdefault(nombre, []).extend(op["mensajes"])
        return reporte

    def register(self, recibi_de_id: int, recibi_data: dict, pagos_input: list):
        """
        pagos_input: list de dicts {socio_data, letra_id, n_cuotas, abono_capital}
          - n_cuotas > 0 → modo cuotas manual (excluyente con abono_capital)
          - abono_capital > 0 → modo abono cascada
        Retorna (recibo_id, excel_path, reporte_global).
        Lanza ValueError con mensaje descriptivo para errores de validación.
        """
        fecha = get_hoy_str()
        ops_pendientes, pagos_para_recibo = self._preparar_operaciones(pagos_input)

        if not ops_pendientes:
            raise ValueError("No hay operaciones válidas para registrar.")

        # --- Fase 2: Ejecución ---
        cursor = self._db.conn.cursor()
        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (%s) RETURNING id", (recibi_de_id,))
            recibo_id = cursor.fetchone()["id"]

            saldo_caja = self._config.get_int("saldo_en_caja")
            fondo_mora = self._config.get_int("total_mora")
            mora_total = 0
            reporte_global = {}

            for op in ops_pendientes:
                saldo_caja, mora_total = self._execute_op(
                    cursor, op, recibo_id, fecha, saldo_caja, mora_total,
                    pagos_para_recibo, reporte_global,
                )

            self._config.set("saldo_en_caja", str(saldo_caja))
            if mora_total > 0:
                self._config.set("total_mora", str(fondo_mora + mora_total))

            self._db.conn.commit()

            excel_path = generar_recibo_solo_pagos(
                get_total_cuotas=self._liquidaciones.get_total_cuotas,
                recibo_id=recibo_id,
                recibi_de_data=recibi_data,
                pagos_credito_info=list(pagos_para_recibo.values()),
            )
            guardar_recibo(self._db.conn, recibo_id, "pago", excel_path)
            return recibo_id, excel_path, reporte_global

        except Exception:
            self._db.conn.rollback()
            raise

    # --- Helpers privados ---

    def _preparar_operaciones(self, pagos_input: list):
        """Fase 1 (solo lecturas): valida y calcula cada operación, incluida
        la mora automática de cada cuota. No escribe nada en la base."""
        hoy = get_hoy()
        tasa_mora = float(self._config.get("porcentaje_mora") or 0.02)

        ops_pendientes = []
        pagos_para_recibo = {}

        for item in pagos_input:
            socio_data = item["socio_data"]
            letra_id = item["letra_id"]
            n_cuotas = item.get("n_cuotas", 0)
            abono_capital = item.get("abono_capital", 0)
            cobrar_mora = item.get("cobrar_mora", True)
            nombre_socio = f"{socio_data['nombres']} {socio_data['apellidos']}"

            if n_cuotas > 0 and abono_capital > 0:
                raise ValueError(
                    f"En el pago de {nombre_socio} (Letra {letra_id}) "
                    "seleccione solo una opción: cuotas O abono."
                )
            if n_cuotas == 0 and abono_capital == 0:
                continue

            if letra_id not in pagos_para_recibo:
                saldo_ini = self._liquidaciones.get_current_debt(letra_id)
                pagos_para_recibo[letra_id] = {
                    "socio_data": socio_data, "letra_id": letra_id,
                    "nro_cuotas_pagadas_start": 0, "nro_cuotas_pagadas_end": 0,
                    "valor_capital_consolidado": 0, "interes_consolidado": 0,
                    "mora_consolidada": 0,
                    "saldo_capital_antes_pago": saldo_ini, "saldo_capital_despues_pago": 0,
                }

            if n_cuotas > 0:
                ops_pendientes.append(
                    self._prepare_cuotas(socio_data, letra_id, n_cuotas, hoy, tasa_mora, cobrar_mora)
                )
            else:
                ops_pendientes.append(
                    self._prepare_abono(socio_data, letra_id, abono_capital, hoy, tasa_mora, cobrar_mora)
                )

        return ops_pendientes, pagos_para_recibo

    def _prepare_cuotas(self, socio_data, letra_id, n_cuotas, hoy, tasa_mora, cobrar_mora=True):
        cursor = self._db.conn.cursor()
        cursor.execute(
            "SELECT nro_cuota, valor_cuota, interes_mes, cuota_mensual, saldo_capital, "
            "fecha_vencimiento, mora_exenta "
            "FROM liquidaciones WHERE credito_letra = %s AND fecha_pago IS NULL "
            "ORDER BY nro_cuota LIMIT %s",
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
            mora = 0
            if cobrar_mora and not fila["mora_exenta"]:
                mora = calculate_mora(fila["fecha_vencimiento"], hoy, fila["valor_cuota"], tasa_mora)
            costo_base = fila["valor_cuota"] + fila["interes_mes"]
            items.append({
                "nro": fila["nro_cuota"], "monto_total": costo_base + mora,
                "monto_base": costo_base, "mora": mora,
                "cap": fila["valor_cuota"], "int": fila["interes_mes"],
            })
            etiqueta = f"Cuota #{fila['nro_cuota']}"
            if mora > 0:
                etiqueta += f" (+ ${mora:,} de mora)"
            mensajes.append(etiqueta)
        return {"tipo": "CUOTAS_MANUAL", "socio_data": socio_data,
                "letra_id": letra_id, "items": items, "mensajes": mensajes}

    def _prepare_abono(self, socio_data, letra_id, dinero_abono, hoy, tasa_mora, cobrar_mora=True):
        nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
        pendientes = self._liquidaciones.find_pending_with_reference(letra_id)
        vencidas = []
        for cuota in pendientes:
            # Una cuota marcada a mano en la liquidación NO es vencida, sin
            # importar la fecha: la marca del operador es la que manda.
            if cuota["mora_exenta"]:
                continue
            if not esta_vencida(cuota["fecha_referencia"], hoy):
                break
            base = cuota["valor_cuota"] + cuota["interes_mes"]
            mora = calculate_mora(cuota["fecha_vencimiento"], hoy, cuota["valor_cuota"], tasa_mora) if cobrar_mora else 0
            vencidas.append({"data": cuota, "costo_total": base + mora,
                             "monto_base": base, "mora": mora})

        # El abono a capital digitado nunca se reduce: primero salda el
        # CAPITAL de las cuotas vencidas (en orden, porque ya se deben) y lo
        # que sobra es el abono real a cuotas futuras. El interés (y la
        # mora) de cada vencida se cobra aparte, sumado encima, jamás
        # restado de lo digitado.
        temp_capital = dinero_abono
        for i, v in enumerate(vencidas):
            capital_cuota = v["data"]["valor_cuota"]
            if temp_capital < capital_cuota:
                if i == 0:
                    raise ValueError(
                        f"Abono insuficiente para {nombre} (Letra {letra_id}): "
                        f"no cubre el capital (${capital_cuota:,}) de la cuota "
                        f"vencida #{v['data']['nro_cuota']}."
                    )
                raise ValueError(
                    f"Abono incompleto en letra {letra_id} para {nombre}. "
                    f"No alcanza para cubrir el capital de la cuota vencida "
                    f"#{v['data']['nro_cuota']}."
                )
            temp_capital -= capital_cuota

        deuda = self._liquidaciones.get_current_debt(letra_id)
        cap_vencidas = sum(v["data"]["valor_cuota"] for v in vencidas)
        deuda_futura = deuda - cap_vencidas
        capital_puro = min(temp_capital, deuda_futura)

        # El resumen se cuenta como se ve en el recibo: el abono a capital
        # completo (capital de vencidas + a futuro, sin desglosar) y aparte
        # el interés (y mora) de cada vencida, que se suma al total.
        cap_total_aplicado = capital_puro + cap_vencidas
        mensajes = []
        if cap_total_aplicado > 0:
            mensajes.append(f"Abono Capital: ${cap_total_aplicado:,}")
        for v in vencidas:
            etiqueta = (
                f"⚠️ Cuota #{v['data']['nro_cuota']} vencida: se cobra su "
                f"interés ${v['data']['interes_mes']:,}"
            )
            if v["mora"] > 0:
                etiqueta += f" + ${v['mora']:,} de mora"
            mensajes.append(etiqueta)
        if vencidas:
            total_pagar = cap_total_aplicado + sum(
                v["data"]["interes_mes"] + v["mora"] for v in vencidas
            )
            mensajes.append(f"Total a pagar: ${total_pagar:,}")

        return {"tipo": "ABONO_CASCADA", "socio_data": socio_data,
                "letra_id": letra_id, "vencidas": vencidas,
                "capital_puro": capital_puro, "mensajes": mensajes}

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
                    VALUES (%s, 'pago_credito', %s, %s, %s, %s, %s)
                """, (recibo_id, socio_data["id"], letra_id, it["nro"], it["monto_total"], it["mora"]))
                cursor.execute("""
                    UPDATE liquidaciones
                    SET fecha_pago = %s, interes_mora = %s, mora_aplicada = %s
                    WHERE credito_letra = %s AND nro_cuota = %s
                """, (fecha, it["mora"], 1 if it["mora"] > 0 else 0, letra_id, it["nro"]))
                saldo_caja += it["monto_base"]
                mora_total += it["mora"]
                dict_recibo["valor_capital_consolidado"] += it["cap"]
                dict_recibo["interes_consolidado"] += it["int"]
                dict_recibo["mora_consolidada"] += it["mora"]
                self._auxiliar.add(
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
                    VALUES (%s, 'pago_credito', %s, %s, %s, %s, %s)
                """, (recibo_id, socio_data["id"], letra_id, nro, v["costo_total"], v["mora"]))
                cursor.execute("""
                    UPDATE liquidaciones
                    SET fecha_pago = %s, interes_mora = %s, mora_aplicada = %s
                    WHERE credito_letra = %s AND nro_cuota = %s
                """, (fecha, v["mora"], 1 if v["mora"] > 0 else 0, letra_id, nro))
                saldo_caja += v["monto_base"]
                mora_total += v["mora"]
                dict_recibo["valor_capital_consolidado"] += v["data"]["valor_cuota"]
                dict_recibo["interes_consolidado"] += v["data"]["interes_mes"]
                dict_recibo["mora_consolidada"] += v["mora"]
            if capital_puro > 0:
                cursor.execute("""
                    INSERT INTO detalle_recibo
                        (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto)
                    VALUES (%s, 'pago_credito', %s, %s, 0, %s)
                """, (recibo_id, socio_data["id"], letra_id, capital_puro))
                saldo_caja += capital_puro
                self._liquidaciones.recalculate_amortization(letra_id, capital_puro)
                dict_recibo["valor_capital_consolidado"] += capital_puro

            # Un solo movimiento de caja "Abono Capital" con todo sumado
            # (capital de vencidas + capital a futuro + interés de las
            # vencidas): la mora no entra porque no va a caja.
            monto_abono_total = capital_puro + sum(v["monto_base"] for v in vencidas)
            if monto_abono_total > 0:
                self._auxiliar.add(
                    fecha=fecha, tipo="Abono Capital", socio=nombre,
                    monto=monto_abono_total, saldo=saldo_caja,
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
