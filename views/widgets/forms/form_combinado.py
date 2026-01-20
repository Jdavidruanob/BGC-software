from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QSize, Signal

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
# IMPORTAR AHORA DESDE EL NUEVO ARCHIVO ESPECÍFICO DE RECIBO COMBINADO
from utils.recibo_generator_combinado import generar_recibo_combinado
import traceback # Para ver errores completos en la consola
from config import HOY, HOY_STR 

MAX_APORTE_ROWS_IN_TEMPLATE = 6
MAX_CREDITO_ROWS_IN_TEMPLATE= 6

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormCombinado(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page):
        
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.aportes_widgets = []
        #------
       # self.socios_data = []
        self.pagos_widgets = []
        
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
        
        # APORTES
        # Sección dinámicos de aportes
        aporte_section_label = QLabel("Aportes a registrar:")
        aporte_section_label.setObjectName("FormLabel")
        main_layout.addWidget(aporte_section_label)

        self.aportes_container = QVBoxLayout()
        self.aportes_container.setSpacing(12)
        main_layout.addLayout(self.aportes_container)

        # Botón agregar nueva fila
        self.btn_agregar_aporte = QPushButton(" Agregar aporte")
        self.btn_agregar_aporte.setObjectName("AddAporteButton")
        self.btn_agregar_aporte.setIcon(load_svg_icon("icons/plus.svg"))
        self.btn_agregar_aporte.setIconSize(QSize(20, 20))
        self.btn_agregar_aporte.clicked.connect(self.agregar_aporte)
        main_layout.addWidget(self.btn_agregar_aporte, alignment=Qt.AlignLeft)

        # PAGOS
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

        # Espacio y botón general para crear el recibo
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Crear Recibo")
        self.btn_registrar.setObjectName("createReceipt")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register_combinado)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial
        self.load_socios()
        # Estilos
        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_combinado.qss"
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

    def agregar_aporte(self):
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocio")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']}"
            combo.addItem(nombre, userData=socio)

        monto_input = QLineEdit()
        monto_input.setObjectName("MontoInput")
        monto_input.setPlaceholderText("Monto aporte")
        monto_input.setAlignment(Qt.AlignRight)
        monto_input.setFixedHeight(34)
        monto_input.setFixedWidth(140) # Ajustado un poco para que quepa todo

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                monto_input.blockSignals(True)
                monto_input.setText(formatted)
                monto_input.setCursorPosition(len(formatted))
                monto_input.blockSignals(False)
        monto_input.textChanged.connect(on_text_changed)

        # --- NUEVO CHECKBOX (Igual que en form_aporte) ---
        chk_papeleria = QCheckBox() 
        chk_papeleria.setObjectName("ChkPapeleria")
        chk_papeleria.setChecked(True)
        chk_papeleria.setToolTip("Cobrar gastos de administración")
        chk_papeleria.setCursor(Qt.PointingHandCursor)
        
        # ------------------------------------------------

        btn_eliminar = QPushButton("")
        btn_eliminar.setObjectName("DeleteButton")
        btn_eliminar.setIcon(load_svg_icon("icons/x.svg"))
        btn_eliminar.setIconSize(QSize(20, 20))
        btn_eliminar.setFixedSize(28, 28)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        
        row_layout.addWidget(combo)
        row_layout.addWidget(monto_input)
        row_layout.addWidget(chk_papeleria) # <--- Agregamos al layout
        row_layout.addWidget(btn_eliminar)

        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(row_widget)

        wrapper = QWidget()
        wrapper.setLayout(container)
        self.aportes_container.addWidget(wrapper)
        
        # --- AQUÍ ESTABA EL ERROR ---
        # Antes guardabas 3, ahora guardamos 4:
        self.aportes_widgets.append((combo, monto_input, chk_papeleria, wrapper))

        def eliminar():
            wrapper.setParent(None)
            # Ahora sí funcionará porque la tupla tiene 4 elementos
            self.aportes_widgets[:] = [t for t in self.aportes_widgets if t[3] is not wrapper]
            
        btn_eliminar.clicked.connect(eliminar)

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
            btn_delete_letra.setFixedSize(25,25)
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
        btn_delete_pago.setFixedSize(28,28)
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

        #self.pagos_widgets.append((combo, letras_container, wrapper_widget))


    def on_register_combinado(self):
        """
        Registra transacción mixta aplicando lógica financiera estricta:
        - Caja/Auxiliar: Solo Capital + Interés.
        - Admin: Aportes papelería + Mora recaudada.
        """
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # Estructuras
        aportes_validos = []
        ops_creditos_validos = []
        pagos_consolidados = {}
        reporte_global = {}
        
        count_cobrables_admin = 0 # Contador para papelería

        # ==============================================================================
        # FASE 1: RECOLECCIÓN Y VALIDACIÓN
        # ==============================================================================
        
        try:
            # 1.1 PROCESAR APORTES
            for combo, monto_input, chk_papeleria, _ in self.aportes_widgets:
                socio = combo.currentData()
                if not socio:
                    show_error(self, "", "Seleccione un socio para cada aporte.")
                    return
                
                monto = parse_miles_colombian(monto_input.text())
                if monto <= 0:
                    show_error(self, "", "El monto del aporte debe ser mayor a cero.")
                    return
                
                socio_full = next((s for s in self.socios_data if s["id"] == socio['id']), None)
                saldo_actual = self.db.get_member_balance(socio['id'])
                
                if chk_papeleria.isChecked():
                    count_cobrables_admin += 1
                
                aportes_validos.append({
                    'socio_data': socio_full,
                    'monto': monto,
                    'saldo_anterior': saldo_actual,
                    'saldo_nuevo': saldo_actual + monto
                })
                
                nombre = f"{socio_full['nombres']} {socio_full['apellidos']}"
                if nombre not in reporte_global: reporte_global[nombre] = []
                reporte_global[nombre].append(f"Aporte: <b>${format_miles_colombian_int(monto)}</b>")

            if len(aportes_validos) > MAX_APORTE_ROWS_IN_TEMPLATE:
                show_warning(self, "Límite Excedido", f"Máximo {MAX_APORTE_ROWS_IN_TEMPLATE} aportes por recibo.")
                return

            # 1.2 PROCESAR CRÉDITOS
            current_pagos_widgets = []
            for i in range(self.pagos_container.count()):
                wrapper = self.pagos_container.itemAt(i).widget()
                if wrapper:
                    combo = wrapper.findChild(NoScrollComboBox, "ComboSocioPago")
                    wrapper_layout = wrapper.layout()
                    if wrapper_layout.count() > 1:
                        letras_container = wrapper_layout.itemAt(1)
                        current_pagos_widgets.append((combo, letras_container, wrapper))

            tasa_mora_str = self.db.get_config_value("porcentaje_mora")
            tasa_mora = float(tasa_mora_str) if tasa_mora_str else 0.02
            hoy_dt = HOY

            for combo, letras_container, _ in current_pagos_widgets:
                socio_selected = combo.currentData()
                if not socio_selected: 
                    show_error(self, "", "Seleccione un socio para cada pago de crédito.")
                    return
                
                socio_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
                nombre_socio = f"{socio_full['nombres']} {socio_full['apellidos']}"

                for i in range(letras_container.count()):
                    w = letras_container.itemAt(i).widget()
                    letra_selected = w.findChild(NoScrollComboBox, "LetraCombo").currentData()
                    if not letra_selected: 
                        show_error(self, "", "Seleccione una letra de crédito válida.")
                        return

                    abono_txt = w.findChild(QLineEdit, "AbonoInput").text()
                    cuotas_txt = w.findChild(QLineEdit, "CuotasInput").text()
                    
                    dinero_abono = parse_miles_colombian(abono_txt) if abono_txt else 0
                    try: n_cuotas = int(cuotas_txt) if cuotas_txt else 0
                    except: n_cuotas = 0

                    if dinero_abono == 0 and n_cuotas == 0: continue

                    letra_id = letra_selected['letra']

                    if dinero_abono > 0 and n_cuotas > 0:
                        show_error(self, "Campos Excluyentes", f"En el pago de {nombre_socio} (Letra {letra_id}) use solo una opción.")
                        return

                    if letra_id not in pagos_consolidados:
                        saldo_ini = self.db.get_deuda_capital_actual(letra_id)
                        pagos_consolidados[letra_id] = {
                            'socio_data': socio_full, 'letra_id': letra_id,
                            'nro_cuotas_pagadas_start': 0, 'nro_cuotas_pagadas_end': 0,
                            'valor_capital_consolidado': 0, 'interes_consolidado': 0, 'mora_consolidada': 0,
                            'saldo_capital_antes_pago': saldo_ini, 'saldo_capital_despues_pago': 0
                        }

                    # --- LÓGICA A: CUOTAS MANUALES ---
                    if n_cuotas > 0:
                        cursor = self.db.conn.cursor()
                        cursor.execute(
                            "SELECT nro_cuota, valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_vencimiento "
                            "FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL "
                            "ORDER BY nro_cuota LIMIT ?", (letra_id, n_cuotas)
                        )
                        filas = cursor.fetchall()
                        if len(filas) < n_cuotas:
                            show_error(self, "Error", f"No hay suficientes cuotas pendientes en letra {letra_id}.")
                            return

                        cuotas_a_pagar = []
                        msgs = []
                        for fila in filas:
                            mora_calc = 0
                            f_venc = datetime.strptime(fila['fecha_vencimiento'], "%Y-%m-%d").date()
                            f_limite = f_venc + relativedelta(months=+1)
                            
                            costo_base = fila['valor_cuota'] + fila['interes_mes']
                            info_mora = ""
                            
                            if hoy_dt > f_limite:
                                mora_calc = int(fila['valor_cuota'] * tasa_mora)
                                info_mora = f" <span style='color:#d9534f'>(+Mora ${format_miles_colombian_int(mora_calc)})</span>"
                            
                            total_recibo = costo_base + mora_calc
                            
                            cuotas_a_pagar.append({
                                'nro': fila['nro_cuota'], 
                                'monto_total': total_recibo, # Base + Mora (Para Recibo)
                                'monto_base': costo_base,    # Base (Para Caja/Auxiliar)
                                'mora': mora_calc,           # Mora (Para Admin)
                                'cap': fila['valor_cuota'], 'int': fila['interes_mes']
                            })
                            msgs.append(f"Cuota #{fila['nro_cuota']} - ${format_miles_colombian_int(costo_base)}{info_mora}")

                        ops_creditos_validos.append({
                            'tipo': 'CUOTAS_MANUAL', 'letra_id': letra_id, 'items': cuotas_a_pagar,
                            'socio_data': socio_full, 'mensajes': msgs
                        })

                    # --- LÓGICA B: ABONO CASCADA ---
                    elif dinero_abono > 0:
                        pendientes = self.db.get_pending_installments(letra_id)
                        vencidas_a_pagar = []
                        
                        for cuota in pendientes:
                            f_venc = datetime.strptime(cuota['fecha_vencimiento'], "%Y-%m-%d").date()
                            if f_venc < hoy_dt:
                                cap = cuota['valor_cuota']
                                ints = cuota['interes_mes']
                                m_calc = 0
                                f_limite = f_venc + relativedelta(months=+1)
                                if hoy_dt > f_limite:
                                    m_calc = int(cap * tasa_mora)
                                
                                base = cap + ints
                                total_row = base + m_calc
                                vencidas_a_pagar.append({
                                    'data': cuota, 'costo_total': total_row, 
                                    'monto_base': base, 'mora': m_calc
                                })
                            else:
                                break
                        
                        temp_dinero = dinero_abono
                        pagables_count = 0
                        costo_acum = 0
                        
                        for v in vencidas_a_pagar:
                            if temp_dinero >= v['costo_total']:
                                temp_dinero -= v['costo_total']
                                costo_acum += v['costo_total']
                                pagables_count += 1
                            else:
                                if pagables_count == 0:
                                    show_error(self, "Abono Insuficiente", f"No cubre la primera cuota vencida de la letra {letra_id}.")
                                    return
                                else:
                                    show_warning(self, "Monto Incompleto", f"Abono incompleto en letra {letra_id}. Ajuste a ${format_miles_colombian_int(costo_acum)}.")
                                    return

                        rem_capital = 0
                        if temp_dinero > 0:
                            deuda_actual = self.db.get_deuda_capital_actual(letra_id)
                            cap_vencidas = sum([v['data']['valor_cuota'] for v in vencidas_a_pagar[:pagables_count]])
                            deuda_futura = deuda_actual - cap_vencidas
                            
                            if temp_dinero > deuda_futura:
                                show_warning(self, "Exceso de Pago", 
                                             f"En letra {letra_id} sobra dinero. Se cobrará solo el saldo real: ${format_miles_colombian_int(deuda_futura)}.")
                                temp_dinero = deuda_futura
                            rem_capital = temp_dinero

                        msgs = []
                        for i in range(pagables_count):
                            v = vencidas_a_pagar[i]
                            info = f"Vencida #{v['data']['nro_cuota']} - ${format_miles_colombian_int(v['monto_base'])}"
                            if v['mora'] > 0: info += f" <span style='color:#d9534f'>(+Mora ${format_miles_colombian_int(v['mora'])})</span>"
                            msgs.append(info)
                        
                        if rem_capital > 0:
                            msgs.append(f"Abono Capital: <b>${format_miles_colombian_int(rem_capital)}</b>")

                        ops_creditos_validos.append({
                            'tipo': 'ABONO_CASCADA', 'letra_id': letra_id, 'socio_data': socio_full,
                            'vencidas': vencidas_a_pagar[:pagables_count], 'capital_puro': rem_capital,
                            'mensajes': msgs
                        })

            if not aportes_validos and not ops_creditos_validos:
                show_warning(self, "", "No hay operaciones válidas para registrar.")
                return

            # ==============================================================================
            # FASE 2: EJECUCIÓN (ESCRITURA EN DB)
            # ==============================================================================
            
            cursor = self.db.conn.cursor()
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid
            
            fecha_str = HOY_STR
            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")
            total_admin = self.db.get_config_value_as_int("total_admin")
            
            mora_total_transaccion = 0

            # 2.1 Ejecutar Aportes
            for ap in aportes_validos:
                cursor.execute("""
                    INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto) 
                    VALUES (?, 'aporte', ?, ?)
                """, (recibo_id, ap['socio_data']['id'], ap['monto']))
                
                cursor.execute("UPDATE socios SET saldo = saldo + ? WHERE id = ?", (ap['monto'], ap['socio_data']['id']))
                
                # Aporte entra a caja y auxiliar
                saldo_caja += ap['monto']
                self.db.add_to_auxiliar(
                    fecha=fecha_str, tipo="Aporte", socio=f"{ap['socio_data']['nombres']} {ap['socio_data']['apellidos']}",
                    monto=ap['monto'], saldo=saldo_caja, recibo=recibo_id
                )

            # 2.2 Ejecutar Créditos
            for op in ops_creditos_validos:
                letra_id = op['letra_id']
                socio_data = op['socio_data']
                nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
                dict_recibo = pagos_consolidados[letra_id]
                
                if nombre not in reporte_global: reporte_global[nombre] = []
                reporte_global[nombre].extend(op['mensajes'])

                if op['tipo'] == 'CUOTAS_MANUAL':
                    items = op['items']
                    dict_recibo['nro_cuotas_pagadas_start'] = items[0]['nro']
                    dict_recibo['nro_cuotas_pagadas_end'] = items[-1]['nro']
                    
                    for it in items:
                        # Recibo: Monto Total (Base + Mora)
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                            VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                        """, (recibo_id, socio_data['id'], letra_id, it['nro'], it['monto_total'], it['mora']))
                        
                        m_flag = 1 if it['mora'] > 0 else 0
                        cursor.execute("""
                            UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ? 
                            WHERE credito_letra=? AND nro_cuota=?
                        """, (it['mora'], m_flag, letra_id, it['nro']))
                        
                        # --- DISTRIBUCIÓN ---
                        saldo_caja += it['monto_base'] # Solo base a Caja
                        mora_total_transaccion += it['mora'] # Mora a Admin
                        
                        dict_recibo['valor_capital_consolidado'] += it['cap']
                        dict_recibo['interes_consolidado'] += it['int']
                        dict_recibo['mora_consolidada'] += it['mora']
                        
                        # Auxiliar: Solo base
                        self.db.add_to_auxiliar(
                            fecha=fecha_str, tipo="Pago Credito", socio=nombre,
                            monto=it['monto_base'], saldo=saldo_caja, recibo=recibo_id, cuota=it['nro'], id_credito=str(letra_id)
                        )

                elif op['tipo'] == 'ABONO_CASCADA':
                    vencidas = op['vencidas']
                    capital_puro = op['capital_puro']
                    
                    for v in vencidas:
                        nro = v['data']['nro_cuota']
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                            VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                        """, (recibo_id, socio_data['id'], letra_id, nro, v['costo_total'], v['mora']))
                        
                        m_flag = 1 if v['mora'] > 0 else 0
                        cursor.execute("""
                            UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ? 
                            WHERE credito_letra=? AND nro_cuota=?
                        """, (v['mora'], m_flag, letra_id, nro))
                        
                        saldo_caja += v['monto_base']
                        mora_total_transaccion += v['mora']
                        
                        dict_recibo['valor_capital_consolidado'] += v['data']['valor_cuota']
                        dict_recibo['interes_consolidado'] += v['data']['interes_mes']
                        dict_recibo['mora_consolidada'] += v['mora']
                        
                        self.db.add_to_auxiliar(
                            fecha=fecha_str, tipo="Pago Credito", socio=nombre,
                            monto=v['monto_base'], saldo=saldo_caja, recibo=recibo_id, cuota=nro, id_credito=str(letra_id)
                        )

                    if capital_puro > 0:
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto)
                            VALUES (?, 'pago_credito', ?, ?, 0, ?)
                        """, (recibo_id, socio_data['id'], letra_id, capital_puro))
                        
                        saldo_caja += capital_puro
                        self.db.recalcular_tabla_amortizacion(letra_id, capital_puro)
                        
                        dict_recibo['valor_capital_consolidado'] += capital_puro
                        self.db.add_to_auxiliar(
                            fecha=fecha_str, tipo="Abono Capital", socio=nombre,
                            monto=capital_puro, saldo=saldo_caja, recibo=recibo_id, cuota=0, id_credito=str(letra_id)
                        )

                    if vencidas:
                        dict_recibo['nro_cuotas_pagadas_start'] = vencidas[0]['data']['nro_cuota']
                        dict_recibo['nro_cuotas_pagadas_end'] = "ABONO" if capital_puro > 0 else vencidas[-1]['data']['nro_cuota']
                    else:
                        dict_recibo['nro_cuotas_pagadas_start'] = "ABONO"
                        dict_recibo['nro_cuotas_pagadas_end'] = "CAPITAL"

                deuda_aprox = dict_recibo['saldo_capital_antes_pago'] - dict_recibo['valor_capital_consolidado']
                dict_recibo['saldo_capital_despues_pago'] = max(0, int(deuda_aprox))

            # 2.3 Actualizar Caja y Admin
            self.db.set_config_value("saldo_en_caja", str(saldo_caja))
            
            # ADMIN = Papelería + Mora recaudada
            monto_papeleria = 3000 * count_cobrables_admin
            nuevo_admin = total_admin + monto_papeleria + mora_total_transaccion
            self.db.set_config_value("total_admin", str(nuevo_admin))

            self.db.conn.commit()

            # 2.4 Generar Reporte y Excel
            if reporte_global:
                msg_final = ""
                for nombre, acciones in reporte_global.items():
                    msg_final += f"<b>{nombre}</b><br>"
                    for accion in acciones:
                        msg_final += f"&nbsp;&nbsp;• {accion}<br>"
                    msg_final += "<br>"
                show_info(self, "Resumen Transacción", msg_final)

            recibo_path = generar_recibo_combinado(
                db_manager=self.db,
                recibo_id=recibo_id,
                recibi_de_data=recibi,
                aportes_info=aportes_validos,
                pagos_credito_info=list(pagos_consolidados.values()),
                num_aportes_cobrables=count_cobrables_admin
            )

            if recibo_path:
                show_success(self, "", f"Recibo combinado #{recibo_id} creado.", file_path=recibo_path)
                self.operation_registered.emit()
            
            self.limpiar_formulario()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "Error", f"Error crítico al registrar: {e}")
            import traceback
            traceback.print_exc()


    def limpiar_formulario(self):
        """Limpia todos los campos y reinicia el formulario."""
        self.combo_recibi_de.setCurrentIndex(-1)

        # Limpiar aportes
        for _, _, _, wrapper in self.aportes_widgets:
            wrapper.setParent(None)
        self.aportes_widgets.clear()

        # Limpiar pagos de crédito dinámicamente del contenedor
        while self.pagos_container.count() > 0:
            item = self.pagos_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.load_socios()
    
    def refresh(self):
        """Recarga lista de socios en todos los combos."""
        self.load_socios()
