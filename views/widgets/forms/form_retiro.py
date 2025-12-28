from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QHBoxLayout, QSizePolicy, QSpacerItem, QFrame
)
from PySide6.QtCore import Qt, Signal
from datetime import date
import os

from config import load_styles, load_svg_icon, parse_miles_colombian, format_miles_colombian_int, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning
from utils.recibo_generator_retiro import generar_recibo_retiro

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class FormRetiro(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.saldo_actual_socio = 0

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 0, 20, 30)
        layout.setSpacing(20)

        # Título
        lbl_titulo = QLabel("Socio que retira:")
        lbl_titulo.setObjectName("FormLabel")
        layout.addWidget(lbl_titulo)

        # Combo de socio
        self.combo_socio = NoScrollComboBox()
        self.combo_socio.setObjectName("ComboSocio")
        self.combo_socio.setMinimumHeight(50)
        self.combo_socio.setMaximumHeight(50)
        self.combo_socio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_socio.currentIndexChanged.connect(self.actualizar_preview)
        layout.addWidget(self.combo_socio)

        # Tarjeta de saldo disponible
        self.card_saldo = QFrame()
        self.card_saldo.setObjectName("CardSaldoDisponible")
        card_saldo_layout = QHBoxLayout()
        card_saldo_layout.setContentsMargins(16, 20, 16, 20)
        card_saldo_layout.setSpacing(16)

        # Icono
        icon_label = QLabel()
        icon_label.setPixmap(load_svg_icon("icons/credit-card.svg").pixmap(28, 28))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent")

        # Información de saldo
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        titulo_saldo = QLabel("SALDO DISPONIBLE EN APORTES")
        titulo_saldo.setObjectName("TituloSaldoDisponible")

        subtitulo_saldo = QLabel("Puede retirar hasta este monto")
        subtitulo_saldo.setObjectName("SubtituloSaldoDisponible")

        info_layout.addWidget(titulo_saldo)
        info_layout.addWidget(subtitulo_saldo)

        # Monto de saldo
        self.label_saldo_disponible = QLabel("$0")
        self.label_saldo_disponible.setObjectName("MontoSaldoDisponible")
        self.label_saldo_disponible.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        card_saldo_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        card_saldo_layout.addLayout(info_layout, 1)
        card_saldo_layout.addWidget(self.label_saldo_disponible, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.card_saldo.setLayout(card_saldo_layout)
        layout.addWidget(self.card_saldo)

        layout.addSpacerItem(QSpacerItem(0, 16))

        # Fila de inputs: Monto a Retirar y Saldo Final
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(20)

        # Columna izquierda: Monto a Retirar
        monto_col = QVBoxLayout()
        monto_col.setSpacing(8)
        lbl_monto = QLabel("Monto a Retirar:")
        lbl_monto.setObjectName("FormLabel")
        
        self.input_monto = QLineEdit()
        self.input_monto.setObjectName("MontoInput")
        self.input_monto.setPlaceholderText("$")
        self.input_monto.setAlignment(Qt.AlignRight)
        self.input_monto.setFixedHeight(40)
        self.input_monto.textChanged.connect(self.actualizar_preview)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                self.input_monto.blockSignals(True)
                self.input_monto.setText(formatted)
                self.input_monto.setCursorPosition(len(formatted))
                self.input_monto.blockSignals(False)

        self.input_monto.textChanged.connect(on_text_changed)
        
        monto_col.addWidget(lbl_monto)
        monto_col.addWidget(self.input_monto)

        # Columna derecha: Saldo Final Estimado
        saldo_final_col = QVBoxLayout()
        saldo_final_col.setSpacing(8)
        lbl_saldo_final = QLabel("Saldo Final Estimado:")
        lbl_saldo_final.setObjectName("FormLabel")

        # Tarjeta de saldo final
        self.card_saldo_final = QFrame()
        self.card_saldo_final.setObjectName("CardSaldoFinal")
        card_final_layout = QHBoxLayout()
        card_final_layout.setContentsMargins(12, 8, 12, 8)
        card_final_layout.setSpacing(8)

        lbl_quedan = QLabel("Quedan:")
        lbl_quedan.setObjectName("LabelQuedan")

        self.label_saldo_final = QLabel("$0")
        self.label_saldo_final.setObjectName("MontoSaldoFinal")

        card_final_layout.addWidget(lbl_quedan)
        card_final_layout.addStretch()
        card_final_layout.addWidget(self.label_saldo_final)
        self.card_saldo_final.setLayout(card_final_layout)

        saldo_final_col.addWidget(lbl_saldo_final)
        saldo_final_col.addWidget(self.card_saldo_final)

        inputs_row.addLayout(monto_col, 1)
        inputs_row.addLayout(saldo_final_col, 1)
        layout.addLayout(inputs_row)

        layout.addSpacerItem(QSpacerItem(0, 40))

        # Botón de registrar
        self.btn_registrar = QPushButton("Registrar Retiro")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.clicked.connect(self.on_register_retiro)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.setLayout(layout)
        self.load_socios()

        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_retiro.qss"
        )
        load_styles(self, qss_path)

    # ...existing code...
    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.blockSignals(True)
            self.combo_socio.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socio.addItem(nombre, userData=socio)
            self.combo_socio.blockSignals(False)
            self.actualizar_preview()
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def actualizar_preview(self):
        socio = self.combo_socio.currentData()
        try:
            monto = parse_miles_colombian(self.input_monto.text())
        except:
            monto = 0

        if socio:
            saldo_actual = socio['saldo']
            self.label_saldo_disponible.setText(f"$ {format_miles_colombian_int(saldo_actual)}")
            nuevo_saldo = saldo_actual - monto
            self.label_saldo_final.setText(f"$ {format_miles_colombian_int(nuevo_saldo)}")
        else:
            self.label_saldo_disponible.setText("$0")
            self.label_saldo_final.setText("$0")

    def on_register_retiro(self):
        socio = self.combo_socio.currentData()
        if not socio:
            show_warning(self, "", "Debes seleccionar un socio.")
            return

        try:
            monto = parse_miles_colombian(self.input_monto.text())
        except:
            show_error(self, "", "Monto inválido.")
            return

        if monto <= 0:
            show_warning(self, "", "El monto debe ser mayor que cero.")
            return

        if monto > socio['saldo']:
            show_error(self, "", "El socio no tiene saldo suficiente para este retiro.")
            return

        try:
            cursor = self.db.conn.cursor()

            # 1. Insertar recibo
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (socio['id'],))
            recibo_id = cursor.lastrowid

            # 2. Insertar detalle
            cursor.execute("""
                INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                VALUES (?, 'retiro', ?, ?)
            """, (recibo_id, socio['id'], monto))

            # 3. Actualizar saldo socio
            cursor.execute("UPDATE socios SET saldo = saldo - ? WHERE id = ?", (monto, socio['id']))

            # 4. Actualizar saldo caja global
            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")
            nuevo_saldo_caja = saldo_caja - monto
            self.db.set_config_value("saldo_en_caja", str(nuevo_saldo_caja))

            # 5. Guardar en auxiliar
            fecha_actual = date.today().strftime("%Y-%m-%d")
            nombre_completo_socio = f"{socio['nombres']} {socio['apellidos']}"

            self.db.add_to_auxiliar(
                fecha=fecha_actual,
                tipo="Retiro",
                socio=nombre_completo_socio,
                numero=recibo_id,
                monto=-monto,
                saldo=nuevo_saldo_caja
            )

            # 6. Generar el recibo de retiro en Excel
            generated_receipt_path = generar_recibo_retiro(
                recibo_id=recibo_id,
                socio_data={'nombres': socio['nombres'], 'apellidos': socio['apellidos']},
                monto_retiro=monto
            )

            # 7. Agregar visual en AssistantPage
            if self.assistant_page:
                self.assistant_page.add_operation({
                    "fecha": fecha_actual,
                    "tipo": "Retiro",
                    "socio": nombre_completo_socio,
                    "numero": recibo_id,
                    "monto": -monto,
                    "saldo": nuevo_saldo_caja
                })

            self.db.conn.commit()

            if generated_receipt_path:
                show_success(self, "", f"Retiro registrado exitosamente. Recibo #{recibo_id}", file_path=generated_receipt_path)
                self.operation_registered.emit()

            else:
                show_success(self, "", f"Retiro registrado exitosamente. Recibo #{recibo_id}")

            self.refresh()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "", f"Error al registrar retiro:\n{e}")

    def refresh(self):
        """Recarga los socios y limpia los campos del formulario."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.blockSignals(True)
            self.combo_socio.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socio.addItem(nombre, userData=socio)
            self.combo_socio.blockSignals(False)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

        self.input_monto.clear()
        self.label_saldo_disponible.setText("$0")
        self.label_saldo_final.setText("$0")
        self.actualizar_preview()