from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DataPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Página de datos"))
        self.setLayout(layout)
