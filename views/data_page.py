import os

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont

from config import load_styles, format_miles_colombian_int, STYLES_DIR, PRIMARY_COLOR

VERDE = "#2E7D32"
ROJO = "#D32F2F"
AMBAR = "#F9A825"

MESES = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
}


def _mes_label(yyyymm):
    try:
        y, m = yyyymm.split("-")
        return f"{MESES.get(m, m)} {y[2:]}"
    except Exception:
        return yyyymm


class _BarChart(QWidget):
    """Gráfico de barras simple (recaudo por mes), dibujado con QPainter."""

    def __init__(self, data, color=PRIMARY_COLOR, parent=None):
        super().__init__(parent)
        self._data = data  # lista de (label, value)
        self._color = color
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self._data:
            p.setPen(QColor("#888"))
            p.drawText(self.rect(), Qt.AlignCenter, "Sin datos de recaudo aún")
            return

        max_v = max((v for _, v in self._data), default=1) or 1
        pad_x, top, base_y = 16, 24, h - 34
        n = len(self._data)
        slot = (w - 2 * pad_x) / n
        bar_w = min(slot * 0.55, 90)

        p.setFont(QFont("", 8))
        for i, (label, val) in enumerate(self._data):
            cx = pad_x + i * slot + slot / 2
            bh = (base_y - top) * (val / max_v)
            x = cx - bar_w / 2
            p.fillRect(int(x), int(base_y - bh), int(bar_w), int(bh), QColor(self._color))
            p.setPen(QColor("#333"))
            p.drawText(int(cx - slot / 2), int(base_y + 6), int(slot), 16,
                       Qt.AlignCenter, label)
            p.setPen(QColor("#555"))
            p.drawText(int(cx - slot / 2), int(base_y - bh - 18), int(slot), 16,
                       Qt.AlignCenter, f"${format_miles_colombian_int(val)}")
        p.setPen(QColor("#DDD"))
        p.drawLine(pad_x, base_y, w - pad_x, base_y)


class _GroupedBarChart(QWidget):
    """Barras agrupadas para comparar dos series por mes (ej. Aportes vs Intereses)."""

    def __init__(self, labels, series, parent=None):
        # labels: lista de etiquetas de mes.
        # series: lista de dicts {"name": str, "color": str, "values": [int,...]}.
        super().__init__(parent)
        self._labels = labels
        self._series = series
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self._labels:
            p.setPen(QColor("#888"))
            p.drawText(self.rect(), Qt.AlignCenter, "Sin datos aún")
            return

        all_vals = [v for s in self._series for v in s["values"]]
        max_v = max(all_vals, default=1) or 1
        pad_x, top, base_y = 24, 40, h - 34
        n = len(self._labels)
        slot = (w - 2 * pad_x) / n
        ns = max(len(self._series), 1)
        group_w = min(slot * 0.7, 90)
        bar_w = group_w / ns

        # Leyenda (arriba).
        p.setFont(QFont("", 9))
        lx = pad_x
        for s in self._series:
            p.fillRect(lx, 12, 12, 12, QColor(s["color"]))
            p.setPen(QColor("#374151"))
            p.drawText(lx + 16, 22, s["name"])
            lx += 16 + p.fontMetrics().horizontalAdvance(s["name"]) + 24

        p.setFont(QFont("", 8))
        for i, label in enumerate(self._labels):
            cx = pad_x + i * slot + slot / 2
            for j, s in enumerate(self._series):
                val = s["values"][i]
                bh = (base_y - top) * (val / max_v)
                x = cx - group_w / 2 + j * bar_w
                p.fillRect(int(x), int(base_y - bh), int(max(bar_w - 2, 1)), int(bh),
                           QColor(s["color"]))
            p.setPen(QColor("#333"))
            p.drawText(int(cx - slot / 2), int(base_y + 6), int(slot), 16,
                       Qt.AlignCenter, label)
        p.setPen(QColor("#DDD"))
        p.drawLine(pad_x, base_y, w - pad_x, base_y)


