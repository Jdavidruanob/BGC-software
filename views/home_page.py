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
from views.widgets.edit_saldo_dialog import EditSaldoDialog

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
        admin_buttons_layout.setContentsMargins(0, 16, 0, 0)  # top margin para separarlos del resumen
        admin_buttons_layout.setSpacing(8)  # Espaciado pequeño entre botones

        btn_editar_saldo = QPushButton("  Editar Saldo")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.setIconSize(QSize(18, 18))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        admin_buttons_layout.addWidget(btn_editar_saldo)

        btn_cambiar_bd = QPushButton("  Cambiar BD")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.setIconSize(QSize(16, 16))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)  # ← Cambia esta línea
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
        """Construye el widget 'Resumen de Caja'."""
        # --- Recuperar datos ---
        # Saldo en caja
        row = self.db_manager.conn.execute(
            "SELECT value FROM config WHERE key = ?", ("saldo_en_caja",)
        ).fetchone()
        saldo_caja = int(row["value"]) if row else 0

        row2 = self.db_manager.conn.execute(
            "SELECT value FROM config WHERE key = ?", ("total_admin",)
        ).fetchone()
        admin = int(row2["value"]) if row2 else 0

        # Créditos activos (total)
        # Asumimos que get_active_credits_by_member solo trae por socio;
        # si quieres global, tendrías que un método new:
        total_creditos = self.db_manager.conn.execute(
            "SELECT COUNT(*) FROM creditos"
        ).fetchone()[0]


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
        bl.setSpacing(8)

        # Fila helper
        def add_row(label, value, bold=False):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(label), alignment=Qt.AlignLeft)
            val_lbl = QLabel(value)
            if bold:
                val_lbl.setObjectName("summaryValueBold")
            else:
                val_lbl.setObjectName("summaryValue")
            row.addStretch()
            row.addWidget(val_lbl, alignment=Qt.AlignRight)
            bl.addLayout(row)

        add_row("Saldo en Caja:", f"$ {format_miles_colombian_int(saldo_caja)}", bold=True)
        add_row("Administración:", f"$ {format_miles_colombian_int(admin)}", bold=True)
        add_row("Créditos Activos:", str(total_creditos), bold=True)

        v.addWidget(header)
        v.addWidget(body)

        
        return frame

    def editar_saldo_en_caja(self):
        saldo_actual = self.db_manager.get_config_value_as_int("saldo_en_caja")
        dlg = EditSaldoDialog(saldo_actual, self)
        if dlg.exec():
            nuevo = dlg.get_saldo()
            self.db_manager.set_config_value("saldo_en_caja", str(nuevo))
            show_success(self, "Saldo actualizado", f"El saldo en caja ahora es: $ {format_miles_colombian_int(nuevo)}")
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
        
        # 🔄 ACTUALIZAR EL WIDGET DEL PANEL DERECHO
        # Elimina contenido anterior del right_panel
        layout = self.right_panel.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # Si es un layout anidado, elimínalo recursivamente
                child_layout = item.layout()
                if child_layout is not None:
                    while child_layout.count():
                        child_item = child_layout.takeAt(0)
                        child_widget = child_item.widget()
                        if child_widget is not None:
                            child_widget.deleteLater()
        
        # Carga de nuevo el resumen
        resumen_widget = self.create_resumen_widget()
        layout.addWidget(resumen_widget)

        # --- Layout agrupador para los botones de administración ---
        admin_buttons_widget = QWidget()
        admin_buttons_layout = QVBoxLayout()
        admin_buttons_layout.setContentsMargins(0, 16, 0, 0)
        admin_buttons_layout.setSpacing(8)

        btn_editar_saldo = QPushButton("  Editar Saldo")
        btn_editar_saldo.setObjectName("btnEditarSaldo")
        btn_editar_saldo.setIcon(load_svg_icon("icons/edit.svg"))
        btn_editar_saldo.setIconSize(QSize(18, 18))
        btn_editar_saldo.clicked.connect(self.editar_saldo_en_caja)
        admin_buttons_layout.addWidget(btn_editar_saldo)

        btn_cambiar_bd = QPushButton("  Cambiar BD")
        btn_cambiar_bd.setObjectName("btnCambiarBD")
        btn_cambiar_bd.setIcon(load_svg_icon("icons/database.svg"))
        btn_cambiar_bd.setIconSize(QSize(16, 16))
        btn_cambiar_bd.clicked.connect(self.cambiar_base_datos)  # ← Cambia esta línea
        admin_buttons_layout.addWidget(btn_cambiar_bd)

        admin_buttons_widget.setLayout(admin_buttons_layout)
        layout.addWidget(admin_buttons_widget)
