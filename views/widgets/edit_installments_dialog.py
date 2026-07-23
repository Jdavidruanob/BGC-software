import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QWidget
)
from PySide6.QtCore import Qt

from config import (
    load_styles, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR,
)
from services.amortization import rebalance_schedule


class EditInstallmentsDialog(QDialog):
    """Edita el valor (capital) de una o varias cuotas y reajusta las demás.

    El usuario marca "Fijar" en las cuotas que quiere dejar en un valor concreto;
    el capital pendiente restante se reparte entre las cuotas libres (la última
    absorbe el residuo). Las cuotas pagadas no se tocan. Se valida en vivo que la
    suma siga cuadrando con el capital antes de permitir guardar.
    """

    COL_FIJAR, COL_NRO, COL_CAPITAL, COL_INTERES, COL_TOTAL, COL_SALDO, COL_ESTADO = range(7)

    def __init__(self, capital, interes, cuotas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar cuotas (reajuste)")
        self.setModal(True)
        self.setMinimumSize(760, 560)
        self.setObjectName("EditInstallmentsDialog")

        self._capital = capital
        self._interes = interes
        # Modelo: lista ordenada de dicts {nro_cuota, valor_cuota, pagada}
        self._cuotas = [
            {"nro_cuota": c["nro_cuota"], "valor_cuota": c["valor_cuota"],
             "pagada": c.get("pagada", c.get("fecha_pago") is not None)}
            for c in cuotas
        ]
        self._rows = {}  # nro_cuota -> {"chk":QCheckBox, "cap":QLineEdit}

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(12)

        titulo = QLabel("Editar cuotas y reajustar el resto")
        titulo.setObjectName("FormLabel")
        root.addWidget(titulo)

        ayuda = QLabel(
            "Marca “Fijar” en la(s) cuota(s) que quieras dejar en un valor exacto "
            "y escribe el nuevo capital. Las demás cuotas pendientes se reparten "
            "solas para que el crédito siga cuadrando. Las cuotas ya pagadas no se tocan."
        )
        ayuda.setWordWrap(True)
        ayuda.setObjectName("HelpText")
        root.addWidget(ayuda)

        self.table = QTableWidget(len(self._cuotas), 7)
        self.table.setObjectName("editInstallmentsTable")
        self.table.setHorizontalHeaderLabels(
            ["Fijar", "Cuota", "Capital", "Interés", "Total", "Saldo", "Estado"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(self.COL_FIJAR, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(self.COL_NRO, QHeaderView.ResizeToContents)
        root.addWidget(self.table)

        self._build_rows()

        self.lbl_estado = QLabel("")
        self.lbl_estado.setObjectName("HelpText")
        self.lbl_estado.setWordWrap(True)
        root.addWidget(self.lbl_estado)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("CancelButton")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        self.btn_guardar = QPushButton("Guardar reajuste")
        self.btn_guardar.setObjectName("CreateMemberButton")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(self.btn_guardar)
        root.addLayout(btns)

        qss_path = os.path.join(STYLES_DIR, "new_member_dialog.qss")
        load_styles(self, qss_path)

        self._recompute()

    def _build_rows(self):
        for row, c in enumerate(self._cuotas):
            nro = c["nro_cuota"]
            pagada = c["pagada"]

            # Fijar (solo cuotas pendientes)
            if not pagada:
                chk = QCheckBox()
                chk.setCursor(Qt.PointingHandCursor)
                chk.stateChanged.connect(lambda _s, n=nro: self._on_fijar_changed(n))
                cont = QWidget()
                lay = QHBoxLayout(cont)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.setAlignment(Qt.AlignCenter)
                lay.addWidget(chk)
                self.table.setCellWidget(row, self.COL_FIJAR, cont)
            else:
                chk = None

            it_nro = QTableWidgetItem(str(nro))
            it_nro.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_NRO, it_nro)

            # Capital editable (deshabilitado hasta marcar Fijar)
            cap = QLineEdit(format_miles_colombian_int(c["valor_cuota"]))
            cap.setAlignment(Qt.AlignRight)
            cap.setEnabled(False)
            if not pagada:
                cap.textEdited.connect(lambda _t, n=nro: self._on_capital_edited(n))
                self._rows[nro] = {"chk": chk, "cap": cap}
            self.table.setCellWidget(row, self.COL_CAPITAL, cap)

            for col in (self.COL_INTERES, self.COL_TOTAL, self.COL_SALDO):
                it = QTableWidgetItem("")
                it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, it)

            estado = QTableWidgetItem("Pagada" if pagada else "Pendiente")
            estado.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_ESTADO, estado)

    def _on_fijar_changed(self, nro):
        r = self._rows[nro]
        r["cap"].setEnabled(r["chk"].isChecked())
        self._recompute()

    def _on_capital_edited(self, nro):
        cap = self._rows[nro]["cap"]
        raw = parse_miles_colombian(cap.text())
        formatted = format_miles_colombian_int(raw)
        if formatted != cap.text():
            cap.blockSignals(True)
            cap.setText(formatted)
            cap.setCursorPosition(len(formatted))
            cap.blockSignals(False)
        self._recompute()

    def get_overrides(self):
        overrides = {}
        for nro, r in self._rows.items():
            if r["chk"] is not None and r["chk"].isChecked():
                overrides[nro] = parse_miles_colombian(r["cap"].text())
        return overrides

    def _recompute(self):
        overrides = self.get_overrides()
        try:
            updates = rebalance_schedule(self._capital, self._interes, self._cuotas, overrides)
        except ValueError as e:
            self.lbl_estado.setText(f"⚠ {e}")
            self.btn_guardar.setEnabled(False)
            return

        by_nro = {u["nro_cuota"]: u for u in updates}
        for row, c in enumerate(self._cuotas):
            nro = c["nro_cuota"]
            if nro not in by_nro:
                continue  # pagada: se deja como está
            u = by_nro[nro]
            # Actualizar el capital de las cuotas libres (no fijadas)
            r = self._rows.get(nro)
            if r and not (r["chk"] is not None and r["chk"].isChecked()):
                r["cap"].blockSignals(True)
                r["cap"].setText(format_miles_colombian_int(u["valor_cuota"]))
                r["cap"].blockSignals(False)
            self.table.item(row, self.COL_INTERES).setText(f"${format_miles_colombian_int(u['interes_mes'])}")
            self.table.item(row, self.COL_TOTAL).setText(f"${format_miles_colombian_int(u['cuota_mensual'])}")
            self.table.item(row, self.COL_SALDO).setText(f"${format_miles_colombian_int(u['saldo_capital'])}")

        self.lbl_estado.setText(
            f"✔ La suma de las cuotas cuadra con el capital "
            f"(${format_miles_colombian_int(self._capital)})."
        )
        self.btn_guardar.setEnabled(True)
