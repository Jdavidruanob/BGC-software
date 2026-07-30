from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt

from config import format_miles_colombian_int


class _NumericItem(QTableWidgetItem):
    """Ítem de tabla que ordena por un valor numérico (no por texto)."""

    def __init__(self, text, value):
        super().__init__(text)
        self._value = value
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def __lt__(self, other):
        try:
            return self._value < other._value
        except AttributeError:
            return super().__lt__(other)


class UtilidadesDialog(QDialog):
    """Muestra la utilidad calculada por socio para el año fiscal en curso.

    Solo despliega el resultado (nombre, saldo de aportes, utilidad); no
    exporta a Excel todavía, eso queda para una plantilla futura.
    """

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Utilidades de socios — Año {data['anio']}")
        self.setModal(True)
        self.setMinimumSize(560, 600)

        def money(x):
            return f"${format_miles_colombian_int(x)}"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"Utilidades de socios — Año {data['anio']}")
        titulo.setStyleSheet("font-size:18px;font-weight:bold;color:#111827;")
        layout.addWidget(titulo)

        formula = QLabel(
            f"Factor = (Intereses {money(data['intereses'])} − "
            f"Salarios {money(data['salarios'])}) / "
            f"Total aportes {money(data['total_aportes'])} = "
            f"<b>{data['factor']}</b>"
        )
        formula.setWordWrap(True)
        formula.setStyleSheet("font-size:13px;color:#374151;")
        layout.addWidget(formula)

        table = QTableWidget(len(data["detalle"]), 3)
        table.setHorizontalHeaderLabels(["Socio", "Saldo de aportes", "Utilidad"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        total_utilidad = 0
        for row, d in enumerate(data["detalle"]):
            total_utilidad += d["utilidad"]

            nombre_item = QTableWidgetItem(d["socio"])
            nombre_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(row, 0, nombre_item)

            saldo_item = _NumericItem(money(d["saldo"]), d["saldo"])
            saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 1, saldo_item)

            utilidad_item = _NumericItem(money(d["utilidad"]), d["utilidad"])
            utilidad_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 2, utilidad_item)

        layout.addWidget(table, 1)

        total = QLabel(f"Total utilidades repartidas: {money(total_utilidad)}")
        total.setStyleSheet("font-size:14px;font-weight:bold;color:#111827;")
        layout.addWidget(total)

        botones = QHBoxLayout()
        botones.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.clicked.connect(self.accept)
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)
