import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QSize
from config import load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR

# --- CONSTANTE DE CARACTERES ---
MAX_MOTIVO_LENGTH = 15

class EditSaldoDialog(QDialog):
    def __init__(self, saldo_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuste de Caja")
        self.setModal(True)
        self.setFixedSize(420, 380)
        self.setObjectName("AdjustBalanceDialog")

        # Estado inicial
        self.is_ingreso = True # True = Sumar, False = Restar
        self.saldo_actual_ref = saldo_actual

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)

        # 1. SELECCIÓN DE TIPO (Botones Toggle)
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)

        self.btn_ingreso = QPushButton("▲ INGRESO ")
        self.btn_ingreso.setCursor(Qt.PointingHandCursor)
        self.btn_ingreso.setProperty("mode", "ingreso")
        self.btn_ingreso.setProperty("active", True) # Por defecto activo
        # --- CORRECCIÓN AQUÍ: Usamos setProperty en lugar de setClass ---
        self.btn_ingreso.setProperty("class", "modeButton") 
        self.btn_ingreso.clicked.connect(lambda: self.toggle_mode(True))

        self.btn_egreso = QPushButton("▼ EGRESO")
        self.btn_egreso.setCursor(Qt.PointingHandCursor)
        self.btn_egreso.setProperty("mode", "egreso")
        self.btn_egreso.setProperty("active", False)
        # --- CORRECCIÓN AQUÍ ---
        self.btn_egreso.setProperty("class", "modeButton")
        self.btn_egreso.clicked.connect(lambda: self.toggle_mode(False))

        type_layout.addWidget(self.btn_ingreso)
        type_layout.addWidget(self.btn_egreso)
        layout.addLayout(type_layout)

        # 2. MONTO
        lbl_monto = QLabel("Monto del ajuste:")
        lbl_monto.setObjectName("FormLabel")
        layout.addWidget(lbl_monto)

        self.input_monto = QLineEdit()
        self.input_monto.setObjectName("InputField")
        self.input_monto.setAlignment(Qt.AlignRight)
        self.input_monto.setPlaceholderText("$ 0")
        self.input_monto.textChanged.connect(self.on_monto_changed)
        layout.addWidget(self.input_monto)

        # 3. MOTIVO (Obligatorio)
        lbl_motivo = QLabel("Motivo (Max 15 caracteres.):")
        lbl_motivo.setObjectName("FormLabel")
        layout.addWidget(lbl_motivo)

        self.input_motivo = QLineEdit()
        self.input_motivo.setObjectName("InputField")
        self.input_motivo.setPlaceholderText("Ej: Error en cambio, Ajuste inicial")
        self.input_motivo.textChanged.connect(self.on_motivo_changed)
        layout.addWidget(self.input_motivo)

        # Contador de caracteres
        self.char_counter = QLabel(f"0 / {MAX_MOTIVO_LENGTH}")
        self.char_counter.setObjectName("CharCounter")
        self.char_counter.setAlignment(Qt.AlignRight)
        layout.addWidget(self.char_counter)

        layout.addStretch()

        # 4. BOTÓN GUARDAR
        self.btn_guardar = QPushButton("Aplicar Ajuste")
        self.btn_guardar.setObjectName("ActionSaveButton")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self.accept)
        self.btn_guardar.setEnabled(False) # Deshabilitado hasta validar
        layout.addWidget(self.btn_guardar)

        self.setLayout(layout)
        
        # Cargar el estilo
        qss_path = os.path.join(STYLES_DIR, "adjust_balance_dialog.qss")
        load_styles(self, qss_path)

    def toggle_mode(self, is_ingreso):
        self.is_ingreso = is_ingreso
        
        # Actualizar propiedades visuales
        self.btn_ingreso.setProperty("active", is_ingreso)
        self.btn_egreso.setProperty("active", not is_ingreso)
        
        # Forzar recarga de estilo para aplicar cambios de color
        self.btn_ingreso.style().unpolish(self.btn_ingreso)
        self.btn_ingreso.style().polish(self.btn_ingreso)
        self.btn_egreso.style().unpolish(self.btn_egreso)
        self.btn_egreso.style().polish(self.btn_egreso)

    def on_monto_changed(self, text):
        if not text: return
        raw = parse_miles_colombian(text)
        formatted = format_miles_colombian_int(raw)
        if formatted != text:
            self.input_monto.blockSignals(True)
            self.input_monto.setText(formatted)
            self.input_monto.setCursorPosition(len(formatted))
            self.input_monto.blockSignals(False)
        self.validate_form()

    def on_motivo_changed(self, text):
        count = len(text)
        self.char_counter.setText(f"{count} / {MAX_MOTIVO_LENGTH}")
        
        # Validar longitud visualmente
        is_excess = count > MAX_MOTIVO_LENGTH
        self.char_counter.setProperty("limitReached", is_excess)
        self.char_counter.style().unpolish(self.char_counter)
        self.char_counter.style().polish(self.char_counter)
        
        self.validate_form()

    def validate_form(self):
        monto = parse_miles_colombian(self.input_monto.text())
        motivo = self.input_motivo.text().strip()
        
        # Condiciones: Monto > 0, Motivo no vacío, Motivo <= Limite
        is_valid = (monto > 0) and (len(motivo) > 0) and (len(motivo) <= MAX_MOTIVO_LENGTH)
        
        self.btn_guardar.setEnabled(is_valid)

    def get_data(self):
        """
        Retorna: (monto_con_signo, texto_motivo, nuevo_saldo_calculado)
        """
        monto_abs = parse_miles_colombian(self.input_monto.text())
        motivo = self.input_motivo.text().strip()
        
        if self.is_ingreso:
            monto_final = monto_abs
        else:
            monto_final = -monto_abs
            
        nuevo_saldo = self.saldo_actual_ref + monto_final
        
        return monto_final, motivo, nuevo_saldo