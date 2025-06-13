# financial_cooperative/views/home_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePage") # Para aplicar QSS específico
        layout = QVBoxLayout(self)
        label = QLabel("Bienvenido a la página de Inicio")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

        self.load_qss()

    def load_qss(self):
        try:
            with open("resources/qss/home_page.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("home_page.qss no encontrado. Usando estilos predeterminados.")