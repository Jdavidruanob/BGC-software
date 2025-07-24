from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QHBoxLayout, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt
from datetime import date
import os

from config import load_styles, load_svg_icon, parse_miles_colombian, format_miles_colombian_int
from views.widgets.message_boxes import show_success, show_error, show_warning
from utils.recibo_generator_retiro import generar_recibo_retiro

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class FormRetiro(QWidget):
    def __init__(self, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.saldo_actual_socio = 0

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(20)

        # Socio + input en una fila
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.combo_socio = NoScrollComboBox()
        self.combo_socio.setObjectName("ComboSocio")
        self.combo_socio.setMinimumHeight(36)
        self.combo_socio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_socio.currentIndexChanged.connect(self.actualizar_preview)
        top_row.addWidget(self.combo_socio, 2)

        self.input_monto = QLineEdit()
        self.input_monto.setObjectName("MontoInput")
        self.input_monto.setPlaceholderText("Monto a retirar")
        self.input_monto.setAlignment(Qt.AlignRight)
        self.input_monto.setFixedHeight(36)
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
        top_row.addWidget(self.input_monto, 1)

        layout.addLayout(top_row)

        # Previsualización del saldo restante
        self.label_preview = QLabel("")
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setStyleSheet("font-size: 18px; color: #333;")
        layout.addWidget(self.label_preview)

        layout.addSpacerItem(QSpacerItem(0, 12))

        # Botón de registrar
        self.btn_registrar = QPushButton("Registrar Retiro")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.clicked.connect(self.on_register_retiro)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.setLayout(layout)
        self.load_socios()

        qss_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "styles", "forms", "form_retiro.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socio.addItem(nombre, userData=socio)
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
            nuevo_saldo = saldo_actual - monto
            self.label_preview.setText(
                f"<b>Saldo tras retiro:</b> ${format_miles_colombian_int(nuevo_saldo)}"
            )
        else:
            self.label_preview.setText("")

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
            nuevo_saldo_caja = saldo_caja - monto # Cambié el nombre de la variable para evitar confusión
            self.db.set_config_value("saldo_en_caja", str(nuevo_saldo_caja))

            # 5. Guardar en auxiliar
            fecha_actual = date.today().strftime("%Y-%m-%d")
            nombre_completo_socio = f"{socio['nombres']} {socio['apellidos']}" # Usar para auxiliar

            self.db.add_to_auxiliar(
                fecha=fecha_actual,
                tipo="Retiro",
                socio=nombre_completo_socio, # Usar el nombre completo
                numero=recibo_id,
                monto=-monto, # Los retiros son valores negativos en auxiliar
                saldo=socio['saldo'] - monto # El saldo es el nuevo saldo del socio
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
                    "saldo": socio['saldo'] - monto
                })

            self.db.conn.commit()

            # Mostrar mensaje de éxito y la ruta del archivo generado
            if generated_receipt_path:
                show_success(self, "", f"Retiro registrado exitosamente. Recibo #{recibo_id} generado en:\n{generated_receipt_path}")
            else:
                show_success(self, "", f"Retiro registrado exitosamente. Recibo #{recibo_id} (no se pudo generar el archivo).")

            self.refresh()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "", f"Error al registrar retiro:\n{e}")

    def refresh(self):
        """Recarga los socios y limpia los campos del formulario."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.clear()
            if not self.socios_data:
                show_warning(self, "", "No hay socios registrados.")
                return
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socio.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

        # Limpiar campos
        self.input_monto.clear()
        self.label_preview.setText("")
