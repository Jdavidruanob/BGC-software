import os
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QSize
from config import load_styles, load_svg_icon


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("HomePage")

        # --- Layout principal: horizontal para izquierda y derecha
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(80, 40, 80, 20)
        main_layout.setSpacing(30)

        # ---------- PANEL IZQUIERDO (más ancho) ----------
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        # Contenedor tipo tarjeta
        self.container = QFrame()
        self.container.setObjectName("HomeCard")

        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Header azul
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

        # Botones de operaciones
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
        self.btn_retiro.setIcon(load_svg_icon("assets/icons/cash-move.svg"))  # Usa un ícono adecuado
        self.btn_retiro.setCheckable(True)
        self.btn_retiro.setProperty("btnType", "operacion")
        self.btn_retiro.clicked.connect(self.toggle_retiro)

        # Orden: Aporte - Pago Crédito - Nuevo Crédito
        button_row.addWidget(self.btn_aporte)
        button_row.addWidget(self.btn_pago_credito)
        button_row.addWidget(self.btn_nuevo_credito)
        button_row.addWidget(self.btn_retiro)


        # Construir el contenedor
        container_layout.addWidget(header)
        container_layout.addLayout(button_row)
        self.container.setLayout(container_layout)

        # Añadir al layout izquierdo
        left_layout.addWidget(self.container)
        self.left_panel.setLayout(left_layout)

        # ---------- PANEL DERECHO (por ahora solo un label) ----------
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop) 

        self.right_label = QLabel("📌 Aquí irán más detalles...")
        self.right_label.setStyleSheet("font-size: 16px; color: #333;")
        right_layout.addWidget(self.right_label)

        self.right_panel.setLayout(right_layout)

        # Añadir ambos paneles al layout principal
        main_layout.addWidget(self.left_panel, 2.5)   # Izquierdo más ancho
        main_layout.addWidget(self.right_panel, 1.5)  # Derecho más delgado

        self.setLayout(main_layout)

        # Estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "home_page.qss")
        load_styles(self, qss_path)

    def toggle_aporte(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_nuevo_credito.setChecked(False)
        if self.btn_retiro.isChecked():
            self.btn_retiro.setChecked(False)
        print(f"Aporte seleccionado: {self.btn_aporte.isChecked()}")

    def toggle_pago_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_nuevo_credito.setChecked(False)
        if self.btn_retiro.isChecked():
            self.btn_retiro.setChecked(False)
        print(f"Pago Crédito seleccionado: {self.btn_pago_credito.isChecked()}")

    def toggle_nuevo_credito(self):
        if self.btn_nuevo_credito.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_retiro.setChecked(False)
        print(f"Nuevo Crédito seleccionado: {self.btn_nuevo_credito.isChecked()}")

    def toggle_retiro(self):
        if self.btn_retiro.isChecked():
            self.btn_aporte.setChecked(False)
            self.btn_pago_credito.setChecked(False)
            self.btn_nuevo_credito.setChecked(False)
        print(f"Retiro seleccionado: {self.btn_retiro.isChecked()}")

