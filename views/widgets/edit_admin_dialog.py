import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QScrollArea, QWidget, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from config import load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR

# Tamaño preferido del diálogo (un poco más grande que antes). Es solo el
# preferido: _ajustar_tamano() lo recorta si no cabe en la pantalla, así la
# ventana nunca queda más alta/ancha que el espacio disponible ni oculta el
# botón de cerrar.
ANCHO_PREFERIDO = 520
ALTO_PREFERIDO = 700

class EditAdminDialog(QDialog):
    def __init__(self, current_papeleria, current_mora_pct,
                 current_next_recibo=1, current_next_letra=1, parent=None,
                 current_fondo_mora=0):
        super().__init__(parent)
        self.setWindowTitle("Configurar Administración")
        self.setModal(True)
        self.setMinimumWidth(470)
        self.setObjectName("NewMemberDialog")  # Reutilizamos el estilo base

        self._orig_recibo = int(current_next_recibo)
        self._orig_letra = int(current_next_letra)
        self._orig_papeleria = current_papeleria
        self._orig_fondo_mora = current_fondo_mora
        self._papeleria_ingreso = True
        self._mora_ingreso = True

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        # --- AJUSTE: FONDO DE PAPELERÍA ---
        # En vez de editar el total directo (lo que obligaba a restar a mano
        # antes de escribir el resultado), se suma o resta un monto sobre el
        # valor actual.
        self.input_ajuste_papeleria = QLineEdit()
        self.btn_papeleria_ingreso, self.btn_papeleria_egreso = self._build_ajuste_block(
            layout,
            titulo="Fondo Acumulado Papelería",
            valor_actual=current_papeleria,
            input_widget=self.input_ajuste_papeleria,
            on_toggle=self._toggle_papeleria,
        )

        # --- AJUSTE: FONDO ACUMULADO DE MORA ---
        self.input_ajuste_mora = QLineEdit()
        self.btn_mora_ingreso, self.btn_mora_egreso = self._build_ajuste_block(
            layout,
            titulo="Fondo Acumulado Mora",
            valor_actual=current_fondo_mora,
            input_widget=self.input_ajuste_mora,
            on_toggle=self._toggle_mora,
        )

        # --- PORCENTAJE DE MORA (tasa, no un fondo: se sigue editando directo) ---
        lbl_mora = QLabel("Porcentaje Interés Mora (0.01 - 1.0):")
        lbl_mora.setObjectName("FormLabel")
        layout.addWidget(lbl_mora)

        self.input_mora = QLineEdit()
        self.input_mora.setObjectName("InputField")
        self.input_mora.setAlignment(Qt.AlignRight)
        self.input_mora.setText(str(current_mora_pct))
        self.input_mora.setPlaceholderText("Ej: 0.02")
        self.input_mora.setToolTip(
            "Se cobra automático por cada cuota vencida, con 5 días de gracia\n"
            "desde el vencimiento. Se multiplica por los meses de atraso."
        )
        layout.addWidget(self.input_mora)

        lbl_mora_nota = QLabel(
            "El sistema cobra esta mora automático (5 días de gracia, luego se "
            "multiplica por los meses de atraso). Puede desmarcarse por letra al "
            "registrar un pago, o por cuota en la liquidación."
        )
        lbl_mora_nota.setObjectName("HelpText")
        lbl_mora_nota.setWordWrap(True)
        layout.addWidget(lbl_mora_nota)

        # --- PRÓXIMO NÚMERO DE RECIBO ---
        lbl_recibo = QLabel("Número del próximo recibo:")
        lbl_recibo.setObjectName("FormLabel")
        layout.addWidget(lbl_recibo)

        self.input_next_recibo = QLineEdit()
        self.input_next_recibo.setObjectName("InputField")
        self.input_next_recibo.setAlignment(Qt.AlignRight)
        self.input_next_recibo.setValidator(QIntValidator(1, 99999999, self))
        self.input_next_recibo.setText(str(current_next_recibo))
        layout.addWidget(self.input_next_recibo)

        # --- PRÓXIMA LETRA (CRÉDITO) ---
        lbl_letra = QLabel("Número de la próxima letra (crédito):")
        lbl_letra.setObjectName("FormLabel")
        layout.addWidget(lbl_letra)

        self.input_next_letra = QLineEdit()
        self.input_next_letra.setObjectName("InputField")
        self.input_next_letra.setAlignment(Qt.AlignRight)
        self.input_next_letra.setValidator(QIntValidator(1, 99999999, self))
        self.input_next_letra.setText(str(current_next_letra))
        layout.addWidget(self.input_next_letra)

        nota = QLabel("Al cambiar estos números, el sistema sigue automático desde ahí.")
        nota.setWordWrap(True)
        nota.setObjectName("HelpText")
        layout.addWidget(nota)

        layout.addStretch()

        # --- BOTÓN GUARDAR ---
        btn_save = QPushButton("Guardar Cambios")
        btn_save.setObjectName("CreateMemberButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save, alignment=Qt.AlignCenter)

        # El formulario va dentro de un scroll: si en una pantalla pequeña no
        # cabe todo el contenido a la vez, se puede bajar con la rueda en vez
        # de que la ventana se estire más allá de la pantalla (eso dejaba la
        # barra de título, con la X de cerrar, fuera del área visible).
        content = QWidget()
        content.setLayout(layout)
        scroll = QScrollArea()
        scroll.setObjectName("AdminDialogScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea#AdminDialogScroll{background:transparent;border:none;}")
        scroll.setWidget(content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        # Cargamos el estilo compartido
        qss_path = os.path.join(STYLES_DIR, "new_member_dialog.qss")
        load_styles(self, qss_path)

        self._ajustar_tamano()

    def _ajustar_tamano(self):
        """Tamaño preferido, recortado para que SIEMPRE quepa en la pantalla
        (con margen para la barra de título) y centrado en ella."""
        pantalla = self.screen() or QApplication.primaryScreen()
        disponible = pantalla.availableGeometry()
        margen = 60
        ancho = min(ANCHO_PREFERIDO, disponible.width() - margen)
        alto = min(ALTO_PREFERIDO, disponible.height() - margen)
        self.resize(ancho, alto)
        x = disponible.x() + (disponible.width() - ancho) // 2
        y = disponible.y() + (disponible.height() - alto) // 2
        self.move(x, y)

    def _build_ajuste_block(self, layout, titulo, valor_actual, input_widget, on_toggle):
        """Arma una fila de ajuste: título con el valor actual, toggle
        Sumar/Restar y monto. No pide motivo ni afecta caja (a diferencia del
        ajuste de saldo en caja): esto solo corrige el fondo acumulado."""
        lbl = QLabel(f"{titulo}  (actual: $ {format_miles_colombian_int(valor_actual)})")
        lbl.setObjectName("FormLabel")
        layout.addWidget(lbl)

        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)

        btn_ingreso = QPushButton("▲ Sumar")
        btn_ingreso.setCursor(Qt.PointingHandCursor)
        btn_ingreso.setProperty("mode", "ingreso")
        btn_ingreso.setProperty("active", True)
        btn_ingreso.setProperty("class", "modeButton")
        btn_ingreso.clicked.connect(lambda: on_toggle(True))

        btn_egreso = QPushButton("▼ Restar")
        btn_egreso.setCursor(Qt.PointingHandCursor)
        btn_egreso.setProperty("mode", "egreso")
        btn_egreso.setProperty("active", False)
        btn_egreso.setProperty("class", "modeButton")
        btn_egreso.clicked.connect(lambda: on_toggle(False))

        type_layout.addWidget(btn_ingreso)
        type_layout.addWidget(btn_egreso)
        layout.addLayout(type_layout)

        input_widget.setObjectName("InputField")
        input_widget.setAlignment(Qt.AlignRight)
        input_widget.setPlaceholderText("$ 0 (déjalo vacío para no ajustar)")
        input_widget.textChanged.connect(
            lambda text: self._on_monto_ajuste_changed(input_widget, text)
        )
        layout.addWidget(input_widget)

        return btn_ingreso, btn_egreso

    def _on_monto_ajuste_changed(self, input_widget, text):
        """Formato de miles en tiempo real para un input de ajuste."""
        if not text:
            return
        raw = parse_miles_colombian(text)
        formatted = format_miles_colombian_int(raw)
        if formatted != text:
            input_widget.blockSignals(True)
            input_widget.setText(formatted)
            input_widget.setCursorPosition(len(formatted))
            input_widget.blockSignals(False)

    def _toggle_papeleria(self, is_ingreso):
        self._papeleria_ingreso = is_ingreso
        self._refresh_toggle(self.btn_papeleria_ingreso, self.btn_papeleria_egreso, is_ingreso)

    def _toggle_mora(self, is_ingreso):
        self._mora_ingreso = is_ingreso
        self._refresh_toggle(self.btn_mora_ingreso, self.btn_mora_egreso, is_ingreso)

    def _refresh_toggle(self, btn_ingreso, btn_egreso, is_ingreso):
        btn_ingreso.setProperty("active", is_ingreso)
        btn_egreso.setProperty("active", not is_ingreso)
        for btn in (btn_ingreso, btn_egreso):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def get_data(self):
        """Retorna (papeleria, mora_pct, next_recibo, next_letra, fondo_mora):
        papelería y fondo_mora ya son el valor actual +/- el ajuste digitado."""
        ajuste_papeleria = parse_miles_colombian(self.input_ajuste_papeleria.text())
        if not self._papeleria_ingreso:
            ajuste_papeleria = -ajuste_papeleria
        papeleria = self._orig_papeleria + ajuste_papeleria

        ajuste_mora = parse_miles_colombian(self.input_ajuste_mora.text())
        if not self._mora_ingreso:
            ajuste_mora = -ajuste_mora
        fondo_mora = self._orig_fondo_mora + ajuste_mora

        try:
            mora = float(self.input_mora.text().replace(',', '.'))
        except ValueError:
            mora = 0.02 # Valor por defecto si fallan

        try:
            next_recibo = int(self.input_next_recibo.text().strip() or self._orig_recibo)
        except ValueError:
            next_recibo = self._orig_recibo
        try:
            next_letra = int(self.input_next_letra.text().strip() or self._orig_letra)
        except ValueError:
            next_letra = self._orig_letra

        return papeleria, mora, next_recibo, next_letra, fondo_mora
