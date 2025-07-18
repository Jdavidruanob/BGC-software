from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox, QSizePolicy, QSpacerItem, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QSize
from datetime import date
import os

from config import load_styles, load_svg_icon, parse_miles_colombian, format_miles_colombian_int
from views.widgets.message_boxes import show_success, show_error, show_warning

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita scroll accidental

class FormNuevoCredito(QWidget):
    def __init__(self, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.socios_seleccionados = []

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(24)

        # Combo de socios
        self.combo_socios = NoScrollComboBox()
        self.combo_socios.setObjectName("ComboSocio")
        self.combo_socios.setMinimumHeight(36)
        self.combo_socios.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_socios.currentIndexChanged.connect(self.agregar_socio_seleccionado)

        lbl_socio = QLabel("Seleccionar Socio:")
        lbl_socio.setObjectName("FormLabel")
        layout.addWidget(lbl_socio)
        layout.addWidget(self.combo_socios)

        # Contenedor de socios seleccionados
        self.selected_container = QHBoxLayout()
        self.selected_container.setSpacing(8)
        layout.addLayout(self.selected_container)

        # Sección horizontal para capital, cuotas e interés
        fields_row = QHBoxLayout()
        fields_row.setSpacing(20)

        # Capital
        self.capital_input = QLineEdit()
        self.capital_input.setObjectName("MontoInput")
        self.capital_input.setPlaceholderText("Capital del crédito")
        self.capital_input.setAlignment(Qt.AlignRight)
        self.capital_input.setFixedHeight(36)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                self.capital_input.blockSignals(True)
                self.capital_input.setText(formatted)
                self.capital_input.setCursorPosition(len(formatted))
                self.capital_input.blockSignals(False)

        self.capital_input.textChanged.connect(on_text_changed)

        # Cuotas
        self.cuotas_input = QLineEdit()
        self.cuotas_input.setPlaceholderText("Número de cuotas")
        self.cuotas_input.setAlignment(Qt.AlignRight)
        self.cuotas_input.setFixedHeight(36)

        # Interés
        self.interes_input = QLineEdit()
        self.interes_input.setPlaceholderText("Interés mensual (ej: 0.015)")
        self.interes_input.setAlignment(Qt.AlignRight)
        self.interes_input.setText("0.01")
        self.interes_input.setFixedHeight(36)

        fields_row.addWidget(self.capital_input)
        fields_row.addWidget(self.cuotas_input)
        fields_row.addWidget(self.interes_input)

        layout.addLayout(fields_row)
        layout.addSpacerItem(QSpacerItem(0, 20))

        # Botón registrar
        self.btn_registrar = QPushButton("Crear Crédito")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.clicked.connect(self.on_register_credito)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

        self.load_socios()

        # Estilos
        qss_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "styles", "forms", "form_nuevo_credito.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socios.clear()
            if not self.socios_data:
                show_warning(self, "", "No hay socios registrados.")
                return
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socios.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_socio_seleccionado(self):
        socio = self.combo_socios.currentData()
        if not socio or socio in self.socios_seleccionados:
            return
        self.socios_seleccionados.append(socio)
        self.mostrar_socio_tag(socio)

    def mostrar_socio_tag(self, socio):
        wrapper = QFrame()
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)
        wrapper.setStyleSheet("background-color: #f1f5f9; border-radius: 12px;")

        label = QLabel(f"{socio['nombres']} {socio['apellidos']}")
        label.setStyleSheet("font-size: 14px;")

        btn = QPushButton("")
        btn.setFixedSize(22, 22)
        btn.setIcon(load_svg_icon("assets/icons/x.svg"))
        btn.setStyleSheet("border: none; background: transparent;")

        def eliminar():
            wrapper.setParent(None)
            self.socios_seleccionados.remove(socio)

        btn.clicked.connect(eliminar)

        layout.addWidget(label)
        layout.addWidget(btn)
        wrapper.setLayout(layout)
        self.selected_container.addWidget(wrapper)

    def on_register_credito(self):
        try:
            if not self.socios_seleccionados:
                show_warning(self, "", "Debes seleccionar al menos un socio.")
                return

            capital = parse_miles_colombian(self.capital_input.text())
            interes = float(self.interes_input.text())
            cuotas = int(self.cuotas_input.text())

            if capital <= 0 or interes <= 0 or cuotas <= 0:
                show_error(self, "", "Revisa que todos los valores sean válidos y positivos.")
                return

            socio_ids = [s['id'] for s in self.socios_seleccionados]
            letra = self.db.add_credit(socio_ids, capital, interes, cuotas)

            if letra:
                saldo_actual = self.db.get_config_value_as_int("saldo_en_caja")
                nuevo_saldo = saldo_actual - capital
                self.db.set_config_value("saldo_en_caja", str(nuevo_saldo))

                fecha_actual = date.today().strftime("%Y-%m-%d")
                nombres = ", ".join([f"{s['nombres']} {s['apellidos']}" for s in self.socios_seleccionados])

                self.db.add_to_auxiliar(
                    fecha=fecha_actual,
                    tipo="Nuevo Credito",
                    socio=nombres,
                    numero=letra,
                    monto=-capital,
                    saldo=nuevo_saldo
                )

                if self.assistant_page:
                    self.assistant_page.add_operation({
                        "fecha": fecha_actual,
                        "tipo": "Nuevo Credito",
                        "socio": nombres,
                        "numero": letra,
                        "monto": -capital,
                        "saldo": nuevo_saldo
                    })

                show_success(self, "", "Crédito creado exitosamente.")

                self.capital_input.clear()
                self.interes_input.setText("0.01")
                self.cuotas_input.clear()
                self.socios_seleccionados.clear()

                # Limpia las etiquetas
                while self.selected_container.count():
                    item = self.selected_container.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

        except Exception as e:
            show_error(self, "", f"Error al crear crédito:\n{e}")
