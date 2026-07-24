import os
from datetime import date

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QDate, QSize

from config import (
    load_styles, load_svg_icon, format_miles_colombian_int,
    parse_miles_colombian, STYLES_DIR,
)
from services.amortization import build_manual_schedule
from views.widgets.comboBox_custom import SearchableComboBox
from utils.message_boxes import show_error


class ManualCreditDialog(QDialog):
    """Crea un crédito manual/histórico a partir de una cuota dada.

    Pide socio(s), capital, número de cuotas, la cuota (parte de capital) y el
    interés. Muestra una vista previa de la liquidación y valida el invariante
    (la suma de las cuotas paga el capital completo) antes de permitir guardar.
    """

    def __init__(self, socios, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crédito manual (histórico)")
        self.setModal(True)
        self.setMinimumSize(720, 640)
        self.setObjectName("ManualCreditDialog")

        self._socios = socios
        self._seleccionados = []   # dicts de socio

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(14)

        titulo = QLabel("Crédito manual (histórico)")
        titulo.setObjectName("FormLabel")
        root.addWidget(titulo)

        ayuda = QLabel(
            "Para créditos que ya se hicieron a mano. En vez de calcular la cuota, "
            "se ingresa. La última cuota absorbe el residuo para que la suma pague "
            "el capital completo."
        )
        ayuda.setWordWrap(True)
        ayuda.setObjectName("HelpText")
        root.addWidget(ayuda)

        # --- Socios ---
        lbl_socios = QLabel("Socio(s):")
        lbl_socios.setObjectName("FormLabel")
        root.addWidget(lbl_socios)

        self.combo_socios = SearchableComboBox(placeholder_text="Escribe para buscar un socio…")
        self.combo_socios.setMinimumHeight(44)
        self.combo_socios.populate_socios(self._socios)
        self.combo_socios.selectionCommitted.connect(self._agregar_socio)
        root.addWidget(self.combo_socios)

        self.tags_container = QHBoxLayout()
        self.tags_container.setSpacing(8)
        tags_wrap = QWidget()
        tags_wrap.setLayout(self.tags_container)
        root.addWidget(tags_wrap)

        # --- Campos numéricos ---
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        self.input_capital = self._money_input("$ Capital prestado")
        self.input_cuotas = QLineEdit()
        self.input_cuotas.setObjectName("InputField")
        self.input_cuotas.setPlaceholderText("N° de cuotas")
        self.input_cuota = self._money_input("$ Cuota (parte de capital)")
        self.input_interes = QLineEdit()
        self.input_interes.setObjectName("InputField")
        self.input_interes.setPlaceholderText("Interés % mensual (ej: 2)")

        self.date_inicio = QDateEdit(calendarPopup=True)
        self.date_inicio.setObjectName("InputField")
        self.date_inicio.setDisplayFormat("yyyy-MM-dd")
        self.date_inicio.setDate(QDate.currentDate())

        # Altura mínima de respaldo (por si el QSS no carga) y columnas parejas
        # y anchas para que los inputs no queden angostos ni cortados.
        for w in (self.input_capital, self.input_cuotas, self.input_cuota,
                  self.input_interes, self.date_inicio):
            w.setMinimumHeight(42)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        grid.addWidget(QLabel("Capital:"), 0, 0)
        grid.addWidget(self.input_capital, 1, 0)
        grid.addWidget(QLabel("N° de cuotas:"), 0, 1)
        grid.addWidget(self.input_cuotas, 1, 1)
        grid.addWidget(QLabel("Cuota (capital):"), 2, 0)
        grid.addWidget(self.input_cuota, 3, 0)
        grid.addWidget(QLabel("Interés % mensual:"), 2, 1)
        grid.addWidget(self.input_interes, 3, 1)
        grid.addWidget(QLabel("Fecha de inicio:"), 4, 0)
        grid.addWidget(self.date_inicio, 5, 0)
        root.addLayout(grid)

        for w in (self.input_cuotas, self.input_interes):
            w.textChanged.connect(self._actualizar_preview)
        self.input_capital.textChanged.connect(self._actualizar_preview)
        self.input_cuota.textChanged.connect(self._actualizar_preview)
        self.date_inicio.dateChanged.connect(self._actualizar_preview)

        # --- Vista previa ---
        lbl_prev = QLabel("Vista previa de la liquidación:")
        lbl_prev.setObjectName("FormLabel")
        root.addWidget(lbl_prev)

        self.preview = QTableWidget(0, 5)
        self.preview.setObjectName("previewTable")
        self.preview.setHorizontalHeaderLabels(
            ["Cuota", "Capital", "Interés", "Total", "Saldo"]
        )
        self.preview.verticalHeader().setVisible(False)
        self.preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview.setSelectionMode(QAbstractItemView.NoSelection)
        self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview.setMinimumHeight(180)
        root.addWidget(self.preview)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setObjectName("HelpText")
        self.lbl_estado.setWordWrap(True)
        root.addWidget(self.lbl_estado)

        # --- Botones ---
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("CancelButton")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        self.btn_guardar = QPushButton("Crear crédito")
        self.btn_guardar.setObjectName("CreateMemberButton")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self._on_guardar)
        btns.addWidget(cancel)
        btns.addWidget(self.btn_guardar)
        root.addLayout(btns)

        qss_path = os.path.join(STYLES_DIR, "new_member_dialog.qss")
        load_styles(self, qss_path)
        self._actualizar_preview()

    # ------------------------------------------------------------------ helpers
    def _money_input(self, placeholder):
        e = QLineEdit()
        e.setObjectName("InputField")
        e.setPlaceholderText(placeholder)
        e.setAlignment(Qt.AlignRight)

        def _fmt(text):
            raw = parse_miles_colombian(text)
            formatted = format_miles_colombian_int(raw)
            if formatted != text:
                e.blockSignals(True)
                e.setText(formatted)
                e.setCursorPosition(len(formatted))
                e.blockSignals(False)
        e.textChanged.connect(_fmt)
        return e

    def _agregar_socio(self):
        socio = self.combo_socios.currentData()
        if not socio or any(s["id"] == socio["id"] for s in self._seleccionados):
            self.combo_socios.setCurrentIndex(-1)
            return
        self._seleccionados.append(socio)
        self._mostrar_tag(socio)
        self.combo_socios.setCurrentIndex(-1)
        self._actualizar_preview()

    def _mostrar_tag(self, socio):
        tag = QFrame()
        tag.setObjectName("tag-socio")
        lay = QHBoxLayout(tag)
        lay.setContentsMargins(8, 2, 8, 2)
        lay.setSpacing(6)
        lay.addWidget(QLabel(f"{socio['nombres']} {socio['apellidos']}"))
        btn = QPushButton()
        btn.setIcon(load_svg_icon("icons/x.svg"))
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.PointingHandCursor)

        def _quitar():
            tag.setParent(None)
            self._seleccionados = [s for s in self._seleccionados if s["id"] != socio["id"]]
            self._actualizar_preview()
        btn.clicked.connect(_quitar)
        lay.addWidget(btn)
        self.tags_container.addWidget(tag)

    def _leer_valores(self):
        capital = parse_miles_colombian(self.input_capital.text())
        cuota = parse_miles_colombian(self.input_cuota.text())
        try:
            n_cuotas = int(self.input_cuotas.text().strip() or 0)
        except ValueError:
            n_cuotas = 0
        try:
            interes = float(self.input_interes.text().strip() or 0) / 100.0
        except ValueError:
            interes = 0.0
        fecha = self.date_inicio.date().toPython()
        return capital, cuota, n_cuotas, interes, fecha

    def _actualizar_preview(self):
        capital, cuota, n_cuotas, interes, fecha = self._leer_valores()
        self.preview.setRowCount(0)
        problemas = []
        if not self._seleccionados:
            problemas.append("Selecciona al menos un socio.")
        if capital <= 0:
            problemas.append("Ingresa el capital.")
        if n_cuotas < 1:
            problemas.append("Ingresa el número de cuotas.")
        if cuota <= 0:
            problemas.append("Ingresa la cuota.")
        if n_cuotas >= 1 and cuota > 0 and capital > 0 and cuota * (n_cuotas - 1) > capital:
            problemas.append("La cuota es demasiado alta: la última quedaría negativa.")

        if problemas:
            self.lbl_estado.setText("• " + "\n• ".join(problemas))
            self.btn_guardar.setEnabled(False)
            return

        filas = build_manual_schedule(0, capital, interes, n_cuotas, cuota, fecha)
        self.preview.setRowCount(len(filas))
        for r, f in enumerate(filas):
            valores = [
                str(f[1]),
                f"${format_miles_colombian_int(f[3])}",
                f"${format_miles_colombian_int(f[4])}",
                f"${format_miles_colombian_int(f[5])}",
                f"${format_miles_colombian_int(f[6])}",
            ]
            for c, v in enumerate(valores):
                it = QTableWidgetItem(v)
                it.setTextAlignment(Qt.AlignCenter)
                self.preview.setItem(r, c, it)

        ultima = capital - cuota * (n_cuotas - 1)
        suma = cuota * (n_cuotas - 1) + ultima
        self.lbl_estado.setText(
            f"✔ Suma de capital = ${format_miles_colombian_int(suma)} "
            f"(coincide con el capital). Última cuota: ${format_miles_colombian_int(ultima)}."
        )
        self.btn_guardar.setEnabled(True)

    def _on_guardar(self):
        if not self._seleccionados:
            show_error(self, "Falta socio", "Selecciona al menos un socio.")
            return
        self.accept()

    def get_data(self):
        capital, cuota, n_cuotas, interes, fecha = self._leer_valores()
        return {
            "socio_ids": [s["id"] for s in self._seleccionados],
            "capital": capital,
            "interes": interes,
            "n_cuotas": n_cuotas,
            "cuota_inicial": cuota,
            "fecha_inicio": fecha,
        }
