import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QSpacerItem, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from config import (
    load_styles, load_svg_icon, format_miles_colombian_int, STYLES_DIR
)
from utils.message_boxes import show_success, show_error, show_warning
from views.widgets.comboBox_custom import SearchableComboBox


class FormDevolucionTotal(QWidget):
    """Devolución/retiro TOTAL: devuelve todo el saldo del socio y lo retira
    de la cooperativa. Operación definitiva (con confirmación reforzada)."""

    operation_registered = Signal()

    def __init__(self, service, db_manager):
        super().__init__()
        self.db = db_manager
        self._service = service
        self.socios_data = []

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 0, 20, 30)
        layout.setSpacing(20)

        lbl_titulo = QLabel("Socio a retirar (devolución total):")
        lbl_titulo.setObjectName("FormLabel")
        layout.addWidget(lbl_titulo)

        self.combo_socio = SearchableComboBox(placeholder_text="Escribe para buscar un socio…")
        self.combo_socio.setObjectName("ComboSocio")
        self.combo_socio.setMinimumHeight(50)
        self.combo_socio.setMaximumHeight(50)
        self.combo_socio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_socio.currentIndexChanged.connect(self.actualizar_preview)
        layout.addWidget(self.combo_socio)

        # Tarjeta con el saldo que se le devolverá.
        self.card_saldo = QFrame()
        self.card_saldo.setObjectName("CardSaldoDisponible")
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(16, 20, 16, 20)
        card_layout.setSpacing(16)

        icon_label = QLabel()
        icon_label.setPixmap(load_svg_icon("icons/credit-card.svg").pixmap(28, 28))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        titulo_saldo = QLabel("SE LE DEVOLVERÁ TODO SU SALDO")
        titulo_saldo.setObjectName("TituloSaldoDisponible")
        subtitulo_saldo = QLabel("El socio quedará retirado de la cooperativa")
        subtitulo_saldo.setObjectName("SubtituloSaldoDisponible")
        info_layout.addWidget(titulo_saldo)
        info_layout.addWidget(subtitulo_saldo)

        self.label_saldo = QLabel("$0")
        self.label_saldo.setObjectName("MontoSaldoDisponible")
        self.label_saldo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        card_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        card_layout.addLayout(info_layout, 1)
        card_layout.addWidget(self.label_saldo, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.card_saldo.setLayout(card_layout)
        layout.addWidget(self.card_saldo)

        layout.addSpacerItem(QSpacerItem(0, 40))

        self.btn_registrar = QPushButton("Registrar Devolución Total")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.clicked.connect(self.on_register)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        self.setLayout(layout)
        self.load_socios()

        qss_path = os.path.join(STYLES_DIR, "forms", "form_retiro.qss")
        load_styles(self, qss_path)

    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.blockSignals(True)
            self.combo_socio.populate_socios(self.socios_data)
            self.combo_socio.blockSignals(False)
            self.actualizar_preview()
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def actualizar_preview(self):
        socio = self.combo_socio.currentData()
        if socio:
            self.label_saldo.setText(f"$ {format_miles_colombian_int(socio['saldo'])}")
        else:
            self.label_saldo.setText("$0")

    def on_register(self):
        socio = self.combo_socio.currentData()
        if not socio:
            show_warning(self, "", "Debes seleccionar un socio.")
            return

        nombre = f"{socio['nombres']} {socio['apellidos']}"
        confirmar = show_warning(
            self,
            "",
            f"Vas a hacer la DEVOLUCIÓN TOTAL de {nombre}.<br><br>"
            f"Se le devolverán <b>$ {format_miles_colombian_int(socio['saldo'])}</b>, "
            "se descontará de la caja y el socio quedará <b>retirado</b> de la cooperativa "
            "(dejará de aparecer en la app y el bot).<br><br>"
            "Es una operación definitiva. ¿Continuar?",
            ask_confirmation=True,
        )
        if confirmar != QMessageBox.Yes:
            return

        try:
            recibo_id, excel_path, _ = self._service.register(socio["id"], socio)
            if excel_path:
                show_success(
                    self, "", f"Devolución total registrada. Recibo #{recibo_id}", file_path=excel_path
                )
            else:
                show_success(self, "", f"Devolución total registrada. Recibo #{recibo_id}")
            self.operation_registered.emit()
            self.refresh()
        except ValueError as e:
            show_error(self, "", str(e))
        except Exception as e:
            show_error(self, "", f"Error al registrar la devolución total:\n{e}")

    def refresh(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socio.blockSignals(True)
            self.combo_socio.populate_socios(self.socios_data)
            self.combo_socio.blockSignals(False)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")
        self.actualizar_preview()
