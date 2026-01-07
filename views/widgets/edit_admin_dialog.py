import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from config import load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR

class EditAdminDialog(QDialog):
    def __init__(self, current_papeleria, current_mora_pct, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Administración")
        self.setModal(True)
        self.setFixedSize(450, 320)
        self.setObjectName("NewMemberDialog")  # Reutilizamos el estilo base

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        # --- CAMPO 1: FONDO DE PAPELERÍA ---
        lbl_papeleria = QLabel("Fondo Acumulado Papelería:")
        lbl_papeleria.setObjectName("FormLabel")
        layout.addWidget(lbl_papeleria)

        self.input_papeleria = QLineEdit()
        self.input_papeleria.setObjectName("InputField")
        self.input_papeleria.setAlignment(Qt.AlignRight)
        self.input_papeleria.setText(format_miles_colombian_int(current_papeleria))
        self.input_papeleria.textChanged.connect(self.on_papeleria_changed)
        layout.addWidget(self.input_papeleria)

        # --- CAMPO 2: PORCENTAJE DE MORA ---
        lbl_mora = QLabel("Porcentaje Interés Mora (0.01 - 1.0):")
        lbl_mora.setObjectName("FormLabel")
        layout.addWidget(lbl_mora)

        self.input_mora = QLineEdit()
        self.input_mora.setObjectName("InputField")
        self.input_mora.setAlignment(Qt.AlignRight)
        self.input_mora.setText(str(current_mora_pct))
        self.input_mora.setPlaceholderText("Ej: 0.02")
        layout.addWidget(self.input_mora)

        layout.addStretch()

        # --- BOTÓN GUARDAR ---
        btn_save = QPushButton("Guardar Cambios")
        btn_save.setObjectName("CreateMemberButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        
        # Cargamos el estilo compartido
        qss_path = os.path.join(STYLES_DIR, "new_member_dialog.qss")
        load_styles(self, qss_path)

    def on_papeleria_changed(self, text):
        """Formato de miles en tiempo real para papelería"""
        if not text: return
        raw = parse_miles_colombian(text)
        formatted = format_miles_colombian_int(raw)
        if formatted != text:
            self.input_papeleria.blockSignals(True)
            self.input_papeleria.setText(formatted)
            self.input_papeleria.setCursorPosition(len(formatted))
            self.input_papeleria.blockSignals(False)

    def get_data(self):
        """Retorna (int_papeleria, float_mora)"""
        papeleria = parse_miles_colombian(self.input_papeleria.text())
        
        try:
            mora = float(self.input_mora.text().replace(',', '.'))
        except ValueError:
            mora = 0.02 # Valor por defecto si fallan
            
        return papeleria, mora