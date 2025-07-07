from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
import os

from config import load_styles, format_miles_colombian

class CreditLiquidationPage(QWidget):
    def __init__(self, credit, member_id, main_window):
        super().__init__()
        self.setObjectName("creditLiquidationPage")
        self.credit = credit
        self.setMinimumSize(900, 600)
        self.setWindowTitle("Liquidación del Crédito")
        self.main_window = main_window
        self.member_id = member_id

        layout = QVBoxLayout()
        layout.setContentsMargins(80, 30, 80, 30)
        layout.setSpacing(20)

        # Título
        # Botón de regreso
        back_btn = QPushButton("←")
        back_btn.setObjectName("backButton")
        view = f"member_detail_{member_id}"
        back_btn.clicked.connect(lambda: self.main_window.show_view(view))
        layout.addWidget(back_btn)

        title = QLabel("Liquidación del Crédito")
        title.setObjectName("liqTitle")
        layout.addWidget(title)

        # Datos del crédito
        info_layout = QHBoxLayout()
        info_layout.setSpacing(40)

        letra_label = QLabel(f"Letra: {credit['letra']}")
        capital_label = QLabel(f"Capital: ${format_miles_colombian(credit['capital'])}")
        fecha_label = QLabel(f"Fecha: {credit['fecha_inicio'][:10]}")
        cuotas_label = QLabel(f"No. Cuotas: {credit['no_cuotas']}")

        for lbl in [letra_label, capital_label, fecha_label, cuotas_label]:
            lbl.setObjectName("liqInfoLabel")
            info_layout.addWidget(lbl)

        layout.addLayout(info_layout)

         # Socios
        socios_label = QLabel(f"👥 Socios participantes: {credit['socios']}")
        socios_label.setObjectName("liqSocioLabel")
        layout.addWidget(socios_label)
        
        self.setLayout(layout)

        # Cargar estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "liquidation_page.qss")
        load_styles(self, qss_path)
