# financial_cooperative/views/data_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class DataPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DataPage")
        layout = QVBoxLayout(self)
        label = QLabel("Contenido de la página Datos")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
        self.load_qss()

    def load_qss(self):
        try:
            with open("resources/qss/data_page.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("data_page.qss no encontrado. Usando estilos predeterminados.")