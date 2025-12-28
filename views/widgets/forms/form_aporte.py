# views/forms/form_aporte.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal
from datetime import date
from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning

# Importar la función generar_recibo_general
from utils.recibo_generator_aporte import generar_recibo_solo_aportes # Importamos también la constante si la usamos

class NoScrollComboBox(QComboBox): 
    def wheelEvent(self, event):
        event.ignore()

class FormAporte(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
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
            
            # Recargar los combos existentes si se recargan los socios después de agregar aportes
            for combo, _, _ in self.aportes_widgets:
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
        monto_input.setPlaceholderText("Monto del aporte")
        monto_input.setAlignment(Qt.AlignRight)
        monto_input.setFixedHeight(34)
        monto_input.setFixedWidth(160)

        def on_text_changed(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                monto_input.blockSignals(True)
                monto_input.setText(formatted)
                monto_input.setCursorPosition(len(formatted))
                monto_input.blockSignals(False)
        monto_input.textChanged.connect(on_text_changed)

        btn_eliminar = QPushButton("")
        btn_eliminar.setObjectName("DeleteButton")
        btn_eliminar.setIcon(load_svg_icon("icons/x.svg"))
        btn_eliminar.setIconSize(QSize(20, 20))
        btn_eliminar.setToolTip("Eliminar aporte")
        btn_eliminar.setFixedSize(30, 30)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(combo)
        row_layout.addWidget(monto_input)
        row_layout.addWidget(btn_eliminar)

        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(row_widget)

        wrapper = QWidget()
        wrapper.setLayout(container)
        self.aportes_container.addWidget(wrapper)
        self.aportes_widgets.append((combo, monto_input, wrapper))

        def eliminar():
            wrapper.setParent(None)
            self.aportes_widgets[:] = [t for t in self.aportes_widgets if t[2] is not wrapper]
        btn_eliminar.clicked.connect(eliminar)

    def on_register(self):
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # Lista para los datos que se guardarán en la DB
        aportes_for_db = [] 
        # Lista para los datos que se pasarán al generador de recibos Excel
        aportes_for_recibo = [] 

        for combo, monto_input, _ in self.aportes_widgets:
            socio_selected = combo.currentData()
            raw_monto = parse_miles_colombian(monto_input.text())
            
            if not socio_selected or raw_monto <= 0:
                show_error(self, "", "Revisa que todos los aportes tengan socio y monto válido.")
                return
            
            # Es CRUCIAL obtener el saldo actual del socio ANTES de aplicar el aporte.
            socio_data_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
            if not socio_data_full:
                show_error(self, "", f"No se encontraron datos completos para el socio ID: {socio_selected['id']}")
                return

            saldo_antes_aporte = socio_data_full['saldo'] 
            
            aportes_for_db.append((socio_data_full['id'], raw_monto))
            # Para el recibo, necesitamos: (socio_data_dict, monto_aporte_int, saldo_socio_antes, saldo_socio_despues)
            aportes_for_recibo.append((
                socio_data_full, 
                raw_monto, 
                saldo_antes_aporte, 
                saldo_antes_aporte + raw_monto # Nuevo saldo para mostrar en el recibo
            ))

        if not aportes_for_db:
            show_warning(self, "", "Debes agregar al menos un aporte.")
            return
        
        # Validar si se excede el límite de 10 aportes para el template
        if len(aportes_for_db) > 10:
            show_warning(self, "", "No se pueden registrar más de 10 aportes en un solo recibo. Por favor, genere un segundo recibo si es necesario.")
            return


        try:
            cursor = self.db.conn.cursor()
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid
            fecha_actual_db_format = date.today().strftime("%Y-%m-%d")

            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")
            saldo_admin = self.db.get_config_value_as_int("total_admin") # Si se necesita para algo
            
            # Recorrer los aportes para actualizar la DB y el log
            for socio_id, monto_aporte_db in aportes_for_db:
                cursor.execute("""
                    INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                    VALUES (?, 'aporte', ?, ?)""", (recibo_id, socio_id, monto_aporte_db))

                cursor.execute("UPDATE socios SET saldo = saldo + ? WHERE id = ?", (monto_aporte_db, socio_id))

                saldo_caja += monto_aporte_db # Acumular el saldo en caja

                socio_info_for_log = next((s for s in self.socios_data if s["id"] == socio_id), None)
                nombre_socio_log = f"{socio_info_for_log['nombres']} {socio_info_for_log['apellidos']}" if socio_info_for_log else "Desconocido"

                self.db.add_to_auxiliar(
                    fecha=fecha_actual_db_format,
                    tipo="Aporte",
                    socio=nombre_socio_log,
                    numero=recibo_id,
                    monto=monto_aporte_db,
                    saldo=saldo_caja
                )

                if self.assistant_page:
                    self.assistant_page.add_operation({
                        "fecha": fecha_actual_db_format,
                        "tipo": "Aporte",
                        "socio": nombre_socio_log,
                        "numero": recibo_id,
                        "monto": monto_aporte_db,
                        "saldo": saldo_caja
                    })
            
            # Finalmente, actualizar el saldo en caja en la configuración global
            self.db.set_config_value("saldo_en_caja", str(saldo_caja))
            gastos_admin = 3000 * len(aportes_for_recibo)
            self.db.set_config_value("total_admin", str(saldo_admin + gastos_admin))

            self.db.conn.commit()

            # Obtener los gastos de administración.

            # Llamar a la función generar_recibo_solo_aportes para crear el recibo Excel
            # YA NO SE PASA pagos_credito_info
            recibo_path = generar_recibo_solo_aportes(
                db_manager=self.db, # Pasamos la instancia de DBManager
                recibo_id=recibo_id,
                recibi_de_data=recibi, # Dict completo del socio que recibe
                aportes_info=aportes_for_recibo, # La lista ya preparada
            )
            
            if recibo_path:
                show_success(self, "", f"Recibo #{recibo_id} creado y saldos actualizados.", file_path=recibo_path)
                self.operation_registered.emit()  # 🎯 Emit after success
            else:
                show_warning(self, "", "Recibo creado y saldos actualizados, pero hubo un error al generar el archivo Excel.")
            
            self.clear_form() # Limpia el formulario y recarga socios
            self.load_socios() # Asegura que los saldos de los socios en los combos se actualicen

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "", f"Error al registrar aporte:\n{e}")
            import traceback
            traceback.print_exc() # Para depuración


    def refresh(self):
        # Este método ahora puede simplemente llamar a load_socios
        # que ya se encarga de actualizar los combos existentes
        self.load_socios()
        # Y también limpiar el formulario si es necesario
        self.clear_form()

    def get_socio_recibi_de(self):
        return self.combo_recibi_de.currentData()

    def get_aportes(self):
        # Esta función no es usada directamente por on_register, pero si la necesitas en otro lado
        return [
            (combo.currentData(), parse_miles_colombian(input.text()))
            for combo, input, _ in self.aportes_widgets
        ]

    def clear_form(self):
        for _, _, wrapper in self.aportes_widgets:
            wrapper.setParent(None) # Elimina los widgets del layout
        self.aportes_widgets.clear() # Vacía la lista
        # self.load_socios() # Ya se llama después de generar el recibo, o al inicio del formulario