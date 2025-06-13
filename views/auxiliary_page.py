# financial_cooperative/views/auxiliary_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class AuxiliaryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AuxiliaryPage")
        layout = QVBoxLayout(self)
        label = QLabel("Contenido de la página Auxiliar")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
        self.load_qss()

    def load_qss(self):
        try:
            with open("resources/qss/auxiliary_page.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("auxiliary_page.qss no encontrado. Usando estilos predeterminados.")