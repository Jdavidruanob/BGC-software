from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DataPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Página de datos"))
        self.setLayout(layout)

    def refresh_view(self):
        """Refresca la información visible en esta página."""
        print("🔁 Refrescando vista data")