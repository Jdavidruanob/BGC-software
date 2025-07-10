import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt

from config import load_styles, format_miles_colombian_int, parse_miles_colombian
from views.widgets.message_boxes import show_success, show_error, show_warning


class FormAporte(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.socios_data = []
        self.aportes_widgets = []

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

        # Título
        title = QLabel("📥 Registro de Aporte")
        title.setObjectName("formTitle")
        main_layout.addWidget(title)

        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = QComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumWidth(300)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)

        # Sección dinámicos de aportes
        aporte_section_label = QLabel("Aportes a registrar:")
        aporte_section_label.setObjectName("FormLabel")
        main_layout.addWidget(aporte_section_label)

        self.aportes_container = QVBoxLayout()
        self.aportes_container.setSpacing(12)
        main_layout.addLayout(self.aportes_container)

        # Botón agregar nueva fila
        self.btn_agregar_aporte = QPushButton("➕ Agregar aporte")
        self.btn_agregar_aporte.setObjectName("AddAporteButton")
        self.btn_agregar_aporte.clicked.connect(self.agregar_aporte)
        main_layout.addWidget(self.btn_agregar_aporte, alignment=Qt.AlignLeft)

        # Espacio y botón registrar
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Registrar Aporte")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial y primera fila
        self.load_socios()
        self.agregar_aporte()

        # Estilos
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "styles", "forms", "form_aporte.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        """Carga lista de socios para combo_recibi_de."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_recibi_de.clear()
            if not self.socios_data:
                show_warning(self, "", "No hay socios registrados.")
                return
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']} (Saldo: {format_miles_colombian_int(socio['saldo'])})"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_aporte(self):
        """Agrega una fila con ComboSocio + MontoInput + DeleteButton."""
        combo = QComboBox()
        combo.setObjectName("ComboSocio")
        combo.setMinimumWidth(250)
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']} (Saldo: {format_miles_colombian_int(socio['saldo'])})"
            combo.addItem(nombre, userData=socio)

        monto_input = QLineEdit()
        monto_input.setObjectName("MontoInput")
        monto_input.setPlaceholderText("Monto del aporte")
        monto_input.setAlignment(Qt.AlignRight)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                monto_input.blockSignals(True)
                monto_input.setText(formatted)
                monto_input.setCursorPosition(len(formatted))
                monto_input.blockSignals(False)
        monto_input.textChanged.connect(on_text_changed)

        btn_eliminar = QPushButton("❌")
        btn_eliminar.setObjectName("DeleteButton")
        btn_eliminar.setFixedSize(28, 28)
        btn_eliminar.setToolTip("Eliminar este aporte")

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(10)
        row_layout.addWidget(combo, 3)
        row_layout.addWidget(monto_input, 1)
        row_layout.addWidget(btn_eliminar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        container = QVBoxLayout()
        container.setContentsMargins(0,0,0,0)
        container.addWidget(row_widget)
        container.addWidget(line)

        wrapper = QWidget()
        wrapper.setLayout(container)
        self.aportes_container.addWidget(wrapper)
        self.aportes_widgets.append((combo, monto_input, wrapper))

        def eliminar():
            wrapper.setParent(None)
            self.aportes_widgets[:] = [t for t in self.aportes_widgets if t[2] is not wrapper]
        btn_eliminar.clicked.connect(eliminar)

    def on_register(self):
        """Valida datos, registra recibo y muestra mensaje."""
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        aportes = []
        for combo, monto_input, _ in self.aportes_widgets:
            socio = combo.currentData()
            raw = parse_miles_colombian(monto_input.text())
            if not socio or raw <= 0:
                show_error(self, "", "Revisa que todos los aportes tengan socio y monto válido.")
                return
            aportes.append((socio['id'], raw))

        if not aportes:
            show_warning(self, "", "Debes agregar al menos un aporte.")
            return

        try:
            recibo_id = self.db.create_aporte_recibo(recibi['id'], aportes)
            if recibo_id:
                show_success(self, "", f"Recibo #{recibo_id} creado y saldos actualizados.")
            else:
                show_error(self, "", "No se pudo registrar el aporte. Intenta nuevamente.")
        except Exception as e:
            show_error(self, "", f"Error al registrar aporte:\n{e}")

    def refresh(self):
        """Recarga lista de socios en todos los combos."""
        self.load_socios()
        for combo, _, _ in self.aportes_widgets:
            combo.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']} (Saldo: {format_miles_colombian_int(socio['saldo'])})"
                combo.addItem(nombre, userData=socio)

    def get_socio_recibi_de(self):
        return self.combo_recibi_de.currentData()

    def get_aportes(self):
        return [
            (combo.currentData(), parse_miles_colombian(input.text()))
            for combo, input, _ in self.aportes_widgets
        ]
