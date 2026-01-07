import os
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QStackedWidget, QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt, QSize
from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
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
        main_layout.setContentsMargins(80, 40, 80, 20) # right up left bottom
        main_layout.setSpacing(30)

        # PANEL IZQUIERDO
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        self.container = QFrame()
        self.container.setObjectName("HomeCard")

        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # HEADER
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

        # BOTONES
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

        # FORMULARIOS: STACK + SCROLL
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

         # 🎯 CONNECT SIGNALS TO REFRESH
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

        # ARMADO
        container_layout.addWidget(header)
        container_layout.addLayout(button_row)
        container_layout.addWidget(self.form_container)
        self.container.setLayout(container_layout)

        left_layout.addWidget(self.container)
        self.left_panel.setLayout(left_layout)

        # --- PANEL DERECHO: ahora con Resumen de Caja ---
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setSpacing(20)

        # 1) Widget de resumen
        resumen = self.create_resumen_widget()
        right_layout.addWidget(resumen)

        # --- Layout agrupador para los botones de administración ---
        admin_buttons_widget = QWidget()
        admin_buttons_layout = QVBoxLayout()
        admin_buttons_layout.setContentsMargins(0, 16, 0, 0)
        admin_buttons_layout.setSpacing(8)

        # 1. FILA SUPERIOR (Saldo + Admin)
        row_admin_actions = QHBoxLayout()
        row_admin_actions.setSpacing(10) # Espacio entre los dos botones
        row_admin_actions.setContentsMargins(0, 0, 0, 0)

        # Botón Editar Saldo
        btn_editar_saldo = QPushButton(" Editar Saldo")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.setIconSize(QSize(18, 18))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        # Expandir para que ocupen mitad y mitad
        btn_editar_saldo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Botón Editar Admin (NUEVO)
        btn_editar_admin = QPushButton(" Editar Admin")
        btn_editar_admin.setObjectName("btnEditarAdmin") # ID para el CSS
        # Usamos un icono de configuración o herramientas (puedes reutilizar edit.svg si no tienes otro)
        btn_editar_admin.setIcon(load_svg_icon("icons/edit.svg")) 
        btn_editar_admin.setIconSize(QSize(18, 18))
        btn_editar_admin.clicked.connect(self.editar_gastos_admin)
        btn_editar_admin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_admin_actions.addWidget(btn_editar_saldo)
        row_admin_actions.addWidget(btn_editar_admin)
        
        admin_buttons_layout.addLayout(row_admin_actions)

        # 2. BOTÓN CAMBIAR BD (Debajo)
        btn_cambiar_bd = QPushButton("  Cambiar Base de Datos")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.setIconSize(QSize(16, 16))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)
        admin_buttons_layout.addWidget(btn_cambiar_bd)

        admin_buttons_widget.setLayout(admin_buttons_layout)
        right_layout.addWidget(admin_buttons_widget)

        self.right_panel.setLayout(right_layout)
        main_layout.addWidget(self.left_panel, 2.5)
        main_layout.addWidget(self.right_panel, 1.5)
        self.setLayout(main_layout)

        qss_path = os.path.join(STYLES_DIR , "home_page.qss")
        load_styles(self, qss_path)

        """ show_error(self, "puerba error", "mensaje de error de prueba")
        show_success(self, "prueba éxito", "mensaje de éxito de prueba")
        show_warning(self, "prueba advertencia", "mensaje de advertencia de prueba")
        show_info(self, "prueba info", "mensaje de info de prueba") """

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
            fecha_actual = date.today().strftime("%Y-%m-%d")
            
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
                # Si hay layouts anidados, limpiar recursivamente (seguridad)
                child_layout = item.layout()
                if child_layout is not None:
                    while child_layout.count():
                        child_item = child_layout.takeAt(0)
                        child_w = child_item.widget()
                        if child_w: child_w.deleteLater()
        
        # 🔄 2. RE-CREAR EL RESUMEN
        resumen_widget = self.create_resumen_widget()
        layout.addWidget(resumen_widget)

        # 🔄 3. RE-CREAR LOS BOTONES DE ADMIN (¡Aquí está el cambio!)
        admin_buttons_widget = QWidget()
        admin_buttons_layout = QVBoxLayout()
        admin_buttons_layout.setContentsMargins(0, 16, 0, 0)
        admin_buttons_layout.setSpacing(8)

        # Fila Horizontal: [Editar Saldo] [Editar Admin]
        row_admin_actions = QHBoxLayout()
        row_admin_actions.setSpacing(10)
        row_admin_actions.setContentsMargins(0, 0, 0, 0)

        # Botón Saldo
        btn_editar_saldo = QPushButton(" Ajuste Caja")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.setIconSize(QSize(18, 18))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        btn_editar_saldo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Botón Admin (NUEVO)
        btn_editar_admin = QPushButton(" Editar Admin")
        btn_editar_admin.setObjectName("btnEditarAdmin")
        btn_editar_admin.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_admin.setIconSize(QSize(18, 18))
        btn_editar_admin.clicked.connect(self.editar_gastos_admin)
        btn_editar_admin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_admin_actions.addWidget(btn_editar_saldo)
        row_admin_actions.addWidget(btn_editar_admin)
        
        admin_buttons_layout.addLayout(row_admin_actions)

        # Botón Cambiar BD (Debajo)
        btn_cambiar_bd = QPushButton("  Cambiar Base de Datos")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.setIconSize(QSize(16, 16))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)
        admin_buttons_layout.addWidget(btn_cambiar_bd)

        admin_buttons_widget.setLayout(admin_buttons_layout)
        layout.addWidget(admin_buttons_widget)
