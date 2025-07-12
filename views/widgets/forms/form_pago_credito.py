from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt

from config import format_miles_colombian_int, parse_miles_colombian
from views.widgets.message_boxes import show_error, show_success, show_warning, show_info


class FormPagoCredito(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.socios_data = [] 
        self.pagos_widgets = []  # [(combo, letras_container, wrapper)]

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        # Título
        title = QLabel("💸 Registro de Pago de Crédito")
        title.setObjectName("formTitle")
        layout.addWidget(title)

        # "Recibí de"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = QComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumWidth(300)
        layout.addWidget(lbl_recibi)
        layout.addWidget(self.combo_recibi_de)

        # Sección de pagos dinámicos
        pagos_label = QLabel("Pagos a registrar:")
        pagos_label.setObjectName("FormLabel")
        layout.addWidget(pagos_label)

        self.pagos_container = QVBoxLayout()
        layout.addLayout(self.pagos_container)

        # Botón para agregar socio que pagará
        btn_agregar_pago = QPushButton("➕ Agregar pago de socio")
        btn_agregar_pago.setObjectName("AddPagoButton")
        btn_agregar_pago.clicked.connect(self.agregar_pago)
        layout.addWidget(btn_agregar_pago, alignment=Qt.AlignLeft)

        # Botón registrar
        layout.addStretch()
        btn_registrar = QPushButton("Registrar Pago")
        btn_registrar.setObjectName("RegisterButton")
        btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_registrar.clicked.connect(self.on_register)
        layout.addWidget(btn_registrar, alignment=Qt.AlignHCenter)

        # Cargar datos
        self.load_socios()

    def load_socios(self):
        if not self.db:
            return
        self.socios_data = self.db.get_all_members_full()
        self.combo_recibi_de.clear()
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']} (Saldo: {format_miles_colombian_int(socio['saldo'])})"
            self.combo_recibi_de.addItem(nombre, userData=socio)

    def agregar_pago(self):
        combo = QComboBox()
        combo.setObjectName("ComboSocioPago")
        combo.setMinimumWidth(250)
        for socio in self.socios_data:
            nombre = f"{socio['nombres']} {socio['apellidos']} (Saldo: {format_miles_colombian_int(socio['saldo'])})"
            combo.addItem(nombre, userData=socio)

        btn_add_letra = QPushButton("Agregar letra a pagar")
        btn_add_letra.setObjectName("AddLetraButton")

        letras_container = QVBoxLayout()
        letras_container.setSpacing(6)

        def agregar_letra():
            letra_row_widget = QWidget()
            letra_row = QHBoxLayout(letra_row_widget)
            letra_row.setContentsMargins(0, 0, 0, 0)

            letra_combo = QComboBox()
            letra_combo.setObjectName("LetraCombo")

            socio = combo.currentData()
            if socio and self.db:
                letras = self.db.get_letras_by_socio_id(socio['id'])
                if not letras:
                    show_info(self, "Sin créditos", "Este socio no tiene créditos activos.")
                    return
                for letra in letras:
                    texto = (
                        f"Letra: {letra['letra']} | "
                        f"Capital: ${format_miles_colombian_int(letra['capital'])} | "
                        f"Cuotas: {letra['no_cuotas']} | "
                        f"Interés: {letra['interes'] * 100:.2f}%"
                    )
                    letra_combo.addItem(texto, userData=letra)

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setFixedWidth(80)
            cuotas_input.setAlignment(Qt.AlignRight)

            btn_delete_letra = QPushButton("❌")
            btn_delete_letra.setFixedSize(26, 26)
            btn_delete_letra.setToolTip("Eliminar esta letra")

            btn_delete_letra.clicked.connect(lambda: (
                letras_container.removeWidget(letra_row_widget),
                letra_row_widget.setParent(None)
            ))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        btn_delete_pago = QPushButton("❌")
        btn_delete_pago.setFixedSize(26, 26)
        btn_delete_pago.setToolTip("Eliminar este pago")

        socio_row = QHBoxLayout()
        socio_row.setContentsMargins(0, 0, 0, 0)
        socio_row.addWidget(combo)
        socio_row.addWidget(btn_add_letra)
        socio_row.addWidget(btn_delete_pago)

        wrapper = QVBoxLayout()
        wrapper.addLayout(socio_row)
        wrapper.addLayout(letras_container)

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper)
        self.pagos_container.addWidget(wrapper_widget)

        btn_delete_pago.clicked.connect(lambda: (
            wrapper_widget.setParent(None),
            self.pagos_widgets.remove((combo, letras_container, wrapper_widget))
        ))

        self.pagos_widgets.append((combo, letras_container, wrapper_widget))

    def on_register(self):
        # 1) Validar "Recibí de"
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # 2) Extraer pagos
        pagos = []  # [(socio_id, letra_id, n_cuotas)]
        for combo, letras_container, _ in self.pagos_widgets:
            socio_pago = combo.currentData()
            for i in range(letras_container.count()):
                widget = letras_container.itemAt(i).widget()
                letra = widget.findChild(QComboBox, "LetraCombo").currentData()
                try:
                    n = int(widget.findChild(QLineEdit, "CuotasInput").text())
                except ValueError:
                    show_error(self, "", "Cuotas inválidas.")
                    return
                pagos.append((socio_pago['id'], letra['letra'], n))

        if not pagos:
            show_warning(self, "", "Agrega al menos un pago.")
            return

        cursor = self.db.conn.cursor()
        # 3) Validar cuotas pendientes
        for _, letra_id, n in pagos:
            cursor.execute(
                "SELECT COUNT(*) FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL",
                (letra_id,)
            )
            faltantes = cursor.fetchone()[0]
            if n > faltantes:
                show_error(self, "Error de cuotas",
                           f"Sólo quedan {faltantes} cuotas pendientes para la letra {letra_id}.")
                return

        # 4) Crear recibo
        cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
        recibo_id = cursor.lastrowid

        # 5) Registrar detalle y marcar pagos
        for socio_id, letra_id, n in pagos:
            cursor.execute(
                "SELECT nro_cuota, valor_cuota, interes_mes FROM liquidaciones "
                "WHERE credito_letra = ? AND fecha_pago IS NULL "
                "ORDER BY nro_cuota LIMIT ?", (letra_id, n)
            )
            filas = cursor.fetchall()
            for fila in filas:
                nro = fila['nro_cuota']
                monto = fila['valor_cuota'] + fila['interes_mes']
                cursor.execute(
                    "INSERT INTO detalle_recibo "
                    "(recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto) "
                    "VALUES (?, 'pago_credito', ?, ?, ?, ?)",
                    (recibo_id, socio_id, letra_id, nro, monto)
                )
                cursor.execute(
                    "UPDATE liquidaciones SET fecha_pago = DATE('now') "
                    "WHERE credito_letra = ? AND nro_cuota = ?",
                    (letra_id, nro)
                )

        self.db.conn.commit()
        show_success(self, "", f"Pago registrado en recibo #{recibo_id}")

        # 6) Limpiar formulario
        for _, _, wrapper in self.pagos_widgets:
            wrapper.setParent(None)
        self.pagos_widgets.clear()
        self.load_socios()
