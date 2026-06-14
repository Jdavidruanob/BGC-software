# views/forms/form_pago_credito.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal

from config import(
     load_styles, load_svg_icon, format_miles_colombian_int, 
     parse_miles_colombian, get_hoy_str, get_hoy, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
)
from utils.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from collections import defaultdict 


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormPagoCredito(QWidget):
    operation_registered = Signal()
    def __init__(self, service, db_manager, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.pagos_widgets = []  # [(combo_socio, letras_container, wrapper_widget)]
        self._service = service

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 0, 20, 30)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)


        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(50)
        self.combo_recibi_de.setMaximumHeight(50)
        self.combo_recibi_de.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)

        # Sección dinámicos de pagos
        pagos_label = QLabel("Pagos a registrar:")
        pagos_label.setObjectName("FormLabel")
        main_layout.addWidget(pagos_label)

        self.pagos_container = QVBoxLayout()
        self.pagos_container.setSpacing(12)
        main_layout.addLayout(self.pagos_container)

        # Botón para agregar socio que pagará
        self.btn_agregar_pago = QPushButton(" Agregar pago de socio")
        self.btn_agregar_pago.setObjectName("AddPagoButton")
        self.btn_agregar_pago.setIcon(load_svg_icon("icons/plus.svg"))
        self.btn_agregar_pago.setIconSize(QSize(20, 20))
        self.btn_agregar_pago.setMinimumHeight(36)
        self.btn_agregar_pago.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_agregar_pago.clicked.connect(self.agregar_pago)
        main_layout.addWidget(self.btn_agregar_pago, alignment=Qt.AlignLeft)

        # Espacio y botón registrar
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Registrar Pago")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial
        self.load_socios()

        # Aplica estilos
        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_pago_credito.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        """Carga lista de socios para combo_recibi_de."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_recibi_de.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_pago(self):
        """Agrega bloque para un socio + sus letras a pagar."""
        # Combo socio
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocioPago")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            combo.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)

        # Botón agregar letra
        btn_add_letra = QPushButton(" Agregar letra a pagar")
        btn_add_letra.setObjectName("AddLetraButton")
        btn_add_letra.setIcon(load_svg_icon("icons/plus.svg"))
        btn_add_letra.setIconSize(QSize(16, 16))
        btn_add_letra.setMinimumHeight(36)
        btn_add_letra.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Contenedor dinámico de letras
        letras_container = QVBoxLayout()
        letras_container.setSpacing(8)

        def agregar_letra():
            letra_row = QHBoxLayout()
            letra_row.setContentsMargins(0,0,0,0)

            letra_combo = NoScrollComboBox()
            letra_combo.setObjectName("LetraCombo")
            letra_combo.setMinimumHeight(34)
            letra_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            socio = combo.currentData()
            if socio:
                letras = self.db.get_letras_by_socio_id(socio['id'])
                if not letras:
                    show_info(self, "Sin créditos", "Este socio no tiene letras activas.")
                    return
                for l in letras:
                    texto = (
                        f"Letra {l['letra']}  ·  "
                        f"${format_miles_colombian_int(l['capital'])}  ·  "
                        f"{l['no_cuotas']} cuotas"
                    )
                    letra_combo.addItem(texto, userData=l)

            # --- INPUT ABONO CAPITAL (Nuevo con formato en tiempo real) ---
            abono_input = QLineEdit()
            abono_input.setObjectName("AbonoInput")
            abono_input.setPlaceholderText("$ Abono capital")
            abono_input.setAlignment(Qt.AlignRight)
            abono_input.setFixedHeight(34)
            abono_input.setFixedWidth(140) 

            def on_abono_changed(text):
                # Usamos las funciones de config.py para limpiar y formatear
                raw = parse_miles_colombian(text)
                formatted = format_miles_colombian_int(raw)
                if formatted != text:
                    abono_input.blockSignals(True)
                    abono_input.setText(formatted)
                    # Mantenemos el cursor al final para que no salte al inicio
                    abono_input.setCursorPosition(len(formatted))
                    abono_input.blockSignals(False)

            abono_input.textChanged.connect(on_abono_changed)       

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setAlignment(Qt.AlignRight)
            cuotas_input.setFixedHeight(34)
            cuotas_input.setFixedWidth(90)

            btn_delete_letra = QPushButton("")
            btn_delete_letra.setObjectName("DeleteLetraButton")
            btn_delete_letra.setIcon(load_svg_icon("icons/x.svg"))
            btn_delete_letra.setIconSize(QSize(16,16))  
            btn_delete_letra.setFixedSize(25,25)
            btn_delete_letra.setToolTip("Eliminar esta letra")
            btn_delete_letra.clicked.connect(lambda: letra_row_widget.setParent(None))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(abono_input) # <--- AGREGAMOS EL INPUT AQUÍ
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letra_row_widget = QWidget()
            letra_row_widget.setLayout(letra_row)
            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        # Botón eliminar todo el pago
        btn_delete_pago = QPushButton("")
        btn_delete_pago.setObjectName("DeletePagoButton")
        btn_delete_pago.setIcon(load_svg_icon("icons/x.svg"))
        btn_delete_pago.setIconSize(QSize(20,20))
        btn_delete_pago.setFixedSize(28,28)
        btn_delete_pago.setToolTip("Eliminar este pago")

        # Layout socio + acciones
        socio_row = QHBoxLayout()
        socio_row.setContentsMargins(0,0,0,0)
        socio_row.addWidget(combo)
        socio_row.addWidget(btn_add_letra)
        socio_row.addWidget(btn_delete_pago)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.addLayout(socio_row)
        wrapper_layout.addLayout(letras_container)

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper_layout)
        self.pagos_container.addWidget(wrapper_widget)

        # Conecta eliminación
        btn_delete_pago.clicked.connect(lambda: wrapper_widget.setParent(None))
        

    def on_register(self):
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        pagos_input = []
        for i in range(self.pagos_container.count()):
            wrapper = self.pagos_container.itemAt(i).widget()
            if not wrapper:
                continue
            combo = wrapper.findChild(NoScrollComboBox, "ComboSocioPago")
            wrapper_layout = wrapper.layout()
            if wrapper_layout.count() <= 1:
                continue
            letras_container = wrapper_layout.itemAt(1)
            socio_selected = combo.currentData()
            if not socio_selected:
                continue
            socio_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
            for j in range(letras_container.count()):
                w = letras_container.itemAt(j).widget()
                letra_selected = w.findChild(NoScrollComboBox, "LetraCombo").currentData()
                if not letra_selected:
                    continue
                abono_text = w.findChild(QLineEdit, "AbonoInput").text()
                cuotas_text = w.findChild(QLineEdit, "CuotasInput").text()
                dinero_abono = parse_miles_colombian(abono_text) if abono_text else 0
                try:
                    n_cuotas = int(cuotas_text) if cuotas_text else 0
                except:
                    n_cuotas = 0
                if dinero_abono == 0 and n_cuotas == 0:
                    continue
                pagos_input.append({
                    "socio_data": socio_full,
                    "letra_id": letra_selected['letra'],
                    "n_cuotas": n_cuotas,
                    "abono_capital": dinero_abono,
                })

        if not pagos_input:
            show_warning(self, "", "Agrega al menos un pago.")
            return

        try:
            recibo_id, excel_path, reporte_global = self._service.register(
                recibi['id'], recibi, pagos_input
            )
            if reporte_global:
                msg_final = ""
                for nombre, acciones in reporte_global.items():
                    msg_final += f"<b>{nombre}</b><br>"
                    for accion in acciones:
                        msg_final += f"&nbsp;&nbsp;• {accion}<br>"
                    msg_final += "<br>"
                show_info(self, "Resumen de Transacción", msg_final)
            if excel_path:
                show_success(self, "Pago Registrado", f"Recibo #{recibo_id} generado.", file_path=excel_path)
            self.operation_registered.emit()
            self.clear_form()
        except ValueError as e:
            show_error(self, "", str(e))
        except Exception as e:
            show_error(self, "Error", f"Error crítico: {e}")
            import traceback
            traceback.print_exc()

    def refresh(self):
        """Recarga la lista de socios y actualiza los combos existentes."""
        self.load_socios()
        # Actualizar combos de socios existentes
        for combo, letras_container, _ in self.pagos_widgets:
            socio_actual = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                combo.addItem(nombre, userData=socio)
            # Reestablecer selección si era válida
            if socio_actual:
                for i in range(combo.count()):
                    if combo.itemData(i)['id'] == socio_actual['id']:
                        combo.setCurrentIndex(i)
                        break
            combo.blockSignals(False)

    def clear_form(self):
        """Limpia el formulario y recarga los socios."""
        # Elimina todos los widgets de pago dinámicos
        for i in reversed(range(self.pagos_container.count())):
            widget = self.pagos_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Vacía la lista de widgets de pago
        self.pagos_widgets.clear()
        
        # Recarga los socios
        self.load_socios()