class _HBarChart(QWidget):
    """Barras horizontales para ranking por socio (Top N)."""

    def __init__(self, data, color=PRIMARY_COLOR, parent=None):
        super().__init__(parent)
        self._data = data  # lista de (label, value)
        self._color = color
        self.setMinimumHeight(max(160, 30 * len(data) + 16))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self._data:
            p.setPen(QColor("#888"))
            p.drawText(self.rect(), Qt.AlignCenter, "Sin datos aún")
            return

        max_v = max((v for _, v in self._data), default=1) or 1
        n = len(self._data)
        pad = 8
        row_h = (h - 2 * pad) / n
        bar_h = min(row_h * 0.6, 22)
        label_w = 160
        bar_x = label_w + 8
        val_w = 96
        bar_max_w = max(w - bar_x - val_w, 10)

        p.setFont(QFont("", 9))
        for i, (label, val) in enumerate(self._data):
            cy = pad + i * row_h + row_h / 2
            name = label if len(label) <= 24 else label[:23] + "…"
            p.setPen(QColor("#374151"))
            p.drawText(0, int(cy - row_h / 2), label_w, int(row_h),
                       Qt.AlignVCenter | Qt.AlignRight, name)
            bw = bar_max_w * (val / max_v)
            p.fillRect(int(bar_x), int(cy - bar_h / 2), int(max(bw, 1)), int(bar_h),
                       QColor(self._color))
            p.setPen(QColor("#555"))
            p.drawText(int(bar_x + bw + 6), int(cy - row_h / 2), val_w, int(row_h),
                       Qt.AlignVCenter | Qt.AlignLeft, f"${format_miles_colombian_int(val)}")


