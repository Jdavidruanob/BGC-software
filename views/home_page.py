import os
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QStackedWidget, QSizePolicy, QInputDialog,
    QRadioButton, QDateEdit, QButtonGroup  # <--- IMPORTANTE: Faltaban estos
)
from PySide6.QtCore import Qt, QSize, QDate # <--- IMPORTANTE: Faltaba QDate
from config import (
    load_styles, load_svg_icon, format_miles_colombian_int, 
    STYLES_DIR, DYNAMIC_DATA_BASE_DIR,
    get_hoy, get_hoy_str, set_fecha_simulada, reset_fecha_normal # <--- Funciones de tiempo
)
from views.widgets.forms.form_aporte import FormAporte
from views.widgets.forms.form_pago_credito import FormPagoCredito
from views.widgets.forms.form_combinado import FormCombinado
from views.widgets.forms.form_nuevo_credito import FormNuevoCredito
from views.widgets.forms.form_retiro import FormRetiro
from views.widgets.adjust_balance_dialog import EditSaldoDialog
from views.widgets.edit_admin_dialog import EditAdminDialog 
from utils.message_boxes import show_error, show_success, show_warning, show_info


class HomePage(QWidget):
    def __init__(self, db_manager, assistant_page, window):
        super().__init__()
        self.setObjectName("HomePage")
        self.db_manager = db_manager
        self.assistant_page = assistant_page
        self.main_window = window

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(80, 40, 80, 20)
        main_layout.setSpacing(30)

        # =================================================
        # 1. PANEL IZQUIERDO (Formularios)
        # =================================================
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        self.container = QFrame()
        self.container.setObjectName("HomeCard")

        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        header = QFrame()
        header.setObjectName("HomeCardHeader")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Operaciones")
        title.setObjectName("homeTitle")
        subtitle = QLabel("Realice aportes, nuevos créditos o pagos de crédito")
        subtitle.setObjectName("homeSubtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header.setLayout(header_layout)

        # --- Botones de Operación ---
        button_row = QHBoxLayout()
        button_row.setContentsMargins(20, 20, 20, 20)
        button_row.setSpacing(0)

        self.btn_aporte = QPushButton(" Aporte")
        self.btn_aporte.setIconSize(QSize(24, 24))
        self.btn_aporte.setIcon(load_svg_icon("icons/pig-money.svg"))
        self.btn_aporte.setCheckable(True)
        self.btn_aporte.setProperty("btnType", "operacion")
        self.btn_aporte.clicked.connect(self.toggle_aporte)

        self.btn_pago_credito = QPushButton(" Pago Crédito")
        self.btn_pago_credito.setIconSize(QSize(24, 24))
        self.btn_pago_credito.setIcon(load_svg_icon("icons/cash.svg"))
        self.btn_pago_credito.setCheckable(True)
        self.btn_pago_credito.setProperty("btnType", "operacion")
        self.btn_pago_credito.clicked.connect(self.toggle_pago_credito)

        self.btn_nuevo_credito = QPushButton(" Nuevo Crédito")
        self.btn_nuevo_credito.setIconSize(QSize(24, 24))
        self.btn_nuevo_credito.setIcon(load_svg_icon("icons/circle-plus.svg"))
        self.btn_nuevo_credito.setCheckable(True)
        self.btn_nuevo_credito.setProperty("btnType", "operacion")
        self.btn_nuevo_credito.clicked.connect(self.toggle_nuevo_credito)

        self.btn_retiro = QPushButton(" Retiro")
        self.btn_retiro.setIconSize(QSize(26, 26))
        self.btn_retiro.setIcon(load_svg_icon("icons/cash-move.svg")) 
        self.btn_retiro.setCheckable(True)
        self.btn_retiro.setProperty("btnType", "operacion")
        self.btn_retiro.clicked.connect(self.toggle_retiro)

        button_row.addWidget(self.btn_aporte)
        button_row.addWidget(self.btn_pago_credito)
        button_row.addWidget(self.btn_nuevo_credito)
        button_row.addWidget(self.btn_retiro)

        # --- Stack de Formularios ---
        self.form_container = QFrame()
        self.form_container.setObjectName("DynamicForm")
        self.form_layout = QVBoxLayout()
        self.form_container.setLayout(self.form_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.stack = QStackedWidget()

        self.form_aporte = FormAporte(self.db_manager, self.assistant_page)
        self.page_pago = FormPagoCredito(self.db_manager, self.assistant_page)
        self.form_nuevo_credito = FormNuevoCredito(self.db_manager, self.main_window, self.assistant_page)
        self.form_retiro = FormRetiro(self.db_manager)
        self.form_aporte_pago = FormCombinado(self.db_manager, self.assistant_page)

        # Conectar señales de actualización
        self.form_aporte.operation_registered.connect(self.refresh_view)
        self.page_pago.operation_registered.connect(self.refresh_view)
        self.form_nuevo_credito.operation_registered.connect(self.refresh_view)
        self.form_retiro.operation_registered.connect(self.refresh_view)
        self.form_aporte_pago.operation_registered.connect(self.refresh_view)
        
        self.stack.addWidget(self.form_aporte)         # 0
        self.stack.addWidget(self.page_pago)           # 1
        self.stack.addWidget(self.form_nuevo_credito)  # 2
        self.stack.addWidget(self.form_retiro)         # 3
        self.stack.addWidget(self.form_aporte_pago)    # 4

        scroll_area.setWidget(self.stack)
        self.form_layout.addWidget(scroll_area)
        self.form_container.setVisible(False)

        # --- Armado del Panel Izquierdo ---
        container_layout.addWidget(header)
        container_layout.addLayout(button_row)
        container_layout.addWidget(self.form_container)
        self.container.setLayout(container_layout)

        left_layout.addWidget(self.container)
        self.left_panel.setLayout(left_layout)

        # =================================================
        # 2. PANEL DERECHO (Resumen + Admin + Fecha)
        # =================================================
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setSpacing(20)

        # 1) Resumen Widget
        resumen = self.create_resumen_widget()
        right_layout.addWidget(resumen)

        # --- Panel de Administración ---
        self.admin_panel = QWidget()
        admin_layout = QVBoxLayout()
        admin_layout.setContentsMargins(0, 16, 0, 0)
        admin_layout.setSpacing(12)

        # Fila 1: Editar Saldo y Admin
        row_admin_actions = QHBoxLayout()
        row_admin_actions.setSpacing(10)
        
        btn_editar_saldo = QPushButton(" Ajuste Caja")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        btn_editar_saldo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_editar_admin = QPushButton(" Editar Admin")
        btn_editar_admin.setObjectName("btnEditarAdmin")
        btn_editar_admin.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_admin.clicked.connect(self.editar_gastos_admin)
        btn_editar_admin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_admin_actions.addWidget(btn_editar_saldo)
        row_admin_actions.addWidget(btn_editar_admin)
        admin_layout.addLayout(row_admin_actions)

        # Fila 2: Cambiar Base de Datos
        btn_cambiar_bd = QPushButton("  Cambiar Base de Datos")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)
        admin_layout.addWidget(btn_cambiar_bd)

        # --- SECCIÓN DE FECHA (NUEVO) ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #CCC; margin-top: 10px; margin-bottom: 5px;")
        admin_layout.addWidget(sep)

        lbl_fecha = QLabel("Configuración de Fecha")
        lbl_fecha.setStyleSheet("font-weight: bold; color: #555;")
        admin_layout.addWidget(lbl_fecha)

        # Radio Buttons
        self.rb_normal = QRadioButton("Fecha Normal (Hoy)")
        self.rb_simulada = QRadioButton("Modo Simulación")
        self.rb_normal.setChecked(True) # Por defecto

        self.bg_fecha = QButtonGroup(self)
        self.bg_fecha.addButton(self.rb_normal)
        self.bg_fecha.addButton(self.rb_simulada)

        # Conectar cambios
        self.bg_fecha.buttonClicked.connect(self.on_date_mode_changed)

        row_radios = QHBoxLayout()
        row_radios.addWidget(self.rb_normal)
        row_radios.addWidget(self.rb_simulada)
        admin_layout.addLayout(row_radios)

        # Widget oculto para elegir fecha
        self.widget_simulacion = QWidget()
        layout_sim = QVBoxLayout(self.widget_simulacion)
        layout_sim.setContentsMargins(0, 5, 0, 0)
        
        row_picker = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(32)
        
        btn_confirmar_fecha = QPushButton("Confirmar Fecha")
        btn_confirmar_fecha.setCursor(Qt.PointingHandCursor)
        btn_confirmar_fecha.setStyleSheet("""
            QPushButton { background-color: #8C5B2F; color: white; border: none; }
            QPushButton:hover { background-color: #6e4623; }
        """)
        btn_confirmar_fecha.clicked.connect(self.aplicar_fecha_simulada)

        row_picker.addWidget(self.date_edit)
        row_picker.addWidget(btn_confirmar_fecha)
        
        layout_sim.addLayout(row_picker)
        
        # Inicialmente oculto
        self.widget_simulacion.setVisible(False)
        admin_layout.addWidget(self.widget_simulacion)

        # -------------------------------

        self.admin_panel.setLayout(admin_layout)
        right_layout.addWidget(self.admin_panel)

        # =================================================
        # 3. ARMADO PRINCIPAL
        # =================================================
        self.right_panel.setLayout(right_layout)
        main_layout.addWidget(self.left_panel, 2.5)
        main_layout.addWidget(self.right_panel, 1.5)
        
        self.setLayout(main_layout)
        qss_path = os.path.join(STYLES_DIR , "home_page.qss")
        load_styles(self, qss_path)

    # --- LÓGICA DE FECHA NUEVA ---

    def on_date_mode_changed(self, button):
        if button == self.rb_normal:
            self.widget_simulacion.setVisible(False)
            reset_fecha_normal()
            show_success(self, "Modo Normal", f"Fecha reestablecida a hoy: {get_hoy()}")
            self.refresh_forms() # Refrescar formularios para que tomen la nueva fecha
        else:
            self.widget_simulacion.setVisible(True)
            # No aplicamos nada aún, esperamos al botón confirmar

    def aplicar_fecha_simulada(self):
        qdate = self.date_edit.date()
        fecha_py = qdate.toPython() # Convertir a datetime.date
        set_fecha_simulada(fecha_py)
        
        show_success(self, "Viaje en el Tiempo", f"Sistema configurado al: {fecha_py}")
        self.refresh_forms() # IMPORTANTE: Refrescar formularios

    def create_resumen_widget(self):
        """Construye el widget 'Resumen de Caja' con desglose de Administración."""
        cursor = self.db_manager.conn.cursor()

        # 1. Saldo en caja
        row_caja = cursor.execute("SELECT value FROM config WHERE key = 'saldo_en_caja'").fetchone()
        saldo_caja = int(row_caja["value"]) if row_caja else 0

        # 2. Papelería (Acumulado histórico guardado en config como 'total_admin')
        row_papeleria = cursor.execute("SELECT value FROM config WHERE key = 'total_admin'").fetchone()
        papeleria = int(row_papeleria["value"]) if row_papeleria else 0

        # 3. Mora (Calculado sumando todos los abonos por mora en recibos)
        # Usamos COALESCE para que si es Null devuelva 0
        row_mora = cursor.execute("SELECT COALESCE(SUM(abono_mora), 0) FROM detalle_recibo").fetchone()
        total_mora = row_mora[0] if row_mora else 0

        # 4. Total Administración (Suma visual)
        gran_total_admin = papeleria + total_mora

        # 5. Créditos activos
        total_creditos = cursor.execute("SELECT COUNT(*) FROM creditos").fetchone()[0]


        # --- Construcción visual ---
        frame = QFrame()
        frame.setObjectName("summaryCard")
        v = QVBoxLayout(frame)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("summaryHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 6, 10, 6)
        lbl = QLabel("Resumen de Caja")
        lbl.setObjectName("summaryTitle")
        hl.addWidget(lbl)
        header.setLayout(hl)

        # Body
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 16, 16, 16)
        bl.setSpacing(6) # Espaciado un poco más ajustado

        # Función helper mejorada con indentación
        def add_row(label, value, is_bold=False, is_subitem=False):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            
            # Label
            lbl_text = QLabel(label)
            row.addWidget(lbl_text, alignment=Qt.AlignLeft)
            
            # Valor
            val_lbl = QLabel(value)
            val_lbl.setObjectName("summaryValueBold") # Estilo negrita grande
            

            row.addStretch()
            row.addWidget(val_lbl, alignment=Qt.AlignRight)
            bl.addLayout(row)

        # --- Filas ---
        add_row("Saldo en Caja:", f"$ {format_miles_colombian_int(saldo_caja)}", is_bold=True)
        
        # Sección Admin con desglose
        add_row("Administración Total:", f"$ {format_miles_colombian_int(gran_total_admin)}", is_bold=True)
        add_row("- Papelería:", f"$ {format_miles_colombian_int(papeleria)}", is_subitem=True)
        add_row("- Por Mora:", f"$ {format_miles_colombian_int(total_mora)}", is_subitem=True)
        
        # Separador visual opcional o espacio
        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        spacer.setStyleSheet("color: #DDD;")
        bl.addWidget(spacer)

        add_row("Créditos Activos:", str(total_creditos), is_bold=True)

        v.addWidget(header)
        v.addWidget(body)
        
        return frame

    def editar_saldo_en_caja(self):
        from datetime import date # Asegúrate de importar date si no está
        
        saldo_actual = self.db_manager.get_config_value_as_int("saldo_en_caja")
        
        # Usamos el nuevo diálogo (el archivo se llama igual edit_saldo_dialog, pero la clase cambió internamente)
        dlg = EditSaldoDialog(saldo_actual, self)
        
        if dlg.exec():
            # Obtener datos del diálogo: (monto +/- , motivo, saldo final)
            monto_ajuste, motivo, nuevo_saldo = dlg.get_data()
            
            # 1. Actualizar Config (Saldo en Caja)
            self.db_manager.set_config_value("saldo_en_caja", str(nuevo_saldo))
            
            # 2. Registrar en Auxiliar
            # Nota: 'motivo' se guarda en la columna 'tipo' para que salga con color café (custom)
            fecha_actual = get_hoy_str()

            self.db_manager.add_to_auxiliar(
                fecha=fecha_actual,
                tipo=motivo,           # El motivo será el "Tipo" (se verá Café si no es estándar)
                socio="Administracion",# Socio genérico para ajustes internos
                recibo=None,           # No hay recibo físico
                monto=monto_ajuste,    # Puede ser positivo o negativo
                saldo=nuevo_saldo,
                cuota=None,
                id_credito=None
            )
            
            show_success(self, "Ajuste Realizado", 
                         f"Se registró un ajuste de: {format_miles_colombian_int(monto_ajuste)}\n"
                         f"Nuevo saldo: $ {format_miles_colombian_int(nuevo_saldo)}")
            
            self.refresh_view()

    def editar_gastos_admin(self):
        """Abre el diálogo para editar fondo de papelería y % de mora."""
        
        # 1. Obtener valores actuales
        current_papeleria = self.db_manager.get_config_value_as_int("total_admin")
        
        # Para el porcentaje, necesitamos leerlo como float (o string y convertir)
        cursor = self.db_manager.conn.cursor()
        row = cursor.execute("SELECT value FROM config WHERE key='porcentaje_mora'").fetchone()
        current_mora = float(row['value']) if row else 0.02

        dlg = EditAdminDialog(current_papeleria, current_mora, self)
        
        if dlg.exec():
            new_papeleria, new_mora = dlg.get_data()
            
            # 2. Guardar en Config
            self.db_manager.set_config_value("total_admin", str(new_papeleria))
            self.db_manager.set_config_value("porcentaje_mora", str(new_mora))
            
            show_success(self, "Configuración Actualizada", 
                         f"Papelería: $ {format_miles_colombian_int(new_papeleria)}\n"
                         f"Tasa Mora: {new_mora}")
            
            # 3. Refrescar el resumen (para ver el cambio en papelería)
            self.refresh_view()

    def cambiar_base_datos(self):
        """Abre el explorador de archivos para seleccionar una BD de año anterior."""
        from PySide6.QtWidgets import QFileDialog
        
        # Comienza en la carpeta de la aplicación (Archivos_BGC)
        start_dir = os.path.join(DYNAMIC_DATA_BASE_DIR, "Archivos_BGC")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Base de Datos",
            start_dir,
            "Base de Datos SQLite (*.db);;Todos los archivos (*.*)"
        )

        if not file_path:
            return  # Usuario canceló

        if not os.path.exists(file_path):
            show_error(self, "Error", "El archivo seleccionado no existe.")
            return

        try:
            # Desconectar la BD actual
            if self.db_manager.conn:
                self.db_manager.conn.close()
            
            # Cambiar la ruta de la BD en el mismo db_manager
            self.db_manager.db_path = file_path
            
            # Conectar a la nueva BD
            if not self.db_manager.connect():
                show_error(self, "Error", "No se pudo conectar a la base de datos seleccionada.")
                return
            
            # Refrescar toda la vista con los datos de la nueva BD
            show_success(self, "BD Cambiada", f"Ahora estás consultando:\n{os.path.basename(file_path)}")
            self.refresh_view()
            self.refresh_forms()
            
        except Exception as e:
            show_error(self, "Error", f"Error al cambiar la base de datos:\n{str(e)}")

    def update_form(self):
        if self.btn_nuevo_credito.isChecked():
            self.stack.setCurrentIndex(2)
            self.form_container.setVisible(True)
            return
        if self.btn_retiro.isChecked():
            self.stack.setCurrentIndex(3)
            self.form_container.setVisible(True)
            return
        if self.btn_aporte.isChecked() and self.btn_pago_credito.isChecked():
            self.stack.setCurrentIndex(4)
            self.form_container.setVisible(True)
            return
        if self.btn_aporte.isChecked():
            self.stack.setCurrentIndex(0)
            self.form_container.setVisible(True)
            return
        if self.btn_pago_credito.isChecked():
            self.stack.setCurrentIndex(1)
            self.form_container.setVisible(True)
            return

        # Nada seleccionado
        self.form_container.setVisible(False)
        self.stack.setCurrentIndex(-1)

    def toggle_aporte(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_nuevo_credito.setChecked(False)
        if self.btn_retiro.isChecked():
            self.btn_retiro.setChecked(False)
        self.update_form()
        #print(f"Aporte seleccionado: {self.btn_aporte.isChecked()}")

    def toggle_pago_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_nuevo_credito.setChecked(False)
        if self.btn_retiro.isChecked():
            self.btn_retiro.setChecked(False)
        self.update_form()
        #print(f"Pago Crédito seleccionado: {self.btn_pago_credito.isChecked()}")

    def toggle_nuevo_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_retiro.setChecked(False)
        self.update_form()
        #print(f"Nuevo Crédito seleccionado: {self.btn_nuevo_credito.isChecked()}")

    def toggle_retiro(self):
        if self.btn_retiro.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_nuevo_credito.setChecked(False)
        self.update_form()
        #print(f"Retiro seleccionado: {self.btn_retiro.isChecked()}")

    def refresh_forms(self):
        """Actualiza todos los formularios de la HomePage si implementan .refresh()"""
        print("🔄 Actualizando formularios...")
        # Aporte
        self.form_aporte.refresh()
        # Pago Crédito
        self.page_pago.refresh()
        # Aporte + Pago Crédito
        self.form_aporte_pago.refresh()
        # Nuevo Crédito 
        self.form_nuevo_credito.refresh()
        # Retiro (más adelante)
        self.form_retiro.refresh()

        

        print("✅ Formularios actualizados.")

    def refresh_view(self):
        print("🔁 Refrescando vista home")
        self.refresh_forms()
        
        # 🔄 1. LIMPIAR EL PANEL DERECHO
        layout = self.right_panel.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout is not None:
                    while child_layout.count():
                        child_item = child_layout.takeAt(0)
                        child_w = child_item.widget()
                        if child_w: child_w.deleteLater()
        
        # 🔄 2. RE-CREAR EL RESUMEN
        resumen_widget = self.create_resumen_widget()
        layout.addWidget(resumen_widget)

        # 🔄 3. RE-CREAR EL PANEL DE ADMINISTRACIÓN COMPLETO
        # (Incluye Botones y Configuración de Fecha)
        self.admin_panel = QWidget()
        admin_layout = QVBoxLayout()
        admin_layout.setContentsMargins(0, 16, 0, 0)
        admin_layout.setSpacing(12)

        # --- A. BOTONES DE ACCIÓN ---
        row_admin_actions = QHBoxLayout()
        row_admin_actions.setSpacing(10)
        
        btn_editar_saldo = QPushButton(" Ajuste Caja")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        btn_editar_saldo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_editar_admin = QPushButton(" Editar Admin")
        btn_editar_admin.setObjectName("btnEditarAdmin")
        btn_editar_admin.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_admin.clicked.connect(self.editar_gastos_admin)
        btn_editar_admin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_admin_actions.addWidget(btn_editar_saldo)
        row_admin_actions.addWidget(btn_editar_admin)
        admin_layout.addLayout(row_admin_actions)

        # Botón BD
        btn_cambiar_bd = QPushButton("  Cambiar Base de Datos")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)
        admin_layout.addWidget(btn_cambiar_bd)

        # --- B. SECCIÓN DE FECHA ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #CCC; margin-top: 10px; margin-bottom: 5px;")
        admin_layout.addWidget(sep)

        lbl_fecha = QLabel("Configuración de Fecha")
        lbl_fecha.setStyleSheet("font-weight: bold; color: #555;")
        admin_layout.addWidget(lbl_fecha)

        # Radio Buttons
        self.rb_normal = QRadioButton("Fecha Normal (Hoy)")
        self.rb_simulada = QRadioButton("Modo Simulación")
        
        # Verificar estado actual para marcar el correcto
        from datetime import date
        if get_hoy() != date.today():
            self.rb_simulada.setChecked(True)
            mostrar_selector = True
        else:
            self.rb_normal.setChecked(True)
            mostrar_selector = False

        self.bg_fecha = QButtonGroup(self)
        self.bg_fecha.addButton(self.rb_normal)
        self.bg_fecha.addButton(self.rb_simulada)
        self.bg_fecha.buttonClicked.connect(self.on_date_mode_changed)

        row_radios = QHBoxLayout()
        row_radios.addWidget(self.rb_normal)
        row_radios.addWidget(self.rb_simulada)
        admin_layout.addLayout(row_radios)

        # Widget selector de fecha
        self.widget_simulacion = QWidget()
        layout_sim = QVBoxLayout(self.widget_simulacion)
        layout_sim.setContentsMargins(0, 5, 0, 0)
        
        row_picker = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        # Poner la fecha que esté configurada actualmente (real o simulada)
        fecha_actual_config = get_hoy()
        self.date_edit.setDate(QDate(fecha_actual_config.year, fecha_actual_config.month, fecha_actual_config.day))
        self.date_edit.setMinimumHeight(32)
        
        btn_confirmar_fecha = QPushButton("Confirmar Fecha")
        btn_confirmar_fecha.setCursor(Qt.PointingHandCursor)
        btn_confirmar_fecha.setStyleSheet("""
            QPushButton { background-color: #8C5B2F; color: white; border: none; }
            QPushButton:hover { background-color: #6e4623; }
        """)
        btn_confirmar_fecha.clicked.connect(self.aplicar_fecha_simulada)

        row_picker.addWidget(self.date_edit)
        row_picker.addWidget(btn_confirmar_fecha)
        layout_sim.addLayout(row_picker)
        
        # Visibilidad según estado
        self.widget_simulacion.setVisible(mostrar_selector)
        admin_layout.addWidget(self.widget_simulacion)

        # -------------------------------
        self.admin_panel.setLayout(admin_layout)
        layout.addWidget(self.admin_panel)
