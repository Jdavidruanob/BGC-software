import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from config import load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR

class EditAdminDialog(QDialog):
    def __init__(self, current_papeleria, current_mora_pct,
                 current_next_recibo=1, current_next_letra=1, parent=None,
                 current_fondo_mora=0):
        super().__init__(parent)
        self.setWindowTitle("Configurar Administración")
        self.setModal(True)
        self.setMinimumSize(470, 500)
        self.setObjectName("NewMemberDialog")  # Reutilizamos el estilo base

        self._orig_recibo = int(current_next_recibo)
        self._orig_letra = int(current_next_letra)

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

        # --- CAMPO 2: FONDO ACUMULADO DE MORA ---
        lbl_fondo_mora = QLabel("Fondo Acumulado Mora:")
        lbl_fondo_mora.setObjectName("FormLabel")
        layout.addWidget(lbl_fondo_mora)

        self.input_fondo_mora = QLineEdit()
        self.input_fondo_mora.setObjectName("InputField")
        self.input_fondo_mora.setAlignment(Qt.AlignRight)
        self.input_fondo_mora.setText(format_miles_colombian_int(current_fondo_mora))
        self.input_fondo_mora.textChanged.connect(self.on_fondo_mora_changed)
        layout.addWidget(self.input_fondo_mora)

        # --- CAMPO 3: PORCENTAJE DE MORA ---
        lbl_mora = QLabel("Porcentaje Interés Mora (0.01 - 1.0):")
        lbl_mora.setObjectName("FormLabel")
        layout.addWidget(lbl_mora)

        self.input_mora = QLineEdit()
        self.input_mora.setObjectName("InputField")
        self.input_mora.setAlignment(Qt.AlignRight)
        self.input_mora.setText(str(current_mora_pct))
        self.input_mora.setPlaceholderText("Ej: 0.02")
        layout.addWidget(self.input_mora)

        # --- CAMPO 3: PRÓXIMO NÚMERO DE RECIBO ---
        lbl_recibo = QLabel("Número del próximo recibo:")
        lbl_recibo.setObjectName("FormLabel")
        layout.addWidget(lbl_recibo)

        self.input_next_recibo = QLineEdit()
        self.input_next_recibo.setObjectName("InputField")
        self.input_next_recibo.setAlignment(Qt.AlignRight)
        self.input_next_recibo.setValidator(QIntValidator(1, 99999999, self))
        self.input_next_recibo.setText(str(current_next_recibo))
        layout.addWidget(self.input_next_recibo)

        # --- CAMPO 4: PRÓXIMA LETRA (CRÉDITO) ---
        lbl_letra = QLabel("Número de la próxima letra (crédito):")
        lbl_letra.setObjectName("FormLabel")
        layout.addWidget(lbl_letra)

        self.input_next_letra = QLineEdit()
        self.input_next_letra.setObjectName("InputField")
        self.input_next_letra.setAlignment(Qt.AlignRight)
        self.input_next_letra.setValidator(QIntValidator(1, 99999999, self))
        self.input_next_letra.setText(str(current_next_letra))
        layout.addWidget(self.input_next_letra)

        nota = QLabel("Al cambiar estos números, el sistema sigue automático desde ahí.")
        nota.setWordWrap(True)
        nota.setObjectName("HelpText")
        layout.addWidget(nota)

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

    def on_fondo_mora_changed(self, text):
        """Formato de miles en tiempo real para el fondo de mora"""
        if not text: return
        raw = parse_miles_colombian(text)
        formatted = format_miles_colombian_int(raw)
        if formatted != text:
            self.input_fondo_mora.blockSignals(True)
            self.input_fondo_mora.setText(formatted)
            self.input_fondo_mora.setCursorPosition(len(formatted))
            self.input_fondo_mora.blockSignals(False)

    def get_data(self):
        """Retorna (papeleria, mora_pct, next_recibo, next_letra, fondo_mora)"""
        papeleria = parse_miles_colombian(self.input_papeleria.text())
        fondo_mora = parse_miles_colombian(self.input_fondo_mora.text())

        try:
            mora = float(self.input_mora.text().replace(',', '.'))
        except ValueError:
            mora = 0.02 # Valor por defecto si fallan

        try:
            next_recibo = int(self.input_next_recibo.text().strip() or self._orig_recibo)
        except ValueError:
            next_recibo = self._orig_recibo
        try:
            next_letra = int(self.input_next_letra.text().strip() or self._orig_letra)
        except ValueError:
            next_letra = self._orig_letra

        return papeleria, mora, next_recibo, next_letra, fondo_mora