# views/forms/form_pago_credito.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import datetime, date
from collections import defaultdict 
from dateutil.relativedelta import relativedelta

# IMPORTAR AHORA DESDE EL NUEVO ARCHIVO ESPECÍFICO DE PAGOS
from utils.recibo_generator_pago import generar_recibo_solo_pagos, DEFAULT_GASTOS_ADMIN, MAX_CREDITO_ROWS_IN_TEMPLATE

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormPagoCredito(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page = None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.pagos_widgets = []  # [(combo_socio, letras_container, wrapper_widget)]

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 0, 20, 30)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)


        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(50)
        self.combo_recibi_de.setMaximumHeight(50)
        self.combo_recibi_de.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)

        # Sección dinámicos de pagos
        pagos_label = QLabel("Pagos a registrar:")
        pagos_label.setObjectName("FormLabel")
        main_layout.addWidget(pagos_label)

        self.pagos_container = QVBoxLayout()
        self.pagos_container.setSpacing(12)
        main_layout.addLayout(self.pagos_container)

        # Botón para agregar socio que pagará
        self.btn_agregar_pago = QPushButton(" Agregar pago de socio")
        self.btn_agregar_pago.setObjectName("AddPagoButton")
        self.btn_agregar_pago.setIcon(load_svg_icon("icons/plus.svg"))
        self.btn_agregar_pago.setIconSize(QSize(20, 20))
        self.btn_agregar_pago.setMinimumHeight(36)
        self.btn_agregar_pago.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_agregar_pago.clicked.connect(self.agregar_pago)
        main_layout.addWidget(self.btn_agregar_pago, alignment=Qt.AlignLeft)

        # Espacio y botón registrar
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Registrar Pago")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial
        self.load_socios()

        # Aplica estilos
        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_pago_credito.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        """Carga lista de socios para combo_recibi_de."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_recibi_de.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_pago(self):
        """Agrega bloque para un socio + sus letras a pagar."""
        # Combo socio
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocioPago")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            combo.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)

        # Botón agregar letra
        btn_add_letra = QPushButton(" Agregar letra a pagar")
        btn_add_letra.setObjectName("AddLetraButton")
        btn_add_letra.setIcon(load_svg_icon("icons/plus.svg"))
        btn_add_letra.setIconSize(QSize(16, 16))
        btn_add_letra.setMinimumHeight(36)
        btn_add_letra.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Contenedor dinámico de letras
        letras_container = QVBoxLayout()
        letras_container.setSpacing(8)

        def agregar_letra():
            letra_row = QHBoxLayout()
            letra_row.setContentsMargins(0,0,0,0)

            letra_combo = NoScrollComboBox()
            letra_combo.setObjectName("LetraCombo")
            letra_combo.setMinimumHeight(34)
            letra_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            socio = combo.currentData()
            if socio:
                letras = self.db.get_letras_by_socio_id(socio['id'])
                if not letras:
                    show_info(self, "Sin créditos", "Este socio no tiene letras activas.")
                    return
                for l in letras:
                    texto = (
                        f"Letra {l['letra']}  ·  "
                        f"${format_miles_colombian_int(l['capital'])}  ·  "
                        f"{l['no_cuotas']} cuotas"
                    )
                    letra_combo.addItem(texto, userData=l)

            # --- INPUT ABONO CAPITAL (Nuevo con formato en tiempo real) ---
            abono_input = QLineEdit()
            abono_input.setObjectName("AbonoInput")
            abono_input.setPlaceholderText("$ Abono capital")
            abono_input.setAlignment(Qt.AlignRight)
            abono_input.setFixedHeight(34)
            abono_input.setFixedWidth(140) 

            def on_abono_changed(text):
                # Usamos las funciones de config.py para limpiar y formatear
                raw = parse_miles_colombian(text)
                formatted = format_miles_colombian_int(raw)
                if formatted != text:
                    abono_input.blockSignals(True)
                    abono_input.setText(formatted)
                    # Mantenemos el cursor al final para que no salte al inicio
                    abono_input.setCursorPosition(len(formatted))
                    abono_input.blockSignals(False)

            abono_input.textChanged.connect(on_abono_changed)       

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setAlignment(Qt.AlignRight)
            cuotas_input.setFixedHeight(34)
            cuotas_input.setFixedWidth(90)

            btn_delete_letra = QPushButton("")
            btn_delete_letra.setObjectName("DeleteLetraButton")
            btn_delete_letra.setIcon(load_svg_icon("icons/x.svg"))
            btn_delete_letra.setIconSize(QSize(16,16))  
            btn_delete_letra.setFixedSize(28,28)
            btn_delete_letra.setToolTip("Eliminar esta letra")
            btn_delete_letra.clicked.connect(lambda: letra_row_widget.setParent(None))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(abono_input) # <--- AGREGAMOS EL INPUT AQUÍ
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letra_row_widget = QWidget()
            letra_row_widget.setLayout(letra_row)
            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        # Botón eliminar todo el pago
        btn_delete_pago = QPushButton("")
        btn_delete_pago.setObjectName("DeletePagoButton")
        btn_delete_pago.setIcon(load_svg_icon("icons/x.svg"))
        btn_delete_pago.setIconSize(QSize(20,20))
        btn_delete_pago.setFixedSize(30,30)
        btn_delete_pago.setToolTip("Eliminar este pago")

        # Layout socio + acciones
        socio_row = QHBoxLayout()
        socio_row.setContentsMargins(0,0,0,0)
        socio_row.addWidget(combo)
        socio_row.addWidget(btn_add_letra)
        socio_row.addWidget(btn_delete_pago)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.addLayout(socio_row)
        wrapper_layout.addLayout(letras_container)

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper_layout)
        self.pagos_container.addWidget(wrapper_widget)

        # Conecta eliminación
        btn_delete_pago.clicked.connect(lambda: wrapper_widget.setParent(None))


# --- NUEVA FUNCIÓN HELPER PARA CALCULAR DEUDA ---
    def get_deuda_capital_actual(self, letra_id):
        """
        Calcula el saldo de capital pendiente real mirando la tabla.
        Lógica: Busca la primera cuota NO pagada. 
        Deuda = Su Saldo Capital (final) + Su Amortización Capital (lo que paga esa cuota).
        """
        cursor = self.db.conn.cursor()
        # Buscar primera cuota pendiente (ya sea vencida o futura)
        cursor.execute("""
            SELECT valor_cuota, saldo_capital 
            FROM liquidaciones 
            WHERE credito_letra = ? AND fecha_pago IS NULL 
            ORDER BY nro_cuota ASC LIMIT 1
        """, (letra_id,))
        row = cursor.fetchone()
        
        if row:
            # Ejemplo: Si en la cuota 1 el saldo final es 16.5M y amortiza 500k, 
            # entonces debía 17M antes de pagar.
            return row['saldo_capital'] + row['valor_cuota']
        else:
            # Si no hay pendientes, puede ser que ya pagó todo o no hay tabla (error)
            # Verificamos si hay saldo en la última pagada
            cursor.execute("SELECT saldo_capital FROM liquidaciones WHERE credito_letra = ? ORDER BY nro_cuota DESC LIMIT 1", (letra_id,))
            last = cursor.fetchone()
            return last['saldo_capital'] if last else 0

    def recalcular_tabla_amortizacion(self, letra_id, abono_capital_recien_registrado):
            """
            Regenera la tabla de amortización.
            Identifica los abonos anteriores buscando 'pago_credito' con nro_cuota = 0.
            """
            cursor = self.db.conn.cursor()
            hoy = date.today().strftime("%Y-%m-%d")

            # 1. Obtener Deuda Total
            cursor.execute("SELECT capital, interes, fecha_inicio FROM creditos WHERE letra = ?", (letra_id,))
            credito = cursor.fetchone()
            capital_original = credito['capital']
            tasa_interes = credito['interes']

            # A) Capital pagado en cuotas normales (nro_cuota > 0) - Usamos la tabla liquidaciones
            cursor.execute("SELECT SUM(valor_cuota) FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NOT NULL", (letra_id,))
            pagado_cuotas = cursor.fetchone()[0] or 0

            # B) Capital abonado extra (SUMA TOTAL HISTÓRICA, INCLUYENDO EL ACTUAL)
            # CORRECCIÓN: Buscamos 'pago_credito' donde nro_cuota sea 0
            cursor.execute("""
                SELECT SUM(monto) FROM detalle_recibo 
                WHERE credito_letra = ? AND tipo_operacion = 'pago_credito' AND nro_cuota = 0
            """, (letra_id,))
            pagado_abonos = cursor.fetchone()[0] or 0

            saldo_real_nuevo = capital_original - pagado_cuotas - pagado_abonos

            # Si ya no debe nada, borrar todo lo pendiente y salir
            if saldo_real_nuevo <= 0:
                cursor.execute("DELETE FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL", (letra_id,))
                self.db.conn.commit()
                return

            # 2. IDENTIFICAR CUOTAS VENCIDAS (EL PASADO - NO SE TOCAN)
            cursor.execute("""
                SELECT id, valor_cuota, nro_cuota, fecha_vencimiento 
                FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento < ?
                ORDER BY nro_cuota ASC
            """, (letra_id, hoy))
            vencidas = cursor.fetchall()
            
            capital_en_vencidas = sum(v['valor_cuota'] for v in vencidas)
            capital_para_futuro = saldo_real_nuevo - capital_en_vencidas

            # Validación de seguridad
            if capital_para_futuro < 0: capital_para_futuro = 0 

            # 3. BORRAR EL FUTURO (Cuotas pendientes desde HOY en adelante)
            cursor.execute("""
                DELETE FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento >= ?
            """, (letra_id, hoy))

            if capital_para_futuro == 0:
                self.db.conn.commit()
                return

            # 4. REGENERAR PROYECCIÓN FUTURA
            cursor.execute("SELECT valor_cuota FROM liquidaciones WHERE credito_letra = ? AND nro_cuota = 1", (letra_id,))
            row_base = cursor.fetchone()
            amortizacion_fija = row_base['valor_cuota'] if row_base else (capital_original // 10)

            # Definir arranque
            cursor.execute("""
                SELECT nro_cuota, fecha_vencimiento FROM liquidaciones 
                WHERE credito_letra = ? 
                ORDER BY nro_cuota DESC LIMIT 1
            """, (letra_id,))
            ultimo_reg = cursor.fetchone()
            
            nro_start = ultimo_reg['nro_cuota'] + 1 if ultimo_reg else 1
            fecha_start = datetime.strptime(ultimo_reg['fecha_vencimiento'], "%Y-%m-%d") if ultimo_reg else datetime.strptime(credito['fecha_inicio'][:10], "%Y-%m-%d")

            nuevas_cuotas = []
            saldo_iter = capital_para_futuro
            
            while saldo_iter > 0:
                fecha_start = fecha_start + relativedelta(months=+1)
                cap_pago = min(saldo_iter, amortizacion_fija)
                
                # Interés sobre saldo total vivo (Futuro + Vencido)
                int_mes = int((saldo_iter + capital_en_vencidas) * tasa_interes)
                cuota_total = cap_pago + int_mes
                
                # Saldo visual en tabla = Saldo Futuro Restante + Capital Vencido
                saldo_final_row = (saldo_iter - cap_pago) + capital_en_vencidas
                
                nuevas_cuotas.append((
                    letra_id, nro_start, fecha_start.strftime("%Y-%m-%d"),
                    int(cap_pago), int(int_mes), int(cuota_total), int(saldo_final_row)
                ))
                
                saldo_iter -= cap_pago
                nro_start += 1

            cursor.executemany("""
                INSERT INTO liquidaciones 
                (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital, interes_mora, mora_aplicada, notif_prev_enviada, notif_venc_enviada, fecha_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, NULL)
            """, nuevas_cuotas)

            self.db.conn.commit()


    def on_register(self):
        """Valida y registra pagos de cuotas y abonos a capital."""
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # Listas para procesar
        operaciones_db = [] # (tipo, socio_id, letra_id, valor, cuotas_count)
        pagos_consolidados_para_recibo = {}
        
        # Recolectar widgets
        current_pagos_widgets = []
        for i in range(self.pagos_container.count()):
            wrapper = self.pagos_container.itemAt(i).widget()
            if wrapper:
                combo = wrapper.findChild(NoScrollComboBox, "ComboSocioPago")
                # Buscar el layout de letras (asumiendo estructura)
                wrapper_layout = wrapper.layout()
                if wrapper_layout.count() > 1:
                    letras_container = wrapper_layout.itemAt(1)
                    current_pagos_widgets.append((combo, letras_container, wrapper))

        if not current_pagos_widgets:
            show_warning(self, "", "Agrega al menos un pago.")
            return

        try:
            cursor = self.db.conn.cursor()
            
            # Crear recibo header
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid
            fecha_actual = date.today().strftime("%Y-%m-%d")
            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")

            entradas_recibo_count = 0

            for combo, letras_container, _ in current_pagos_widgets:
                socio_selected = combo.currentData()
                if not socio_selected: continue
                
                # Datos socio completo
                socio_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)

                for i in range(letras_container.count()):
                    w = letras_container.itemAt(i).widget()
                    letra_selected = w.findChild(NoScrollComboBox, "LetraCombo").currentData()
                    if not letra_selected: continue

                    # Obtener inputs
                    abono_text = w.findChild(QLineEdit, "AbonoInput").text()
                    cuotas_text = w.findChild(QLineEdit, "CuotasInput").text()
                    
                    valor_abono = parse_miles_colombian(abono_text) if abono_text else 0
                    try:
                        n_cuotas = int(cuotas_text) if cuotas_text else 0
                    except:
                        show_error(self, "", "Número de cuotas inválido.")
                        return

                    if valor_abono == 0 and n_cuotas == 0:
                        continue

                    letra_id = letra_selected['letra']

                    # --- 1. PROCESAR CUOTAS NORMALES ---
                    if n_cuotas > 0:
                        cursor.execute(
                            "SELECT nro_cuota, valor_cuota, interes_mes, saldo_capital, interes_mora "
                            "FROM liquidaciones "
                            "WHERE credito_letra = ? AND fecha_pago IS NULL "
                            "ORDER BY nro_cuota LIMIT ?", (letra_id, n_cuotas)
                        )
                        filas = cursor.fetchall()
                        
                        if len(filas) < n_cuotas:
                            show_error(self, "Error", f"No hay suficientes cuotas pendientes para pagar {n_cuotas}.")
                            return

                        # Consolidar para recibo
                        key_recibo = f"{letra_id}_cuotas"
                        if key_recibo not in pagos_consolidados_para_recibo:
                            # Buscar saldo antes del pago (para recibo)
                            first_nro = filas[0]['nro_cuota']
                            saldo_ini = 0
                            if first_nro == 1:
                                saldo_ini = letra_selected['capital']
                            else:
                                prev = cursor.execute("SELECT saldo_capital FROM liquidaciones WHERE credito_letra=? AND nro_cuota=?", (letra_id, first_nro-1)).fetchone()
                                saldo_ini = prev['saldo_capital'] if prev else 0

                            pagos_consolidados_para_recibo[key_recibo] = {
                                'socio_data': socio_full,
                                'letra_id': letra_id,
                                'nro_cuotas_pagadas_start': first_nro,
                                'nro_cuotas_pagadas_end': first_nro,
                                'valor_capital_consolidado': 0,
                                'interes_consolidado': 0,
                                'saldo_capital_antes_pago': saldo_ini,
                                'saldo_capital_despues_pago': 0
                            }
                            entradas_recibo_count += 1

                        dict_recibo = pagos_consolidados_para_recibo[key_recibo]

                        for fila in filas:
                            nro = fila['nro_cuota']
                            # Sumamos Mora si existe (columna nueva)
                            mora = fila['interes_mora'] if 'interes_mora' in fila.keys() else 0
                            
                            monto_total = fila['valor_cuota'] + fila['interes_mes'] + mora
                            
                            # Actualizar BD
                            cursor.execute(
                                "INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora) "
                                "VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)",
                                (recibo_id, socio_selected['id'], letra_id, nro, monto_total, mora)
                            )
                            cursor.execute("UPDATE liquidaciones SET fecha_pago = DATE('now') WHERE credito_letra=? AND nro_cuota=?", (letra_id, nro))
                            
                            saldo_caja += monto_total

                            # Actualizar datos recibo
                            dict_recibo['valor_capital_consolidado'] += fila['valor_cuota']
                            # OJO: En el recibo sumamos la mora al interés para simplificar, o solo interés normal
                            dict_recibo['interes_consolidado'] += (fila['interes_mes'] + mora) 
                            dict_recibo['nro_cuotas_pagadas_end'] = nro
                            dict_recibo['saldo_capital_despues_pago'] = fila['saldo_capital']

                            # Log Auxiliar
                            nombre_log = f"{socio_full['nombres']} {socio_full['apellidos']}"
                            self.db.add_to_auxiliar(
                                fecha=fecha_actual, tipo="Pago Credito", socio=nombre_log, 
                                numero=recibo_id, monto=monto_total, saldo=saldo_caja, 
                                cuota=nro, id_credito=letra_id
                            )
                            if self.assistant_page:
                                self.assistant_page.add_operation({
                                    "fecha": fecha_actual, "tipo": "Pago Credito", "socio": nombre_log,
                                    "numero": recibo_id, "cuota": nro, "monto": monto_total, 
                                    "saldo": saldo_caja, "id_credito": letra_id
                                })

                    # --- 2. PROCESAR ABONO CAPITAL ---
                    if valor_abono > 0:
                        letra_id = letra_selected['letra']

                        # 1. VALIDACIÓN
                        deuda_capital_real = self.get_deuda_capital_actual(letra_id)
                        if valor_abono > deuda_capital_real:
                            show_warning(self, "Monto Inválido", 
                                         f"El abono supera el saldo de capital actual (${format_miles_colombian_int(deuda_capital_real)}).")
                            return

                        # 2. REGISTRO EN BD (CORREGIDO: Usamos 'pago_credito' para cumplir el CHECK)
                        cursor.execute(
                            "INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto) "
                            "VALUES (?, 'abono_capital', ?, ?, 0, ?)", # <--- 'abono_capital' y nro_cuota 0
                            (recibo_id, socio_selected['id'], letra_id, valor_abono)
                        )
                        saldo_caja += valor_abono

                        # 3. RECALCULAR (La función ahora busca 'abono_capital' con cuota 0)
                        self.recalcular_tabla_amortizacion(letra_id, valor_abono)

                        # 4. AUXILIAR
                        self.db.add_to_auxiliar(
                            fecha=fecha_actual, 
                            tipo="Abono Capital", 
                            socio=f"{socio_full['nombres']} {socio_full['apellidos']}", 
                            numero=recibo_id, 
                            monto=valor_abono, 
                            saldo=saldo_caja, 
                            id_credito=letra_id
                        )

                        # 5. PREPARAR RECIBO (Esto sigue igual, es solo visual para el Excel)
                        key_abono = f"{letra_id}_abono"
                        saldo_final_recibo = deuda_capital_real - valor_abono
                        pagos_consolidados_para_recibo[key_abono] = {
                            'socio_data': socio_full,
                            'letra_id': letra_id,
                            'nro_cuotas_pagadas_start': "ABONO",
                            'nro_cuotas_pagadas_end': "CAPITAL",
                            'valor_capital_consolidado': valor_abono,
                            'interes_consolidado': 0,
                            'saldo_capital_antes_pago': int(deuda_capital_real),
                            'saldo_capital_despues_pago': int(max(0, saldo_final_recibo))
                        }
                        entradas_recibo_count += 1
                        # -----------------------------------------------

            # Finalizar Transacción
            self.db.set_config_value("saldo_en_caja", str(saldo_caja))
            self.db.conn.commit()

            # Generar Recibo
            lista_recibo = list(pagos_consolidados_para_recibo.values())
            recibo_path = generar_recibo_solo_pagos(
                db_manager=self.db,
                recibo_id=recibo_id,
                recibi_de_data=recibi,
                pagos_credito_info=lista_recibo
            )

            if recibo_path:
                show_success(self, "Pago Registrado", f"Transacción exitosa. Recibo #{recibo_id}", file_path=recibo_path)
                self.operation_registered.emit()
            
            self.clear_form()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "Error", f"Ocurrió un error al registrar: {e}")
            import traceback
            traceback.print_exc()

    def refresh(self):
        """Recarga la lista de socios y actualiza los combos existentes."""
        self.load_socios()
        # Actualizar combos de socios existentes
        for combo, letras_container, _ in self.pagos_widgets:
            socio_actual = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                combo.addItem(nombre, userData=socio)
            # Reestablecer selección si era válida
            if socio_actual:
                for i in range(combo.count()):
                    if combo.itemData(i)['id'] == socio_actual['id']:
                        combo.setCurrentIndex(i)
                        break
            combo.blockSignals(False)

    def clear_form(self):
        """Limpia el formulario y recarga los socios."""
        # Elimina todos los widgets de pago dinámicos
        for i in reversed(range(self.pagos_container.count())):
            widget = self.pagos_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Vacía la lista de widgets de pago
        self.pagos_widgets.clear()
        
        # Recarga los socios
        self.load_socios()