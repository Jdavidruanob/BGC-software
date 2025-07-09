from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

class FormNuevoCredito(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("💸 Pago de Crédito"))
        layout.addWidget(QLineEdit("Número de crédito"))
        layout.addWidget(QLineEdit("Monto del pago"))
        layout.addWidget(QPushButton("Pagar"))

        self.setLayout(layout)
