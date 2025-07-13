from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian
from views.widgets.message_boxes import show_success, show_error, show_warning, show_info
import os
class FormPagoCredito(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.socios_data = []
        self.pagos_widgets = []  # [(combo_socio, letras_container, wrapper_widget)]

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)


        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = QComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(40)
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
        self.btn_agregar_pago.setIcon(load_svg_icon("assets/icons/plus.svg"))
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
            os.path.dirname(__file__),
            "..", "..", "..", "styles", "forms", "form_pago_credito.qss"
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
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_pago(self):
        """Agrega bloque para un socio + sus letras a pagar."""
        # Combo socio
        combo = QComboBox()
        combo.setObjectName("ComboSocioPago")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            combo.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)

        # Botón agregar letra
        btn_add_letra = QPushButton(" Agregar letra a pagar")
        btn_add_letra.setObjectName("AddLetraButton")
        btn_add_letra.setIcon(load_svg_icon("assets/icons/plus.svg"))
        btn_add_letra.setIconSize(QSize(16, 16))
        btn_add_letra.setMinimumHeight(36)
        btn_add_letra.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Contenedor dinámico de letras
        letras_container = QVBoxLayout()
        letras_container.setSpacing(8)

        def agregar_letra():
            letra_row = QHBoxLayout()
            letra_row.setContentsMargins(0,0,0,0)

            letra_combo = QComboBox()
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

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setAlignment(Qt.AlignRight)
            cuotas_input.setFixedHeight(34)
            cuotas_input.setFixedWidth(80)

            btn_delete_letra = QPushButton("")
            btn_delete_letra.setObjectName("DeleteLetraButton")
            btn_delete_letra.setIcon(load_svg_icon("assets/icons/x.svg"))
            btn_delete_letra.setIconSize(QSize(16,16))
            btn_delete_letra.setFixedSize(28,28)
            btn_delete_letra.setToolTip("Eliminar esta letra")
            btn_delete_letra.clicked.connect(lambda: letra_row_widget.setParent(None))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letra_row_widget = QWidget()
            letra_row_widget.setLayout(letra_row)
            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        # Botón eliminar todo el pago
        btn_delete_pago = QPushButton("")
        btn_delete_pago.setObjectName("DeletePagoButton")
        btn_delete_pago.setIcon(load_svg_icon("assets/icons/x.svg"))
        btn_delete_pago.setIconSize(QSize(20,20))
        btn_delete_pago.setFixedSize(30,30)
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

        self.pagos_widgets.append((combo, letras_container, wrapper_widget))

    def on_register(self):
        """Valida y registra el pago en la BD."""
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        pagos = []
        for combo, letras_container, _ in self.pagos_widgets:
            socio = combo.currentData()
            for i in range(letras_container.count()):
                w = letras_container.itemAt(i).widget()
                letra = w.findChild(QComboBox, "LetraCombo").currentData()
                try:
                    n = int(w.findChild(QLineEdit, "CuotasInput").text())
                except:
                    show_error(self, "", "Número de cuotas inválido.")
                    return
                pagos.append((socio['id'], letra['letra'], n))

        if not pagos:
            show_warning(self, "", "Agrega al menos un pago.")
            return

        cursor = self.db.conn.cursor()
        # Aquí tu lógica de validación y registro...
        self.db.conn.commit()
        show_success(self, "", "Pago registrado correctamente.")
        for _,_,w in self.pagos_widgets:
            w.setParent(None)
        self.pagos_widgets.clear()
        self.load_socios()
