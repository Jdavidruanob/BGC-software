from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian
from views.widgets.message_boxes import show_success, show_error, show_warning, show_info
import os

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormCombinado(QWidget):
    def __init__(self, db_manager):
        
        super().__init__()
        self.db = db_manager
        self.socios_data = []
        self.aportes_widgets = []
        #------
       # self.socios_data = []
        self.pagos_widgets = []
        
        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(40)
        self.combo_recibi_de.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)
        
        # APORTES
        # Sección dinámicos de aportes
        aporte_section_label = QLabel("Aportes a registrar:")
        aporte_section_label.setObjectName("FormLabel")
        main_layout.addWidget(aporte_section_label)

        self.aportes_container = QVBoxLayout()
        self.aportes_container.setSpacing(12)
        main_layout.addLayout(self.aportes_container)

        # Botón agregar nueva fila
        self.btn_agregar_aporte = QPushButton(" Agregar aporte")
        self.btn_agregar_aporte.setObjectName("AddAporteButton")
        self.btn_agregar_aporte.setIcon(load_svg_icon("assets/icons/plus.svg"))
        self.btn_agregar_aporte.setIconSize(QSize(20, 20))
        self.btn_agregar_aporte.clicked.connect(self.agregar_aporte)
        main_layout.addWidget(self.btn_agregar_aporte, alignment=Qt.AlignLeft)

        # PAGOS
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

        # Espacio y botón general para crear el recibo
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Crear Recibo")
        self.btn_registrar.setObjectName("createReceipt")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register_combinado)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial
        self.load_socios()
        # Estilos
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "styles", "forms", "form_combinado.qss"
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

    def agregar_aporte(self):
        """Agrega una fila con ComboSocio + MontoInput + DeleteButton."""
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
        btn_eliminar.setIcon(load_svg_icon("assets/icons/x.svg"))
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

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
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

    def on_register_combinado(self):
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        aportes = []
        for combo, monto_input, _ in self.aportes_widgets:
            socio = combo.currentData()
            monto = parse_miles_colombian(monto_input.text())
            if socio and monto > 0:
                aportes.append((socio['id'], monto))

        pagos = []
        cursor = self.db.conn.cursor()
        for combo, letras_container, _ in self.pagos_widgets:
            socio = combo.currentData()
            for i in range(letras_container.count()):
                w = letras_container.itemAt(i).widget()
                letra = w.findChild(NoScrollComboBox, "LetraCombo")
                cuotas_input = w.findChild(QLineEdit, "CuotasInput")
                if letra is None or cuotas_input is None:
                    continue
                letra_data = letra.currentData()
                try:
                    n = int(cuotas_input.text())
                except:
                    show_error(self, "", "Número de cuotas inválido.")
                    return
                if letra_data and n > 0:
                    cursor.execute(
                        "SELECT COUNT(*) FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL",
                        (letra_data['letra'],)
                    )
                    faltantes = cursor.fetchone()[0]
                    if n > faltantes:
                        show_error(self, "Error de cuotas",
                                   f"Sólo quedan {faltantes} cuotas pendientes para la letra {letra_data['letra']}.")
                        return
                    pagos.append((socio['id'], letra_data['letra'], n))

        if not aportes or not pagos:
            show_warning(self, "", "Debes agregar al menos un aporte y un pago.")
            return

        try:
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid 

            for socio_id, monto in aportes:
                cursor.execute("""
                    INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, monto)
                    VALUES (?, 'aporte', ?, ?)
                """, (recibo_id, socio_id, monto))
                cursor.execute("""
                    UPDATE socios SET saldo = saldo + ? WHERE id = ?
                """, (monto, socio_id))

            for socio_id, letra_id, n in pagos:
                cursor.execute("""
                    SELECT nro_cuota, valor_cuota, interes_mes FROM liquidaciones
                    WHERE credito_letra = ? AND fecha_pago IS NULL
                    ORDER BY nro_cuota LIMIT ?
                """, (letra_id, n))
                for fila in cursor.fetchall():
                    nro = fila['nro_cuota']
                    monto = fila['valor_cuota'] + fila['interes_mes']
                    cursor.execute("""
                        INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto)
                        VALUES (?, 'pago_credito', ?, ?, ?, ?)
                    """, (recibo_id, socio_id, letra_id, nro, monto))
                    cursor.execute("""
                        UPDATE liquidaciones SET fecha_pago = DATE('now')
                        WHERE credito_letra = ? AND nro_cuota = ?
                    """, (letra_id, nro))

            self.db.conn.commit()
            show_success(self, "", f"Recibo combinado #{recibo_id} creado exitosamente.")
            self.limpiar_formulario()
        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "", f"Error al crear recibo combinado:\n{e}")

    def limpiar_formulario(self):
        """Limpia todos los campos y reinicia el formulario."""
        self.combo_recibi_de.setCurrentIndex(-1)

        for _, _, widget in self.aportes_widgets:
            widget.setParent(None)
        self.aportes_widgets.clear()

        for _, _, widget in self.pagos_widgets:
            widget.setParent(None)
        self.pagos_widgets.clear()

        self.load_socios()
