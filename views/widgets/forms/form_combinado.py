from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QSize, Signal

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import date
# IMPORTAR AHORA DESDE EL NUEVO ARCHIVO ESPECÍFICO DE RECIBO COMBINADO
from utils.recibo_generator_combinado import generar_recibo_combinado, MAX_APORTE_ROWS_IN_TEMPLATE, MAX_CREDITO_ROWS_IN_TEMPLATE
import traceback # Para ver errores completos en la consola

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
        btn_eliminar.setFixedSize(30, 30)

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

        #self.pagos_widgets.append((combo, letras_container, wrapper_widget))


    def on_register_combinado(self):
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # ---------------------------------------------------------------------
        # 1. RECOPILAR APORTES (Con lógica de Checkbox Papelería)
        # ---------------------------------------------------------------------
        aportes_para_db_y_recibo = [] 
        count_cobrables = 0 # <--- Contador para administración (Checkboxes marcados)
        
        # OJO: Aquí asumimos que ya actualizaste agregar_aporte para guardar 4 cosas
        # (combo, input, check, wrapper)
        for combo, monto_input, chk_papeleria, _ in self.aportes_widgets:
            socio_selected = combo.currentData()
            if not socio_selected:
                show_error(self, "", "Seleccione un socio para cada aporte.")
                return
            
            try:
                monto = parse_miles_colombian(monto_input.text())
                if monto <= 0:
                    show_error(self, "", "El monto del aporte debe ser mayor a cero.")
                    return
            except ValueError:
                show_error(self, "", "Monto de aporte inválido.")
                return
            
            # Verificar si paga administración
            if chk_papeleria.isChecked():
                count_cobrables += 1
            
            socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
            if not socio_data_full:
                show_error(self, "", f"No se encontraron datos completos para el socio ID: {socio_selected['id']}")
                return
            
            # Obtener saldo actual DB
            current_socio_db_saldo = self.db.get_member_balance(socio_selected['id']) 

            aportes_para_db_y_recibo.append({
                'socio_id': socio_selected['id'],
                'monto': monto,
                'socio_data': socio_data_full, 
                'saldo_anterior_aporte': current_socio_db_saldo,
                'nuevo_saldo_aporte': current_socio_db_saldo + monto
            })

        if len(aportes_para_db_y_recibo) > MAX_APORTE_ROWS_IN_TEMPLATE:
            show_warning(self, "", f"Se excede el límite de {MAX_APORTE_ROWS_IN_TEMPLATE} aportes por recibo combinado.")
            return

        # ---------------------------------------------------------------------
        # 2. RECOPILAR PAGOS CRÉDITO Y ABONOS (Lógica centralizada)
        # ---------------------------------------------------------------------
        pagos_cuotas_para_db = [] 
        abonos_para_db = [] 
        pagos_consolidados_para_recibo = {} 

        # Recolectar widgets dinámicamente
        current_pagos_widgets = []
        for i in range(self.pagos_container.count()):
            wrapper_widget = self.pagos_container.itemAt(i).widget()
            if wrapper_widget:
                combo = wrapper_widget.findChild(NoScrollComboBox, "ComboSocioPago")
                
                # Buscar el layout de letras (asumiendo estructura: layout -> [row_socio, layout_letras])
                wrapper_layout = wrapper_widget.layout()
                letras_container = None
                if wrapper_layout and wrapper_layout.count() > 1:
                    item = wrapper_layout.itemAt(1)
                    if item.layout(): # Verificar si es un layout
                        letras_container = item.layout() # Puede ser el layout directamente
                    elif item.widget(): # O un widget que contiene el layout
                         letras_container = item.widget().layout()
                    # Fallback simple: si es QVBoxLayout directo
                    if isinstance(item, QVBoxLayout): letras_container = item

                if combo and letras_container:
                    current_pagos_widgets.append((combo, letras_container, wrapper_widget))

        # Iterar sobre socios pagadores
        for combo_socio_pago, letras_container, _ in current_pagos_widgets:
            socio_selected = combo_socio_pago.currentData()
            if not socio_selected:
                show_error(self, "", "Seleccione un socio para cada pago de crédito.")
                return

            socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
            
            # Recolectar widgets de letras/abonos de este socio
            letras_en_este_pago = []
            for i in range(letras_container.count()):
                letra_row_widget = letras_container.itemAt(i).widget()
                if letra_row_widget:
                    letra_combo = letra_row_widget.findChild(NoScrollComboBox, "LetraCombo")
                    cuotas_input = letra_row_widget.findChild(QLineEdit, "CuotasInput")
                    abono_input = letra_row_widget.findChild(QLineEdit, "AbonoInput")
                    
                    if letra_combo and cuotas_input:
                        letras_en_este_pago.append((letra_combo, cuotas_input, abono_input, letra_row_widget))

            if not letras_en_este_pago:
                show_warning(self, "", f"El socio {socio_selected['nombres']} no tiene cuotas seleccionadas.")
                return

            for letra_combo, cuotas_input, abono_input, _ in letras_en_este_pago:
                letra_selected = letra_combo.currentData()
                if not letra_selected:
                    show_error(self, "", "Seleccione una letra para cada cuota.")
                    return
                
                letra_id = letra_selected['letra']
                
                # Valores Inputs
                try:
                    c_txt = cuotas_input.text()
                    n_cuotas_input = int(c_txt) if c_txt else 0
                except: n_cuotas_input = 0
                
                a_txt = abono_input.text() if abono_input else ""
                valor_abono = parse_miles_colombian(a_txt) if a_txt else 0

                if n_cuotas_input <= 0 and valor_abono <= 0:
                    continue 

                # --- A) CUOTAS NORMALES ---
                if n_cuotas_input > 0:
                    cursor_temp = self.db.conn.cursor()
                    cursor_temp.execute(
                        "SELECT nro_cuota, valor_cuota, interes_mes, saldo_capital FROM liquidaciones "
                        "WHERE credito_letra = ? AND fecha_pago IS NULL ORDER BY nro_cuota LIMIT ?", 
                        (letra_id, n_cuotas_input)
                    )
                    cuotas_db = cursor_temp.fetchall() 

                    if len(cuotas_db) < n_cuotas_input:
                        show_error(self, "Error", f"No hay suficientes cuotas pendientes en letra {letra_id}.")
                        return
                    
                    # Saldo inicial para recibo
                    saldo_antes = 0
                    if cuotas_db[0]['nro_cuota'] == 1:
                        cred_data = self.db.get_credit_by_letra(letra_id) 
                        if cred_data: saldo_antes = cred_data['capital']
                    else:
                        cursor_temp.execute("SELECT saldo_capital FROM liquidaciones WHERE credito_letra=? AND nro_cuota=?", (letra_id, cuotas_db[0]['nro_cuota'] - 1))
                        res = cursor_temp.fetchone()
                        saldo_antes = res['saldo_capital'] if res else 0 

                    # Consolidar
                    if letra_id not in pagos_consolidados_para_recibo:
                        pagos_consolidados_para_recibo[letra_id] = {
                            'socio_data': socio_data_full, 'letra_id': letra_id,
                            'nro_cuotas_pagadas_start': cuotas_db[0]['nro_cuota'],
                            'nro_cuotas_pagadas_end': 0, 'valor_capital_consolidado': 0,
                            'interes_consolidado': 0, 'saldo_capital_antes_pago': saldo_antes,
                            'saldo_capital_despues_pago': 0
                        }
                    
                    entry = pagos_consolidados_para_recibo[letra_id]
                    for c in cuotas_db:
                        entry['valor_capital_consolidado'] += c['valor_cuota']
                        entry['interes_consolidado'] += c['interes_mes']
                        entry['nro_cuotas_pagadas_end'] = c['nro_cuota']
                        entry['saldo_capital_despues_pago'] = c['saldo_capital']

                    pagos_cuotas_para_db.append((socio_selected['id'], letra_id, n_cuotas_input))

                # --- B) ABONO CAPITAL ---
                if valor_abono > 0:
                    deuda_real = self.db.get_deuda_capital_actual(letra_id)
                    
                    if valor_abono > deuda_real:
                        show_error(self, "Error", f"El abono de ${format_miles_colombian_int(valor_abono)} supera el saldo (${format_miles_colombian_int(deuda_real)}).")
                        return

                    # Ajuste visual recibo si hubo cuotas antes
                    key_abono = f"{letra_id}_abono"
                    saldo_final = deuda_real - valor_abono
                    if letra_id in pagos_consolidados_para_recibo:
                        # Restamos el capital que se pagará en las cuotas normales de arriba
                        cap_cuotas = pagos_consolidados_para_recibo[letra_id]['valor_capital_consolidado']
                        saldo_final = (deuda_real - cap_cuotas) - valor_abono

                    pagos_consolidados_para_recibo[key_abono] = {
                        'socio_data': socio_data_full, 'letra_id': letra_id,
                        'nro_cuotas_pagadas_start': "ABONO", 'nro_cuotas_pagadas_end': "CAPITAL",
                        'valor_capital_consolidado': valor_abono, 'interes_consolidado': 0,
                        'saldo_capital_antes_pago': int(deuda_real),
                        'saldo_capital_despues_pago': int(max(0, saldo_final))
                    }

                    abonos_para_db.append({
                        'socio_id': socio_selected['id'], 'letra_id': letra_id,
                        'monto': valor_abono, 'socio_name': f"{socio_data_full['nombres']} {socio_data_full['apellidos']}"
                    })

        pagos_consolidados_lista = list(pagos_consolidados_para_recibo.values())

        if not aportes_para_db_y_recibo and not pagos_consolidados_lista:
            show_warning(self, "", "Agregue al menos un movimiento.")
            return

        if len(pagos_consolidados_lista) > MAX_CREDITO_ROWS_IN_TEMPLATE:
            show_warning(self, "", "Excede límite de filas de crédito en recibo.")
            return

        # ---------------------------------------------------------------------
        # 3. EJECUCIÓN EN BASE DE DATOS
        # ---------------------------------------------------------------------
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid
            fecha_actual = date.today().strftime("%Y-%m-%d")

            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")
            saldo_admin = self.db.get_config_value_as_int("total_admin")
            
            # --- A. APORTES ---
            for ap in aportes_para_db_y_recibo:
                cursor.execute("INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto) VALUES (?, 'aporte', ?, ?)", 
                               (recibo_id, ap['socio_id'], ap['monto']))
                cursor.execute("UPDATE socios SET saldo = saldo + ? WHERE id = ?", (ap['monto'], ap['socio_id']))
                saldo_caja += ap['monto']
                
                n_socio = f"{ap['socio_data']['nombres']} {ap['socio_data']['apellidos']}"
                self.db.add_to_auxiliar(fecha_actual, "Aporte", n_socio, ap['monto'], saldo_caja, recibo=recibo_id)
                
                if self.assistant_page:
                    self.assistant_page.add_operation({"fecha": fecha_actual, "tipo": "Aporte", "socio": n_socio, "recibo": recibo_id, "monto": ap['monto'], "saldo": saldo_caja})

            # --- B. CUOTAS ---
            for socio_id, letra_id, n_c in pagos_cuotas_para_db:
                cursor.execute("SELECT nro_cuota, valor_cuota, interes_mes FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL ORDER BY nro_cuota LIMIT ?", (letra_id, n_c))
                filas = cursor.fetchall()
                for f in filas:
                    monto_tot = f['valor_cuota'] + f['interes_mes']
                    cursor.execute("INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto) VALUES (?, 'pago_credito', ?, ?, ?, ?)",
                                   (recibo_id, socio_id, letra_id, f['nro_cuota'], monto_tot))
                    cursor.execute("UPDATE liquidaciones SET fecha_pago = DATE('now') WHERE credito_letra = ? AND nro_cuota = ?", (letra_id, f['nro_cuota']))
                    
                    saldo_caja += monto_tot
                    
                    s_inf = next((s for s in self.socios_data if s["id"] == socio_id), None)
                    n_socio = f"{s_inf['nombres']} {s_inf['apellidos']}" if s_inf else "Socio"
                    
                    self.db.add_to_auxiliar(fecha_actual, "Pago Credito", n_socio, monto_tot, saldo_caja, recibo=recibo_id, cuota=f['nro_cuota'], id_credito=letra_id)
                    
                    if self.assistant_page:
                        self.assistant_page.add_operation({"fecha": fecha_actual, "tipo": "Pago Credito", "socio": n_socio, "recibo": recibo_id, "cuota": f['nro_cuota'], "monto": monto_tot, "saldo": saldo_caja, "id_credito": letra_id})

            # --- C. ABONOS ---
            for ab in abonos_para_db:
                # Insertar con nro_cuota 0 y tipo pago_credito (para cumplir constraints)
                cursor.execute("INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto) VALUES (?, 'pago_credito', ?, ?, 0, ?)",
                               (recibo_id, ab['socio_id'], ab['letra_id'], ab['monto']))
                
                saldo_caja += ab['monto']
                # Recalcular usando lógica centralizada
                self.db.recalcular_tabla_amortizacion(ab['letra_id'], ab['monto'])

                self.db.add_to_auxiliar(fecha_actual, "Abono Capital", ab['socio_name'], ab['monto'], saldo_caja, recibo=recibo_id, cuota=0, id_credito=ab['letra_id'])
                
                if self.assistant_page:
                    self.assistant_page.add_operation({"fecha": fecha_actual, "tipo": "Abono Capital", "socio": ab['socio_name'], "recibo": recibo_id, "monto": ab['monto'], "saldo": saldo_caja, "id_credito": ab['letra_id']})

            # --- FINALIZAR ---
            self.db.set_config_value("saldo_en_caja", str(saldo_caja))
            
            # CALCULO DE GASTOS (Usando el contador del inicio)
            gastos_admin_nuevos = 3000 * count_cobrables
            self.db.set_config_value("total_admin", str(saldo_admin + gastos_admin_nuevos))
            
            self.db.conn.commit()
            
            recibo_path = generar_recibo_combinado(
                db_manager=self.db, 
                recibo_id=recibo_id,
                recibi_de_data=recibi, 
                aportes_info=aportes_para_db_y_recibo, 
                pagos_credito_info=pagos_consolidados_lista,
                # OJO: Si generar_recibo_combinado acepta el parámetro num_aportes_cobrables, pásalo aquí:
                num_aportes_cobrables=count_cobrables
            )
            
            if recibo_path:
                show_success(self, "", f"Recibo combinado #{recibo_id} creado exitosamente.", file_path = recibo_path)
                self.operation_registered.emit()
            else:
                show_warning(self, "", "Recibo combinado registrado, pero hubo un error al generar el archivo Excel.")
            
            self.limpiar_formulario()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "", f"Error al crear recibo combinado:\n{e}")
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