class DataPage(QWidget):
    """Tablero de datos: indicadores clave, salud de cartera y tendencia."""

    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.setObjectName("dataPage")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(self.scroll)

        qss_path = os.path.join(STYLES_DIR, "home_page.qss")
        load_styles(self, qss_path)

        self._build()

    # ------------------------------------------------------------------ UI
    def _kpi(self, titulo, valor, color=PRIMARY_COLOR, subtitulo=None):
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet(
            f"#kpiCard{{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;"
            f"border-left:6px solid {color};}}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)
        t = QLabel(titulo)
        t.setStyleSheet("color:#6B7280;font-size:13px;")
        v = QLabel(valor)
        v.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;")
        lay.addWidget(t)
        lay.addWidget(v)
        if subtitulo:
            s = QLabel(subtitulo)
            s.setStyleSheet("color:#9CA3AF;font-size:11px;")
            lay.addWidget(s)
        return card

    def _seccion_titulo(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("font-size:16px;font-weight:bold;color:#374151;margin-top:8px;")
        return lbl

    def _chart_card(self, titulo, widget, color=PRIMARY_COLOR):
        """Tarjeta blanca con acento lateral que envuelve un gráfico."""
        card = QFrame()
        card.setObjectName("chartCard")
        card.setStyleSheet(
            f"#chartCard{{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;"
            f"border-left:6px solid {color};}}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        t = QLabel(titulo)
        t.setStyleSheet("font-size:15px;font-weight:bold;color:#374151;")
        lay.addWidget(t)
        lay.addWidget(widget)
        return card

    def _build(self):
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(60, 30, 60, 30)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignTop)

        titulo = QLabel("Tablero de datos")
        titulo.setStyleSheet("font-size:24px;font-weight:bold;color:#111827;")
        root.addWidget(titulo)

        if not self.db_manager:
            root.addWidget(QLabel("Sin conexión a datos."))
            self.scroll.setWidget(content)
            return

        try:
            m = self.db_manager.dashboard_metrics()
        except Exception as e:
            print(f"❌ Error cargando métricas del tablero: {e}")
            root.addWidget(QLabel("No se pudieron cargar las métricas."))
            self.scroll.setWidget(content)
            return

        def money(x):
            return f"${format_miles_colombian_int(x)}"

        # --- Arriba: indicadores clave ---
        row1 = QGridLayout()
        row1.setSpacing(14)
        row1.addWidget(self._kpi("Saldo en caja", money(m["saldo_caja"]), PRIMARY_COLOR), 0, 0)
        row1.addWidget(self._kpi("Aportes de socios", money(m["aportes_socios"]), PRIMARY_COLOR), 0, 1)
        row1.addWidget(self._kpi("Cartera por cobrar", money(m["cartera"]), PRIMARY_COLOR), 0, 2)
        row1.addWidget(self._kpi(
            "Administración", money(m["administracion"]), PRIMARY_COLOR,
            f"Papelería {money(m['papeleria'])} · Mora {money(m['mora_acumulada'])}"), 0, 3)
        root.addLayout(row1)

        # --- Medio: salud de cartera ---
        root.addWidget(self._seccion_titulo("Salud de la cartera"))
        row2 = QGridLayout()
        row2.setSpacing(14)
        row2.addWidget(self._kpi("Créditos al día", str(m["creditos_al_dia"]), VERDE), 0, 0)
        row2.addWidget(self._kpi("Créditos en mora", str(m["creditos_en_mora"]), ROJO), 0, 1)
        row2.addWidget(self._kpi("Recaudo del mes", money(m["recaudo_mes"]), VERDE), 0, 2)
        row2.addWidget(self._kpi(
            "Socios / Créditos vigentes",
            f"{m['socios_activos']} / {m['creditos_vigentes']}", PRIMARY_COLOR), 0, 3)
        root.addLayout(row2)

        # --- Abajo: mayores deudores + tendencia ---
        row3 = QHBoxLayout()
        row3.setSpacing(20)

        deudores_card = QFrame()
        deudores_card.setObjectName("summaryCard")
        dl = QVBoxLayout(deudores_card)
        dl.setContentsMargins(16, 12, 16, 12)
        dl.setSpacing(6)
        dl.addWidget(self._seccion_titulo("Mayores deudores"))
        if m["mayores_deudores"]:
            for d in m["mayores_deudores"]:
                row = QLabel(f"Letra {d['letra']} · {d['socios']} · {money(d['deuda'])}")
                row.setWordWrap(True)
                dl.addWidget(row)
        else:
            dl.addWidget(QLabel("Sin créditos vigentes."))
        dl.addStretch()
        row3.addWidget(deudores_card, 1)

        tendencia_card = QFrame()
        tendencia_card.setObjectName("summaryCard")
        tl = QVBoxLayout(tendencia_card)
        tl.setContentsMargins(16, 12, 16, 12)
        tl.setSpacing(6)
        tl.addWidget(self._seccion_titulo("Recaudo por mes"))
        datos = [(_mes_label(t["mes"]), t["total"]) for t in m["tendencia"]]
        tl.addWidget(_BarChart(datos))
        row3.addWidget(tendencia_card, 1)

        root.addLayout(row3)

        # --- Aportes e intereses (gráficas ampliadas) ---
        try:
            extra = self.db_manager.dashboard_charts()
        except Exception as e:
            print(f"❌ Error cargando gráficas de aportes/intereses: {e}")
            extra = None

        if extra:
            root.addWidget(self._seccion_titulo("Aportes e intereses"))

            # KPIs acumulados.
            rowk = QGridLayout()
            rowk.setSpacing(14)
            rowk.addWidget(self._kpi(
                "Aportes registrados (histórico)", money(extra["aportes_total"]), VERDE), 0, 0)
            rowk.addWidget(self._kpi(
                "Intereses recaudados (histórico)", money(extra["intereses_total"]), PRIMARY_COLOR), 0, 1)
            root.addLayout(rowk)

            # Comparativo mensual: Aportes vs Intereses (barras agrupadas).
            meses_union = sorted(
                {d["mes"] for d in extra["aportes_mes"]}
                | {d["mes"] for d in extra["intereses_mes"]}
            )
            ap_map = {d["mes"]: d["total"] for d in extra["aportes_mes"]}
            it_map = {d["mes"]: d["total"] for d in extra["intereses_mes"]}
            labels = [_mes_label(mm) for mm in meses_union]
            series = [
                {"name": "Aportes", "color": VERDE,
                 "values": [ap_map.get(mm, 0) for mm in meses_union]},
                {"name": "Intereses", "color": PRIMARY_COLOR,
                 "values": [it_map.get(mm, 0) for mm in meses_union]},
            ]
            root.addWidget(self._chart_card(
                "Aportes vs. Intereses por mes", _GroupedBarChart(labels, series), PRIMARY_COLOR))

            # Por socio: dos rankings horizontales lado a lado (Top 10).
            row_soc = QHBoxLayout()
            row_soc.setSpacing(20)
            ap_data = [(d["socio"], d["total"]) for d in extra["aportes_socio"]]
            it_data = [(d["socio"], d["total"]) for d in extra["intereses_socio"]]
            row_soc.addWidget(self._chart_card(
                "Aportes por socio (Top 10)", _HBarChart(ap_data, VERDE), VERDE), 1)
            row_soc.addWidget(self._chart_card(
                "Intereses por socio (Top 10)", _HBarChart(it_data, PRIMARY_COLOR), PRIMARY_COLOR), 1)
            root.addLayout(row_soc)

        self.scroll.setWidget(content)

    def refresh_view(self):
        print("🔁 Refrescando vista data")
        self._build()
