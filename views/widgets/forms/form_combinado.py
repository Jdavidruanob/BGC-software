from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian
from views.widgets.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import date
# IMPORTAR AHORA DESDE EL NUEVO ARCHIVO ESPECÍFICO DE RECIBO COMBINADO
from utils.recibo_generator_combinado import generar_recibo_combinado, DEFAULT_GASTOS_ADMIN, MAX_APORTE_ROWS_IN_TEMPLATE, MAX_CREDITO_ROWS_IN_TEMPLATE
import traceback # Para ver errores completos en la consola

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormCombinado(QWidget):
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
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(40)
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
        self.btn_agregar_aporte.setIcon(load_svg_icon("assets/icons/plus.svg"))
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
        self.btn_agregar_pago.setIcon(load_svg_icon("assets/icons/plus.svg"))
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
            os.path.dirname(__file__),
            "..", "..", "..", "styles", "forms", "form_combinado.qss"
        )
        load_styles(self, qss_path)


    def load_socios(self):
        """Carga lista de socios para combo_recibi_de."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_recibi_de.clear()
            if not self.socios_data:
                show_warning(self, "", "No hay socios registrados.")
                return
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_aporte(self):
        """Agrega una fila con ComboSocio + MontoInput + DeleteButton."""
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocio")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']}"
            combo.addItem(nombre, userData=socio)

        monto_input = QLineEdit()
        monto_input.setObjectName("MontoInput")
        monto_input.setPlaceholderText("Monto del aporte")
        monto_input.setAlignment(Qt.AlignRight)
        monto_input.setFixedHeight(34)
        monto_input.setFixedWidth(160)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                monto_input.blockSignals(True)
                monto_input.setText(formatted)
                monto_input.setCursorPosition(len(formatted))
                monto_input.blockSignals(False)
        monto_input.textChanged.connect(on_text_changed)

        btn_eliminar = QPushButton("")
        btn_eliminar.setObjectName("DeleteButton")
        btn_eliminar.setIcon(load_svg_icon("assets/icons/x.svg"))
        btn_eliminar.setIconSize(QSize(20, 20))
        btn_eliminar.setToolTip("Eliminar aporte")
        btn_eliminar.setFixedSize(30, 30)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(combo)
        row_layout.addWidget(monto_input)
        row_layout.addWidget(btn_eliminar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(row_widget)
        container.addWidget(line)

        wrapper = QWidget()
        wrapper.setLayout(container)
        self.aportes_container.addWidget(wrapper)
        self.aportes_widgets.append((combo, monto_input, wrapper))

        def eliminar():
            wrapper.setParent(None)
            self.aportes_widgets[:] = [t for t in self.aportes_widgets if t[2] is not wrapper]
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
        btn_add_letra.setIcon(load_svg_icon("assets/icons/plus.svg"))
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

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setAlignment(Qt.AlignRight)
            cuotas_input.setFixedHeight(34)
            cuotas_input.setFixedWidth(80)

            btn_delete_letra = QPushButton("")
            btn_delete_letra.setObjectName("DeleteLetraButton")
            btn_delete_letra.setIcon(load_svg_icon("assets/icons/x.svg"))
            btn_delete_letra.setIconSize(QSize(16,16))
            btn_delete_letra.setFixedSize(28,28)
            btn_delete_letra.setToolTip("Eliminar esta letra")
            btn_delete_letra.clicked.connect(lambda: letra_row_widget.setParent(None))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letra_row_widget = QWidget()
            letra_row_widget.setLayout(letra_row)
            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        # Botón eliminar todo el pago
        btn_delete_pago = QPushButton("")
        btn_delete_pago.setObjectName("DeletePagoButton")
        btn_delete_pago.setIcon(load_svg_icon("assets/icons/x.svg"))
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

            # --- Recopilar datos de APORTES para DB y Recibo ---
            aportes_para_db_y_recibo = [] 
            for combo, monto_input, _ in self.aportes_widgets:
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
                
                socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
                if not socio_data_full:
                    show_error(self, "", f"No se encontraron datos completos para el socio ID: {socio_selected['id']}")
                    return
                
                # Obtener el saldo actual del socio directamente de la DB para este cálculo
                # Esto asegura que el saldo_anterior_aporte es el saldo real antes de esta transacción
                # para cada aporte individual si hay múltiples aportes del mismo socio.
                current_socio_db_saldo = self.db.get_member_balance(socio_selected['id']) 

                aportes_para_db_y_recibo.append({
                    'socio_id': socio_selected['id'],
                    'monto': monto,
                    'socio_data': socio_data_full, 
                    'saldo_anterior_aporte': current_socio_db_saldo,
                    'nuevo_saldo_aporte': current_socio_db_saldo + monto
                })
                # No es necesario actualizar socio_data_full['saldo'] aquí, ya que se consulta la DB
                # para el saldo_anterior_aporte en cada iteración y la DB se actualiza al final.


            if len(aportes_para_db_y_recibo) > MAX_APORTE_ROWS_IN_TEMPLATE:
                show_warning(self, "", f"Se excede el límite de {MAX_APORTE_ROWS_IN_TEMPLATE} aportes por recibo combinado. Por favor, ajuste la entrada.")
                return

            # --- Recopilar datos de PAGOS DE CRÉDITO para DB y Recibo (CONSOLIDADOS) ---
            pagos_cuotas_para_db = [] 
            pagos_consolidados_para_recibo = {} 

            # --- NUEVA LÓGICA: Recolectar dinámicamente los widgets de pago activos ---
            current_pagos_widgets = []
            for i in range(self.pagos_container.count()):
                wrapper_widget = self.pagos_container.itemAt(i).widget()
                if wrapper_widget:
                    # Encuentra el QComboBox y el QVBoxLayout dentro del wrapper_widget
                    combo = wrapper_widget.findChild(NoScrollComboBox, "ComboSocioPago")
                    letras_container = wrapper_widget.findChild(QVBoxLayout) # Esto puede ser tricky si hay múltiples QVBoxLayouts. Asegúrate de que sea el correcto.
                                                                            # Una mejor opción sería darle un objectName al letras_container también.
                                                                            # Por ahora, asumiremos que es el primer/único QVBoxLayout anidado.
                    
                    # Una forma más robusta de encontrar 'letras_container':
                    # Si el 'wrapper_layout' es el layout principal del 'wrapper_widget'
                    wrapper_layout = wrapper_widget.layout()
                    if wrapper_layout and wrapper_layout.count() > 1: # Esperamos socio_row y letras_container
                        # El segundo item en el wrapper_layout es el letras_container (siempre y cuando la estructura no cambie)
                        letras_container_layout_item = wrapper_layout.itemAt(1) 
                        if letras_container_layout_item and isinstance(letras_container_layout_item, QVBoxLayout):
                            letras_container = letras_container_layout_item
                        else:
                            letras_container = None # Fallback si no lo encuentra

                    if combo and letras_container:
                        current_pagos_widgets.append((combo, letras_container, wrapper_widget))
            # --- FIN NUEVA LÓGICA ---

            # Ahora itera sobre la lista recién construida
            if not current_pagos_widgets:
                show_warning(self, "", "Agrega al menos un pago.")
                return

            for combo_socio_pago, letras_container, _ in current_pagos_widgets: # Changed from 'letras_data_for_this_pago' to 'letras_container'
                socio_selected = combo_socio_pago.currentData()
                if not socio_selected:
                    show_error(self, "", "Seleccione un socio para cada pago de crédito.")
                    return

                socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
                if not socio_data_full:
                    show_error(self, "", f"No se encontraron datos completos para el socio ID: {socio_selected['id']}")
                    return

                # Iterate through the widgets in letras_container
                letras_en_este_pago = []
                for i in range(letras_container.count()):
                    letra_row_widget = letras_container.itemAt(i).widget()
                    if letra_row_widget:
                        letra_combo = letra_row_widget.findChild(NoScrollComboBox, "LetraCombo")
                        cuotas_input = letra_row_widget.findChild(QLineEdit, "CuotasInput")
                        if letra_combo and cuotas_input:
                            letras_en_este_pago.append((letra_combo, cuotas_input, letra_row_widget))

                if not letras_en_este_pago:
                    show_warning(self, "", f"El socio {socio_selected['nombres']} {socio_selected['apellidos']} no tiene cuotas de crédito seleccionadas.")
                    return

                for letra_combo, cuotas_input, _ in letras_en_este_pago:
                    letra_selected = letra_combo.currentData()
                    if not letra_selected:
                        show_error(self, "", "Seleccione una letra para cada cuota de crédito.")
                        return
                    
                    try:
                        n_cuotas_input = int(cuotas_input.text())
                        if n_cuotas_input <= 0:
                            show_error(self, "", "El número de cuotas debe ser mayor a cero.")
                            return
                    except ValueError:
                        show_error(self, "", "Número de cuotas inválido (debe ser un número entero).")
                        return
                    
                    cursor_temp = self.db.conn.cursor()
                    
                    cursor_temp.execute(
                        "SELECT nro_cuota, valor_cuota, interes_mes, saldo_capital FROM liquidaciones "
                        "WHERE credito_letra = ? AND fecha_pago IS NULL "
                        "ORDER BY nro_cuota LIMIT ?", 
                        (letra_selected['letra'], n_cuotas_input)
                    )
                    cuotas_a_pagar_detalles = cursor_temp.fetchall() 

                    if len(cuotas_a_pagar_detalles) < n_cuotas_input:
                        show_error(self, "Error de cuotas",
                                f"Sólo quedan {len(cuotas_a_pagar_detalles)} cuotas pendientes para la letra {letra_selected['letra']}, y se intentó pagar {n_cuotas_input}.")
                        return
                    
                    if not cuotas_a_pagar_detalles:
                        continue 

                    letra_id = letra_selected['letra']

                    # Get initial saldo_capital_antes_pago for this specific credit
                    saldo_antes_pago_credito = 0
                    if cuotas_a_pagar_detalles[0]['nro_cuota'] == 1:
                        # FIX: Corrected function name here
                        credito_data = self.db.get_credit_by_letra(letra_id) 
                        if credito_data: # Ensure credito_data is not None
                            saldo_antes_pago_credito = credito_data['capital']
                        else:
                            show_error(self, "", f"No se encontró información para el crédito de la letra: {letra_id}")
                            return
                    else:
                        cursor_temp.execute(
                            "SELECT saldo_capital FROM liquidaciones "
                            "WHERE credito_letra = ? AND nro_cuota = ?", 
                            (letra_id, cuotas_a_pagar_detalles[0]['nro_cuota'] - 1)
                        )
                        result = cursor_temp.fetchone()
                        saldo_antes_pago_credito = result['saldo_capital'] if result else 0 

                    if letra_id not in pagos_consolidados_para_recibo:
                        pagos_consolidados_para_recibo[letra_id] = {
                            'socio_data': socio_data_full,
                            'letra_id': letra_id,
                            'nro_cuotas_pagadas_start': cuotas_a_pagar_detalles[0]['nro_cuota'],
                            'nro_cuotas_pagadas_end': cuotas_a_pagar_detalles[0]['nro_cuota'], # Will be updated
                            'valor_capital_consolidado': 0,
                            'interes_consolidado': 0,
                            'saldo_capital_antes_pago': saldo_antes_pago_credito,
                            'saldo_capital_despues_pago': 0 # Will be updated
                        }
                    
                    consolidated_entry = pagos_consolidados_para_recibo[letra_id]
                    
                    for detalle_cuota_db in cuotas_a_pagar_detalles:
                        consolidated_entry['valor_capital_consolidado'] += detalle_cuota_db['valor_cuota']
                        consolidated_entry['interes_consolidado'] += detalle_cuota_db['interes_mes']
                        consolidated_entry['nro_cuotas_pagadas_end'] = detalle_cuota_db['nro_cuota']
                        consolidated_entry['saldo_capital_despues_pago'] = detalle_cuota_db['saldo_capital']

                    pagos_cuotas_para_db.append((socio_selected['id'], letra_id, n_cuotas_input))

            pagos_consolidados_lista = list(pagos_consolidados_para_recibo.values())

            if not aportes_para_db_y_recibo and not pagos_consolidados_lista:
                show_warning(self, "", "Debe agregar al menos un aporte o un pago de crédito para generar el recibo.")
                return

            if len(pagos_consolidados_lista) > MAX_CREDITO_ROWS_IN_TEMPLATE:
                show_warning(self, "", f"Se excede el límite de {MAX_CREDITO_ROWS_IN_TEMPLATE} pagos de crédito por recibo combinado. Por favor, ajuste la entrada.")
                return

            try:
                cursor = self.db.conn.cursor()

                cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
                recibo_id = cursor.lastrowid
                fecha_actual = date.today().strftime("%Y-%m-%d")

                saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")

                # --- Procesar y registrar APORTES en DB y Auxiliar ---
                for aporte_detail in aportes_para_db_y_recibo:
                    socio_id = aporte_detail['socio_id']
                    monto = aporte_detail['monto']
                    socio_data = aporte_detail['socio_data'] 

                    cursor.execute("""
                        INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                        VALUES (?, 'aporte', ?, ?)
                    """, (recibo_id, socio_id, monto))
                    
                    # Actualizar el saldo del socio en la base de datos
                    cursor.execute("UPDATE socios SET saldo = saldo + ? WHERE id = ?", (monto, socio_id))
                    
                    saldo_caja += monto
                    
                    nombre = f"{socio_data['nombres']} {socio_data['apellidos']}"
                    self.db.add_to_auxiliar(
                        fecha=fecha_actual,
                        tipo="Aporte",
                        socio=nombre,
                        numero=recibo_id,
                        monto=monto,
                        saldo=saldo_caja
                    )
                    if self.assistant_page:
                        self.assistant_page.add_operation({
                            "fecha": fecha_actual,
                            "tipo": "Aporte",
                            "socio": nombre,
                            "numero": recibo_id,
                            "monto": monto,
                            "saldo": saldo_caja
                        })

                # --- Procesar y registrar PAGOS DE CRÉDITO en DB y Auxiliar ---
                for socio_id, letra_id, n_cuotas_a_pagar in pagos_cuotas_para_db:
                    cursor.execute(
                        "SELECT nro_cuota, valor_cuota, interes_mes FROM liquidaciones "
                        "WHERE credito_letra = ? AND fecha_pago IS NULL "
                        "ORDER BY nro_cuota LIMIT ?", (letra_id, n_cuotas_a_pagar)
                    )
                    filas_cuotas_a_pagar_transaccion = cursor.fetchall()
                    
                    for fila in filas_cuotas_a_pagar_transaccion:
                        nro = fila['nro_cuota']
                        monto_capital_cuota = fila['valor_cuota'] 
                        interes_cuota = fila['interes_mes']
                        monto_total_cuota = monto_capital_cuota + interes_cuota

                        cursor.execute(
                            "INSERT INTO detalle_recibo "
                            "(recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto) "
                            "VALUES (?, 'pago_credito', ?, ?, ?, ?)",
                            (recibo_id, socio_id, letra_id, nro, monto_total_cuota)
                        )

                        cursor.execute(
                            "UPDATE liquidaciones SET fecha_pago = DATE('now') "
                            "WHERE credito_letra = ? AND nro_cuota = ?",
                            (letra_id, nro)
                        )

                        saldo_caja += monto_total_cuota
                        
                        socio_info_for_log = next((s for s in self.socios_data if s["id"] == socio_id), None)
                        nombre_socio_log = f"{socio_info_for_log['nombres']} {socio_info_for_log['apellidos']}" if socio_info_for_log else "Desconocido"
                        
                        self.db.add_to_auxiliar(
                            fecha=fecha_actual,
                            tipo=f"Pago Credito", 
                            socio=nombre_socio_log,
                            numero=recibo_id,
                            monto=monto_total_cuota,
                            saldo=saldo_caja
                        )
                        
                        if self.assistant_page:
                            self.assistant_page.add_operation({
                                "fecha": fecha_actual,
                                "tipo": f"Pago Credito - Letra {letra_id} Cuota {nro}",
                                "socio": nombre_socio_log,
                                "numero": recibo_id,
                                "monto": monto_total_cuota,
                                "saldo": saldo_caja
                            })
                
                self.db.set_config_value("saldo_en_caja", str(saldo_caja))
                self.db.conn.commit()
                
                gastos_admin_value = DEFAULT_GASTOS_ADMIN 

                recibo_path = generar_recibo_combinado(
                    db_manager=self.db, 
                    recibo_id=recibo_id,
                    recibi_de_data=recibi, 
                    aportes_info=aportes_para_db_y_recibo, 
                    pagos_credito_info=pagos_consolidados_lista, 
                    gastos_admin=gastos_admin_value
                )
                
                if recibo_path:
                    show_success(self, "", f"Recibo combinado #{recibo_id} creado exitosamente. Archivo: {recibo_path}")
                else:
                    show_warning(self, "", "Recibo combinado registrado, pero hubo un error al generar el archivo Excel.")
                
                self.limpiar_formulario()

            except Exception as e:
                self.db.conn.rollback()
                show_error(self, "", f"Error al crear recibo combinado:\n{e}")
                import traceback
                traceback.print_exc() # Esto imprimirá el error completo en la consola


    def limpiar_formulario(self):
        """Limpia todos los campos y reinicia el formulario."""
        self.combo_recibi_de.setCurrentIndex(-1)

        for _, _, widget in self.aportes_widgets:
            widget.setParent(None)
        self.aportes_widgets.clear()

        for _, _, widget in self.pagos_widgets:
            widget.setParent(None)
        self.pagos_widgets.clear()

        self.load_socios()
    
    def refresh(self):
        """Recarga lista de socios en todos los combos."""
        self.load_socios()
