# widgets/credit_card_widget.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
import os
from config import load_styles  # Asegúrate de tener esta función

class CreditCardWidget(QFrame):
    clicked = Signal(int)  # Emitimos la letra del crédito al hacer clic

    def __init__(self, credito):
        super().__init__()
        self.setObjectName("CreditCardWidget")
        self.setCursor(Qt.PointingHandCursor)

        self.letra = credito["letra"]
        capital = credito["capital"]
        interes = credito["interes"]
        cuotas = credito["no_cuotas"]

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(30)

        self.lbl_letra = QLabel(f"🆔 #{self.letra}")
        self.lbl_letra.setObjectName("creditInfo")

        self.lbl_capital = QLabel(f"💰 ${capital:,.0f}")
        self.lbl_capital.setObjectName("creditInfo")

        self.lbl_interes = QLabel(f"📈 {interes * 100:.2f}%")
        self.lbl_interes.setObjectName("creditInfo")

        self.lbl_cuotas = QLabel(f"📅 {cuotas} cuotas")
        self.lbl_cuotas.setObjectName("creditInfo")

        layout.addWidget(self.lbl_letra)
        layout.addWidget(self.lbl_capital)
        layout.addWidget(self.lbl_interes)
        layout.addWidget(self.lbl_cuotas)
        layout.addStretch()

        self.setLayout(layout)

        # Cargar estilos QSS
        qss_path = os.path.join(os.path.dirname(__file__), "..", "..", "styles", "credit_card_widget.qss")
        load_styles(self, qss_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.letra)
        super().mousePressEvent(event)
