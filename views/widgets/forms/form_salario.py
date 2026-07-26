import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from config import (
    STYLES_DIR, format_miles_colombian_int, get_hoy, load_styles, load_svg_icon,
)
from utils.message_boxes import show_error, show_success, show_warning
from utils.recibo_generator_salario import MESES, nombre_mes


class FormSalario(QWidget):
    """Pago del salario del administrador.

    Solo pide el valor y el mes: no hay socio que elegir, porque el dinero sale
    de la caja hacia el administrador. Propone el último salario pagado, que es
    el caso habitual (se repite mes a mes y solo cambia cuando sube el mínimo).
    """

    operation_registered = Signal()

    def __init__(self, service, db_manager):
        super().__init__()
        self.db = db_manager
        self._service = service

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 0, 20, 30)
        layout.setSpacing(20)

        # --- Mes al que corresponde ---
        lbl_mes = QLabel("Mes que se está pagando:")
        lbl_mes.setObjectName("FormLabel")
        layout.addWidget(lbl_mes)

        self.combo_mes = QComboBox()
        self.combo_mes.setObjectName("ComboSocio")
        self.combo_mes.setMinimumHeight(50)
        self.combo_mes.setMaximumHeight(50)
        self.combo_mes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_mes.addItems(MESES)
        layout.addWidget(self.combo_mes)

        # --- Valor ---
        lbl_valor = QLabel("Valor del salario:")
        lbl_valor.setObjectName("FormLabel")
        layout.addWidget(lbl_valor)

        self.input_valor = QLineEdit()
        self.input_valor.setObjectName("MontoInput")
        self.input_valor.setPlaceholderText("Ej: 1.423.500")
        self.input_valor.setMinimumHeight(50)
        self.input_valor.setAlignment(Qt.AlignRight)
        self.input_valor.textChanged.connect(self._formatear_valor)
        layout.addWidget(self.input_valor)

        # --- Tarjeta con el acumulado del año ---
        self.card_total = QFrame()
        self.card_total.setObjectName("CardSaldoDisponible")
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(16, 20, 16, 20)
        card_layout.setSpacing(16)

        icon_label = QLabel()
        icon_label.setPixmap(load_svg_icon("icons/cash.svg").pixmap(28, 28))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        titulo = QLabel("SALARIOS PAGADOS (ACUMULADO)")
        titulo.setObjectName("TituloSaldoDisponible")
        self.subtitulo = QLabel("Sale de la caja")
        self.subtitulo.setObjectName("SubtituloSaldoDisponible")
        info_layout.addWidget(titulo)
        info_layout.addWidget(self.subtitulo)

        self.label_total = QLabel("$0")
        self.label_total.setObjectName("MontoSaldoDisponible")
        self.label_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        card_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        card_layout.addLayout(info_layout, 1)
        card_layout.addWidget(self.label_total, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.card_total.setLayout(card_layout)
        layout.addWidget(self.card_total)

        layout.addSpacerItem(QSpacerItem(0, 30))

        self.btn_registrar = QPushButton("Registrar Pago de Salario")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.clicked.connect(self.on_register)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

        qss_path = os.path.join(STYLES_DIR, "forms", "form_retiro.qss")
        load_styles(self, qss_path)

        self.refresh()

    # ------------------------------------------------------------------ helpers
    def _formatear_valor(self, texto):
        """Muestra el monto con separador de miles mientras se escribe."""
        solo_digitos = "".join(c for c in texto if c.isdigit())
        formateado = format_miles_colombian_int(int(solo_digitos)) if solo_digitos else ""
        if formateado != texto:
            self.input_valor.blockSignals(True)
            self.input_valor.setText(formateado)
            self.input_valor.setCursorPosition(len(formateado))
            self.input_valor.blockSignals(False)

    def _valor_actual(self) -> int:
        solo_digitos = "".join(c for c in self.input_valor.text() if c.isdigit())
        return int(solo_digitos) if solo_digitos else 0

    # ------------------------------------------------------------------ acciones
    def on_register(self):
        monto = self._valor_actual()
        if monto <= 0:
            show_warning(self, "", "Escribe el valor del salario.")
            return

        mes = self.combo_mes.currentText()
        confirmar = show_warning(
            self,
            "",
            f"Vas a registrar el pago del salario de <b>{mes}</b> por "
            f"<b>$ {format_miles_colombian_int(monto)}</b>.<br><br>"
            "Ese dinero <b>se descuenta de la caja</b> y se suma al acumulado "
            "de salarios del año.<br><br>¿Continuar?",
            ask_confirmation=True,
        )
        if confirmar != QMessageBox.Yes:
            return

        try:
            recibo_id, excel_path, _ = self._service.register(monto, mes)
            mensaje = f"Salario de {mes} registrado. Recibo #{recibo_id}"
            if excel_path:
                show_success(self, "", mensaje, file_path=excel_path)
            else:
                show_success(self, "", mensaje)
            self.operation_registered.emit()
            self.refresh()
        except ValueError as e:
            show_error(self, "", str(e))
        except Exception as e:
            show_error(self, "", f"Error al registrar el salario:\n{e}")

    def refresh(self):
        try:
            self.combo_mes.setCurrentText(nombre_mes(get_hoy()))
            total = self._service.get_total_salarios()
            self.label_total.setText(f"$ {format_miles_colombian_int(total)}")
            ultimo = self._service.get_ultimo_salario()
            if ultimo:
                self.input_valor.setText(format_miles_colombian_int(ultimo))
        except Exception as e:
            print(f"❌ Error refrescando el formulario de salario: {e}")
