from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox, QSizePolicy, QSpacerItem, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QSize
from datetime import date, timedelta
import os
from datetime import date
from dateutil.relativedelta import relativedelta

from config import load_styles, load_svg_icon, parse_miles_colombian, format_miles_colombian_int, BASE_APP_DIR
from utils.message_boxes import show_success, show_error, show_warning
from views.liquidation_page import CreditLiquidationPage
from utils.credit_liquidation_generator import generar_liquidacion_credito

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita scroll accidental

class FormNuevoCredito(QWidget):
    def __init__(self, db_manager, window, assistant_page=None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.main_window = window
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

        # Resumen dinámico
        resumen_row = QHBoxLayout()
        resumen_row.setSpacing(24)

        self.label_cuota = QLabel()
        self.label_cuota.setStyleSheet("font-size: 15px;")

        self.label_fecha_final = QLabel()
        self.label_fecha_final.setStyleSheet("font-size: 15px;")

        resumen_row.addWidget(self._etiqueta("Cuota estimada:"))
        resumen_row.addWidget(self.label_cuota)
        resumen_row.addSpacing(40)
        resumen_row.addWidget(self._etiqueta("Último pago:"))
        resumen_row.addWidget(self.label_fecha_final)

        layout.addLayout(resumen_row)
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
            BASE_APP_DIR, "styles", "forms", "form_nuevo_credito.qss"
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
                self.label_cuota.setText("")
                self.label_fecha_final.setText("")
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

            fecha_inicio = date.today() # O la fecha de inicio real del crédito si es diferente
            fecha_final = fecha_inicio + relativedelta(months=+cuotas) # <-- Esto es lo que necesitas

            self.label_cuota.setText(f"${format_miles_colombian_int(cuota_base)}")
            self.label_fecha_final.setText(fecha_final.strftime("%Y-%m-%d"))

        except:
            self.label_cuota.setText("")
            self.label_fecha_final.setText("")

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
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)
        wrapper.setStyleSheet("background-color: #f1f5f9; border-radius: 12px;")

        label = QLabel(f"{socio['nombres']} {socio['apellidos']}")
        label.setStyleSheet("font-size: 14px;")

        btn = QPushButton("")
        btn.setFixedSize(22, 22)
        btn.setIcon(load_svg_icon("icons/x.svg"))
        btn.setStyleSheet("border: none; background: transparent;")

        def eliminar():
            wrapper.setParent(None)
            self.socios_seleccionados.remove(socio)
            self.combo_socios.setCurrentIndex(0)  # 👈 Permite volver a seleccionarlo

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
            
            # La función add_credit guarda el crédito y devuelve la letra
            letra = self.db.add_credit(socio_ids, capital, interes, cuotas)
            
            # Obtener los datos completos del crédito recién creado para pasarlos al generador
            credit_data_from_db = self.db.get_credit_by_letra(letra) 

            if letra:
                # Actualizar saldo caja global
                saldo_actual = self.db.get_config_value_as_int("saldo_en_caja")
                nuevo_saldo = saldo_actual - capital
                self.db.set_config_value("saldo_en_caja", str(nuevo_saldo))

                fecha_actual = date.today().strftime("%Y-%m-%d")
                nombres = ", ".join([f"{s['nombres']} {s['apellidos']}" for s in self.socios_seleccionados])

                self.db.add_to_auxiliar(
                    fecha=fecha_actual,
                    tipo="Nuevo Credito",
                    socio=nombres,
                    # Si `numero` en auxiliar es el ID del recibo del crédito, y `letra` es tu `id_credito` TEXT,
                    # deberías tener un `recibo_id_credito_nuevo` o similar para `numero`.
                    # Por ahora, dado que `numero` es INTEGER NOT NULL y antes pasabas `letra` (que es tu ID de crédito),
                    # y si `letra` *realmente* puede ser un entero, se mantiene.
                    # Si `letra` es TEXT (ej. "CR001"), entonces `numero` en auxiliar debería ser NULL o un ID numérico de recibo.
                    # POR AHORA, ASUMIMOS QUE LA `letra` GENERADA POR `add_credit` ES NUMÉRICA Y PUEDE IR EN `numero` (como antes)
                    # Y TAMBIÉN SE VA A `id_credito` PARA EL NUEVO FILTRO.
                    numero=letra, # Si 'letra' es numérica, puede ir aquí. Si es alfanumérica, necesitas un número de recibo aquí.
                    monto=-capital,
                    saldo=nuevo_saldo,
                    cuota=None, # Los nuevos créditos no tienen 'cuota' individual
                    id_credito=letra # <-- ¡Aquí es donde realmente quieres la letra!
                )

                # Agregar visual en AssistantPage
                if self.assistant_page:
                    self.assistant_page.add_operation({
                        "fecha": fecha_actual,
                        "tipo": "Nuevo Credito",
                        "socio": nombres,
                        "numero": letra, # Y aquí también para la visualización consistente
                        "cuota": None,
                        "monto": -capital,
                        "saldo": nuevo_saldo,
                        "id_credito": letra # <-- ¡Y aquí también para la visualización y filtro en AssistantPage!
                    })

                # --- Generar el archivo de liquidación Excel ---
                generated_liq_path = generar_liquidacion_credito(
                    credit_data=credit_data_from_db,
                    socios_list=self.socios_seleccionados # Pasamos la lista de diccionarios de socios
                )
                
                # Crear la vista de liquidación en la UI (esto ya lo tienes)
                for id_socio in socio_ids: # Iterar por cada socio para la vista
                    liquidation_view = CreditLiquidationPage(
                        credit_data_from_db, 
                        member_id=id_socio, 
                        main_window=self.main_window, 
                        db_manager=self.db
                    )
                    view_name = f"liquidation_credit_{letra}_{id_socio}" # Un nombre único por socio si lo necesitas
                    self.main_window.add_view(view_name, liquidation_view)

                show_success(self, "", f"Crédito creado exitosamente. Letra: {letra}.", file_path= generated_liq_path)

                # Limpiar el formulario
                self.capital_input.clear()
                self.interes_input.setText("0.01")
                self.cuotas_input.clear()
                self.socios_seleccionados.clear()
                while self.selected_container.count():
                    item = self.selected_container.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                self.load_socios() # Recargar socios y resetear el combo
                self.actualizar_resumen_credito() # Limpiar el resumen

        except Exception as e:
            show_error(self, "", f"Error al crear crédito:\n{e}")
            import traceback
            traceback.print_exc() # Para ver el error completo en la consola

    def refresh(self):
        """Refresca el formulario: limpia inputs, recarga socios y borra etiquetas previas."""
        self.load_socios()  # Recarga lista de socios

