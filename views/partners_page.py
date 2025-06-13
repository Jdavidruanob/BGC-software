# financial_cooperative/views/partners_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class PartnersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PartnersPage")
        layout = QVBoxLayout(self)
        label = QLabel("Contenido de la página Socios")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
        self.load_qss()

    def load_qss(self):
        try:
            with open("resources/qss/partners_page.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("partners_page.qss no encontrado. Usando estilos predeterminados.")