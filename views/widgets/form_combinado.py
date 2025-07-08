from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

class FormCombinado(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("🧾 Aporte + Pago Crédito"))

        # Aporte
        layout.addWidget(QLabel("Monto del aporte"))
        layout.addWidget(QLineEdit())

        # Pago
        layout.addWidget(QLabel("Número de crédito"))
        layout.addWidget(QLineEdit())
        layout.addWidget(QPushButton("Registrar ambos"))

        self.setLayout(layout)
