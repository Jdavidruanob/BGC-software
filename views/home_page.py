import os
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QStackedWidget, QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt, QSize
from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian
from views.widgets.forms.form_aporte import FormAporte
from views.widgets.forms.form_pago_credito import FormPagoCredito
from views.widgets.forms.form_combinado import FormCombinado
from views.widgets.forms.form_nuevo_credito import FormNuevoCredito
from views.widgets.forms.form_retiro import FormRetiro
from views.widgets.message_boxes import show_error, show_success


class HomePage(QWidget):
    def __init__(self, db_manager, assistant_page):
        super().__init__()
        self.setObjectName("HomePage")
        self.db_manager = db_manager
        self.assistant_page = assistant_page

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(80, 40, 80, 20)
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
        self.btn_aporte.setIcon(load_svg_icon("assets/icons/pig-money.svg"))
        self.btn_aporte.setCheckable(True)
        self.btn_aporte.setProperty("btnType", "operacion")
        self.btn_aporte.clicked.connect(self.toggle_aporte)

        self.btn_pago_credito = QPushButton(" Pago Crédito")
        self.btn_pago_credito.setIconSize(QSize(24, 24))
        self.btn_pago_credito.setIcon(load_svg_icon("assets/icons/cash.svg"))
        self.btn_pago_credito.setCheckable(True)
        self.btn_pago_credito.setProperty("btnType", "operacion")
        self.btn_pago_credito.clicked.connect(self.toggle_pago_credito)

        self.btn_nuevo_credito = QPushButton(" Nuevo Crédito")
        self.btn_nuevo_credito.setIconSize(QSize(24, 24))
        self.btn_nuevo_credito.setIcon(load_svg_icon("assets/icons/circle-plus.svg"))
        self.btn_nuevo_credito.setCheckable(True)
        self.btn_nuevo_credito.setProperty("btnType", "operacion")
        self.btn_nuevo_credito.clicked.connect(self.toggle_nuevo_credito)

        self.btn_retiro = QPushButton(" Retiro")
        self.btn_retiro.setIconSize(QSize(26, 26))
        self.btn_retiro.setIcon(load_svg_icon("assets/icons/cash-move.svg"))
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
        self.form_nuevo_credito = FormNuevoCredito()
        self.form_retiro = FormRetiro()
        self.form_aporte_pago = FormCombinado(self.db_manager)

        #for widget in [self.form_aporte, self.page_pago, self.form_nuevo_credito, self.form_retiro, self.form_aporte_pago]:
            #widget.setStyleSheet("font-size: 16px; padding: 20px;")

        self.stack.addWidget(self.form_aporte)         # 0
        self.stack.addWidget(self.page_pago)           # 1
        self.stack.addWidget(self.form_nuevo_credito)  # 2
        self.stack.addWidget(self.form_retiro)         # 3
        self.stack.addWidget(self.form_aporte_pago)    # 4

        #self.stack.setStyleSheet(""" background-color: trasparent; border-radius: 8px""")

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

        self.right_panel.setLayout(right_layout)
        main_layout.addWidget(self.left_panel, 2.5)
        main_layout.addWidget(self.right_panel, 1.5)
        self.setLayout(main_layout)

        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "home_page.qss")
        load_styles(self, qss_path)

    def create_resumen_widget(self):
        """Construye el widget 'Resumen de Caja'."""
        # --- Recuperar datos ---
        # Saldo en caja
        row = self.db_manager.conn.execute(
            "SELECT value FROM config WHERE key = ?", ("saldo_en_caja",)
        ).fetchone()
        saldo_caja = int(row["value"]) if row else 0

        # Créditos activos (total)
        # Asumimos que get_active_credits_by_member solo trae por socio;
        # si quieres global, tendrías que un método new:
        total_creditos = self.db_manager.conn.execute(
            "SELECT COUNT(*) FROM socio_credito"
        ).fetchone()[0]

        # Total socios
        total_socios = len(self.db_manager.get_all_members_full())

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
        bl.setContentsMargins(12, 12, 12, 12)
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
        add_row("Créditos Activos:", str(total_creditos), bold=True)
        add_row("Total Socios:", str(total_socios), bold=True)

        v.addWidget(header)
        v.addWidget(body)

        
        return frame

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
        if hasattr(self.form_aporte, "refresh"):
            self.form_aporte.refresh()

        # Pago Crédito
        if hasattr(self.page_pago, "refresh"):
            self.page_pago.refresh()

        """  # Nuevo Crédito (más adelante)
        if hasattr(self.page_credito, "refresh"):
            self.page_credito.refresh()

        # Retiro (más adelante)
        if hasattr(self.page_retiro, "refresh"):
            self.page_retiro.refresh() """

        """ # Aporte + Pago Crédito
        if hasattr(self.form_aporte_pago, "refresh"):
            self.form_aporte_pago.refresh() """

        print("✅ Formularios actualizados.")

    def refresh_view(self):
        print("🔁 Refrescando vista home")
        self.refresh_forms()
        
        # 🔄 ACTUALIZAR EL WIDGET DEL PANEL DERECHO
        # Elimina contenido anterior del right_panel
        for i in reversed(range(self.right_panel.layout().count())):
            widget = self.right_panel.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Carga de nuevo el resumen
        resumen_widget = self.create_resumen_widget()
        self.right_panel.layout().addWidget(resumen_widget)

