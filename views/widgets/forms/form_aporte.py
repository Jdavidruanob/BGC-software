

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QSize, Signal
from datetime import date
from config import (
    load_styles, load_svg_icon, format_miles_colombian_int, 
    parse_miles_colombian, get_hoy, get_hoy_str, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR 
)
from utils.message_boxes import show_success, show_error, show_warning
from services.aporte_service import AporteService

class NoScrollComboBox(QComboBox): 
    def wheelEvent(self, event):
        event.ignore()

class FormAporte(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self._service = AporteService(db_manager)
        self.socios_data = [] # Esta lista debe contener los dicts completos de los socios con su 'saldo' actual
        self.aportes_widgets = []

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 0, 20, 30)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(50)
        self.combo_recibi_de.setMaximumHeight(50)

        self.combo_recibi_de.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)

        aporte_section_label = QLabel("Aportes a registrar:")
        aporte_section_label.setObjectName("FormLabel")
        main_layout.addWidget(aporte_section_label)

        self.aportes_container = QVBoxLayout()
        self.aportes_container.setSpacing(12)
        main_layout.addLayout(self.aportes_container)

        self.btn_agregar_aporte = QPushButton(" Agregar aporte")
        self.btn_agregar_aporte.setObjectName("AddAporteButton")
        self.btn_agregar_aporte.setIcon(load_svg_icon("icons/plus.svg"))
        self.btn_agregar_aporte.setIconSize(QSize(20, 20))
        self.btn_agregar_aporte.clicked.connect(self.agregar_aporte)
        main_layout.addWidget(self.btn_agregar_aporte, alignment=Qt.AlignLeft)

        main_layout.addStretch()
        self.btn_registrar = QPushButton("Registrar Aporte")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.load_socios()

        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_aporte.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        try:
            # Asegúrate de que get_all_members_full() retorne el 'saldo' actual de cada socio
            self.socios_data = self.db.get_all_members_full() 
            self.combo_recibi_de.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
            
            # Recargar los combos existentes
            # AHORA DESEMPAQUETAMOS 4 ELEMENTOS: combo, input, check, wrapper
            for combo, _, _, _ in self.aportes_widgets: 
                combo.clear()
                for socio in self.socios_data:
                    nombre = f"{socio['nombres']} {socio['apellidos']}"
                    combo.addItem(nombre, userData=socio)

        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_aporte(self):
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocio")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']}"
            combo.addItem(nombre, userData=socio)

        monto_input = QLineEdit()
        monto_input.setObjectName("MontoInput")
        monto_input.setPlaceholderText("Monto aporte")
        monto_input.setAlignment(Qt.AlignRight)
        monto_input.setFixedHeight(34)
        monto_input.setFixedWidth(140)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                monto_input.blockSignals(True)
                monto_input.setText(formatted)
                monto_input.setCursorPosition(len(formatted))
                monto_input.blockSignals(False)
        monto_input.textChanged.connect(on_text_changed)

        # --- NUEVO CHECKBOX ---
        chk_papeleria = QCheckBox("")
        chk_papeleria.setObjectName("ChkPapeleria") # Para darle estilo si quieres
        chk_papeleria.setChecked(True) # Por defecto activado
        chk_papeleria.setToolTip("Desmarcar para no cobrar gastos de administración a este aporte")
        # Ajuste visual opcional
        chk_papeleria.setCursor(Qt.PointingHandCursor)
        # ----------------------

        btn_eliminar = QPushButton("")
        btn_eliminar.setObjectName("DeleteButton")
        btn_eliminar.setIcon(load_svg_icon("icons/x.svg"))
        btn_eliminar.setIconSize(QSize(20, 20))
        btn_eliminar.setToolTip("Eliminar aporte")
        btn_eliminar.setFixedSize(28, 28)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(combo)
        row_layout.addWidget(monto_input)
        row_layout.addWidget(chk_papeleria)
        row_layout.addWidget(btn_eliminar)

        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(row_widget)

        wrapper = QWidget()
        wrapper.setLayout(container)
        self.aportes_container.addWidget(wrapper)
        # Debes agregar chk_papeleria a la tupla
        self.aportes_widgets.append((combo, monto_input, chk_papeleria, wrapper))

        def eliminar():
            wrapper.setParent(None)
            # CORRECCIÓN CLAVE: Buscar el wrapper en el índice 3
            self.aportes_widgets[:] = [t for t in self.aportes_widgets if t[3] is not wrapper]
        btn_eliminar.clicked.connect(eliminar)

    def on_register(self):
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        aportes = []
        count_cobrables = 0
        for combo, monto_input, chk_papeleria, _ in self.aportes_widgets:
            socio_selected = combo.currentData()
            raw_monto = parse_miles_colombian(monto_input.text())
            if not socio_selected or raw_monto <= 0:
                show_error(self, "", "Revisa que todos los aportes tengan socio y monto válido.")
                return
            if chk_papeleria.isChecked():
                count_cobrables += 1
            socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
            if not socio_data_full:
                show_error(self, "", f"No se encontraron datos completos para el socio ID: {socio_selected['id']}")
                return
            aportes.append((socio_data_full, raw_monto))

        if not aportes:
            show_warning(self, "", "Debes agregar al menos un aporte.")
            return

        if len(aportes) > 6:
            show_warning(self, "", "El programa solo puede generar 6 aportes por recibo. Por favor, genere un segundo recibo si es necesario.")
            return

        try:
            recibo_id, excel_path = self._service.register(recibi['id'], recibi, aportes, count_cobrables)
            if excel_path:
                show_success(self, "", f"Recibo #{recibo_id} creado y saldos actualizados.", file_path=excel_path)
            else:
                show_warning(self, "", "Recibo creado y saldos actualizados, pero hubo un error al generar el archivo Excel.")
            self.operation_registered.emit()
            self.clear_form()
            self.load_socios()
        except ValueError as e:
            show_error(self, "", str(e))
        except Exception as e:
            show_error(self, "", f"Error al registrar aporte:\n{e}")


    def refresh(self):
        # Este método ahora puede simplemente llamar a load_socios
        # que ya se encarga de actualizar los combos existentes
        self.load_socios()
        # Y también limpiar el formulario si es necesario
        self.clear_form()

    def get_socio_recibi_de(self):
        return self.combo_recibi_de.currentData()

    def get_aportes(self):
        return [
            (combo.currentData(), parse_miles_colombian(input.text()))
            for combo, input, _, _ in self.aportes_widgets # <--- Ignoramos check y wrapper
        ]

    def clear_form(self):
        for _, _, _, wrapper in self.aportes_widgets: # <--- Usamos el 4to elemento
            wrapper.setParent(None) 
        self.aportes_widgets.clear()