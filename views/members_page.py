from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class MembersPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Página de socios"))
        self.setLayout(layout)
