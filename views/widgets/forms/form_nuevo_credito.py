from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox, QSizePolicy, QSpacerItem, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal
from datetime import date, timedelta
import os
from datetime import date
from dateutil.relativedelta import relativedelta

from config import load_styles, load_svg_icon, parse_miles_colombian, format_miles_colombian_int, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning
from views.liquidation_page import CreditLiquidationPage
from utils.credit_liquidation_generator import generar_liquidacion_credito
from config import HOY, HOY_STR 

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita scroll accidental

class FormNuevoCredito(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, window, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.main_window = window
        self.socios_data = []
        self.socios_seleccionados = []

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 0, 20, 30)
        layout.setSpacing(24)

        # Combo de socios
        self.combo_socios = NoScrollComboBox()
        self.combo_socios.setObjectName("ComboSocio")
        self.combo_socios.setMinimumHeight(50)
        self.combo_socios.setMaximumHeight(50)
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
        self.selected_container.setAlignment(Qt.AlignLeft)
        self.selected_container.addStretch()  # <-- Espaciador que empuja los tags a la izquierda

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
        self.capital_input.textChanged.connect(lambda _: self.actualizar_resumen_credito())

        # Cuotas
        self.cuotas_input = QLineEdit()
        self.cuotas_input.setPlaceholderText("Número de cuotas")
        self.cuotas_input.setAlignment(Qt.AlignRight)
        self.cuotas_input.setFixedHeight(36)
        self.cuotas_input.textChanged.connect(lambda _: self.actualizar_resumen_credito())

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

        # Tarjeta de Cuota Mensual Estimada
        self.card_cuota = QFrame()
        self.card_cuota.setObjectName("CardCuotaMensual")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 5, 20, 5)
        card_layout.setSpacing(12)

        # Título
        titulo_cuota = QLabel("CUOTA MENSUAL ESTIMADA")
        titulo_cuota.setObjectName("TituloCuotaMensual")

        # Monto grande
        self.label_monto_cuota = QLabel("$0")
        self.label_monto_cuota.setObjectName("MontoCuotaMensual")

        # Fila de fecha
        fecha_row = QHBoxLayout()
        fecha_row.setSpacing(12)
        
        label_fecha_texto = QLabel("Fecha Finalización")
        label_fecha_texto.setObjectName("LabelFechaFinalizacion")
        
        self.label_fecha_finalizacion = QLabel("---")
        self.label_fecha_finalizacion.setObjectName("FechaFinalizacionValor")

        fecha_row.addWidget(label_fecha_texto)
        fecha_row.addWidget(self.label_fecha_finalizacion)
        fecha_row.addStretch()

        card_layout.addWidget(titulo_cuota)
        card_layout.addWidget(self.label_monto_cuota)
        card_layout.addLayout(fecha_row)
        self.card_cuota.setLayout(card_layout)

        layout.addWidget(self.card_cuota)

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
            STYLES_DIR, "forms", "form_nuevo_credito.qss"
        )
        load_styles(self, qss_path)

    def _etiqueta(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        return lbl

    def actualizar_resumen_credito(self):
        try:
            capital = parse_miles_colombian(self.capital_input.text())
            cuotas = int(self.cuotas_input.text())
            if capital <= 0 or cuotas <= 0:
                self.label_monto_cuota.setText("$0")
                self.label_fecha_finalizacion.setText("---")
                return

            # Calcular cuota base tentativa
            for redondeo in [10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]:
                posible_cuota = round((capital / cuotas) / redondeo) * redondeo
                total_normales = posible_cuota * (cuotas - 1)
                ultima_cuota = capital - total_normales
                if 10000 <= ultima_cuota <= posible_cuota * 1.5:
                    cuota_base = posible_cuota
                    break
            else:
                cuota_base = capital // cuotas

            fecha_inicio = HOY
            fecha_final = fecha_inicio + relativedelta(months=+cuotas) # <-- Esto es lo que necesitas

            self.label_monto_cuota.setText(f"${format_miles_colombian_int(cuota_base)}")
            self.label_fecha_finalizacion.setText(fecha_final.strftime("%Y-%m-%d"))

        except:
            self.label_monto_cuota.setText("$0")
            self.label_fecha_finalizacion.setText("---")

    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socios.blockSignals(True)
            self.combo_socios.clear()
            self.combo_socios.addItem("-- Selecciona un socio --", userData=None)  # 👈 opción vacía
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_socios.addItem(nombre, userData=socio)
            self.combo_socios.setCurrentIndex(0)
            self.combo_socios.blockSignals(False)
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

        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)
        wrapper.setObjectName("tag-socio")
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Icono del usuario
        icon_btn = QPushButton("")
        icon_btn.setFixedSize(21, 21)  
        icon_btn.setIcon(load_svg_icon("icons/xs.svg"))
        icon_btn.setObjectName("user-btn")

        label = QLabel(f"{socio['nombres']} {socio['apellidos']}")
        label.setObjectName("tag-label-socio")

        btn = QPushButton("")
        btn.setFixedSize(22, 22)
        btn.setIcon(load_svg_icon("icons/x.svg"))
        btn.setObjectName("DeleteButton")

        def eliminar():
            wrapper.setParent(None)
            self.socios_seleccionados.remove(socio)
            self.combo_socios.setCurrentIndex(0)

        btn.clicked.connect(eliminar)
        layout.addWidget(icon_btn)  # <-- Icono a la izquierda
        layout.addWidget(label)
        layout.addWidget(btn)
        wrapper.setLayout(layout)
        self.selected_container.insertWidget(self.selected_container.count() - 1, wrapper)  # <-- Inserta antes del stretch


    def on_register_credito(self):
        try:
            if not self.socios_seleccionados:
                show_warning(self, "", "Debes seleccionar al menos un socio.")
                return

            # Validaciones de input
            try:
                capital = parse_miles_colombian(self.capital_input.text())
                interes_tasa = float(self.interes_input.text())
                n_cuotas = int(self.cuotas_input.text())
            except ValueError:
                show_error(self, "", "Datos inválidos. Verifique capital, interés y cuotas.")
                return

            if capital <= 0 or interes_tasa <= 0 or n_cuotas <= 0:
                show_error(self, "", "Revisa que todos los valores sean válidos y positivos.")
                return

            socio_ids = [s['id'] for s in self.socios_seleccionados]
            
            # --- LLAMADA MAESTRA AL DB MANAGER ---
            # Toda la lógica pesada ocurre aquí adentro
            letra, nuevo_saldo_caja = self.db.registrar_credito_completo(
                socio_ids, capital, interes_tasa, n_cuotas
            )
            
            if letra:
                # Actualizar UI auxiliar (solo visual)
                fecha_actual_str = HOY_STR
                nombres_str = ", ".join([f"{s['nombres']} {s['apellidos']}" for s in self.socios_seleccionados])

                self.db.add_to_auxiliar(
                    fecha=fecha_actual_str,
                    tipo="Nuevo Credito",
                    socio=nombres_str,
                    recibo=None,           # <--- CAMBIO: Nuevo crédito no suele tener recibo de caja
                        id_credito=letra,      # <--- CORRECTO: La letra va aquí
                        monto=-capital,
                        saldo=nuevo_saldo_caja,
                        cuota=None
                    )
                
                self.db.set_config_value("saldo_en_caja", str(nuevo_saldo_caja))
                self.db.conn.commit()

                # Generar Excel (Usando datos frescos de la BD)
                credit_data_from_db = self.db.get_credit_by_letra(letra) 
                
                generated_liq_path = generar_liquidacion_credito(
                    credit_data=credit_data_from_db,
                    socios_list=self.socios_seleccionados
                )
                
                # Crear vistas
                for id_socio in socio_ids:
                    liquidation_view = CreditLiquidationPage(
                        credit_data_from_db, 
                        member_id=id_socio, 
                        main_window=self.main_window, 
                        db_manager=self.db
                    )
                    self.main_window.add_view(f"liquidation_credit_{letra}_{id_socio}", liquidation_view)

                show_success(self, "", f"Crédito creado exitosamente. Letra: {letra}.", file_path=generated_liq_path)
                
                # Limpiar formulario
                self.capital_input.clear()
                self.interes_input.setText("0.01")
                self.cuotas_input.clear()
                self.socios_seleccionados.clear()
                while self.selected_container.count():
                    item = self.selected_container.takeAt(0)
                    if item.widget(): item.widget().deleteLater()
                self.load_socios()
                self.actualizar_resumen_credito()
                self.operation_registered.emit()

        except Exception as e:
            show_error(self, "Error BD", f"Error al registrar crédito:\n{e}")
            import traceback
            traceback.print_exc()


    def refresh(self):
        self.load_socios()  