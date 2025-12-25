import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt

from config import load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR

class EditSaldoDialog(QDialog):
    def __init__(self, saldo_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Saldo en Caja")
        self.setModal(True)
        self.setFixedSize(400, 220)
        self.setObjectName("NewMemberDialog")  # Usa el mismo QSS

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        label = QLabel("Nuevo saldo en caja:")
        label.setObjectName("FormLabel")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setObjectName("InputField")
        self.input.setAlignment(Qt.AlignRight)
        self.input.setText(format_miles_colombian_int(saldo_actual))
        layout.addWidget(self.input)

        # Formateo automático de miles
        self.input.textChanged.connect(self.on_text_changed)

        # Botón guardar
        btn = QPushButton("Guardar")
        btn.setObjectName("CreateMemberButton")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        qss_path = os.path.join(STYLES_DIR, "new_member_dialog.qss")
        load_styles(self, qss_path)

    def on_text_changed(self, text):
        if not text:
            return
        raw = parse_miles_colombian(text)
        formatted = format_miles_colombian_int(raw)
        if formatted != text:
            cursor = self.input.cursorPosition()
            self.input.blockSignals(True)
            self.input.setText(formatted)
            self.input.setCursorPosition(len(formatted))
            self.input.blockSignals(False)

    def get_saldo(self):
        return parse_miles_colombian(self.input.text())