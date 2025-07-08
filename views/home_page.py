import os
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QStackedWidget
)
from PySide6.QtCore import Qt, QSize
from config import load_styles, load_svg_icon
from views.widgets.form_aporte import FormAporte
from views.widgets.form_pago_credito import FormPagoCredito
from views.widgets.form_combinado import FormCombinado
from views.widgets.form_nuevo_credito import FormNuevoCredito
from views.widgets.form_retiro import FormRetiro


class HomePage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.setObjectName("HomePage")
        self.db_manager = db_manager

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


        # Botón Refrescar
        self.btn_refrescar = QPushButton("🔄 Refrescar")
        self.btn_refrescar.setFixedWidth(140)
        self.btn_refrescar.setStyleSheet("margin-top: 5px; padding: 6px 10px;")
        self.btn_refrescar.clicked.connect(self.refresh_forms)

        refresh_row = QHBoxLayout()
        refresh_row.addStretch()
        refresh_row.addWidget(self.btn_refrescar)
        refresh_row.setContentsMargins(20, 0, 20, 10)

        container_layout.addLayout(refresh_row)


        # FORMULARIOS: STACK + SCROLL
        self.form_container = QFrame()
        self.form_container.setObjectName("DynamicForm")
        self.form_layout = QVBoxLayout()
        self.form_container.setLayout(self.form_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.stack = QStackedWidget()

        self.form_aporte = FormAporte(self.db_manager)
        self.page_pago = FormPagoCredito()
        self.form_nuevo_credito = FormNuevoCredito()
        self.form_retiro = FormRetiro()
        self.form_aporte_pago = FormCombinado()

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

        # PANEL DERECHO
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        self.right_label = QLabel("📌 Aquí irán más detalles...")
        self.right_label.setStyleSheet("font-size: 16px; color: #333;")
        right_layout.addWidget(self.right_label)
        self.right_panel.setLayout(right_layout)

        # FINAL
        main_layout.addWidget(self.left_panel, 2.5)
        main_layout.addWidget(self.right_panel, 1.5)
        self.setLayout(main_layout)

        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "home_page.qss")
        load_styles(self, qss_path)

    def actualizar_formulario(self):
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
        self.actualizar_formulario()
        #print(f"Aporte seleccionado: {self.btn_aporte.isChecked()}")

    def toggle_pago_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_nuevo_credito.setChecked(False)
        if self.btn_retiro.isChecked():
            self.btn_retiro.setChecked(False)
        self.actualizar_formulario()
        #print(f"Pago Crédito seleccionado: {self.btn_pago_credito.isChecked()}")

    def toggle_nuevo_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_retiro.setChecked(False)
        self.actualizar_formulario()
        #print(f"Nuevo Crédito seleccionado: {self.btn_nuevo_credito.isChecked()}")

    def toggle_retiro(self):
        if self.btn_retiro.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_nuevo_credito.setChecked(False)
        self.actualizar_formulario()
        #print(f"Retiro seleccionado: {self.btn_retiro.isChecked()}")

    def refresh_forms(self):
        """Actualiza todos los formularios de la HomePage si implementan .refresh()"""
        print("🔄 Actualizando formularios...")

        # Aporte
        if hasattr(self.form_aporte, "refresh"):
            self.form_aporte.refresh()

        """ # Pago Crédito
        if hasattr(self.page_pago, "refresh"):
            self.page_pago.refresh() """

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
