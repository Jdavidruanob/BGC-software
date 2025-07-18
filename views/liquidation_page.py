from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import os
from datetime import datetime, timedelta

from config import load_styles, format_miles_colombian_int

class CreditLiquidationPage(QWidget):
    def __init__(self, credit, member_id, main_window, db_manager):
        super().__init__()
        self.setObjectName("creditLiquidationPage")
        self.credit = credit
        self.main_window = main_window
        self.member_id = member_id
        self.db_manager = db_manager

        self.setMinimumSize(900, 600)
        self.setWindowTitle("Liquidación del Crédito")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(80, 30, 80, 30)
        main_layout.setSpacing(15)

        # Top bar azul con título y botón de regreso
        top_bar = QFrame()
        top_bar.setObjectName("liqTopBar")
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        back_btn = QPushButton("← Volver")
        back_btn.setObjectName("liqBackButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.show_view(f"member_detail_{member_id}"))

        title = QLabel("🧾 Liquidación del Crédito")
        title.setObjectName("liqTitle")

        top_bar_layout.addWidget(back_btn)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(title)
        top_bar_layout.addStretch()
        top_bar.setLayout(top_bar_layout)
        main_layout.addWidget(top_bar)

        # Encabezado de datos del crédito
        credit_info = QFrame()
        credit_info.setObjectName("liqHeader")
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(20, 5, 20, 5)
        info_layout.setSpacing(20)

        fields = [
            f"Letra: {credit['letra']}",
            f"Capital: ${format_miles_colombian_int(credit['capital'])}",
            f"Fecha: {credit['fecha_inicio'][:10]}",
            f"Cuotas: {credit['no_cuotas']}"
        ]
        for f in fields:
            lbl = QLabel(f)
            lbl.setObjectName("liqInfoLabel")
            info_layout.addWidget(lbl)

        credit_info.setLayout(info_layout)
        main_layout.addWidget(credit_info)

        # Socios
        socios_label = QLabel(f"👥 Socios participantes: {credit['socios']}")
        socios_label.setObjectName("liqSocios")
        main_layout.addWidget(socios_label)

        # ---- QTableWidget para la tabla de liquidación ----
        headers = [
            "Fecha", "Cuota", "Valor Cuota", "Intereses",
            "Total Mensual", "Saldo Capital", "Fecha Pago"
        ]
        self.table = QTableWidget(0, len(headers))
        self.table.setObjectName("liqTableWidget")
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)  # Oculta la columna de índices
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Ocupa todo el ancho
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget#liqTableWidget {
                background: white;
                border: 1px solid #DADDE1;
                font-size: 16px;
            }
            QHeaderView::section {
                background: #E9ECEF;
                font-weight: bold;
                font-size: 15px;
                color: #333;
                border: 1px solid #DADDE1;
                padding: 8px 4px;
            }
            QTableWidget::item {
                padding: 5px 8px;
                border-right: 1px solid #EEEEEE;
            }
            QTableWidget::item:last-child {
                border-right: none;
            }
        """)

        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # Estilos adicionales
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "liquidation_page.qss")
        load_styles(self, qss_path)

        # Generar cuotas
        self.generate_liquidation_schedule()

    def generate_liquidation_schedule(self):
        capital = self.credit["capital"]
        interes = self.credit["interes"]
        cuotas = self.credit["no_cuotas"]
        fecha_inicio = datetime.strptime(self.credit["fecha_inicio"][:10], "%Y-%m-%d")

        cuota_base = None
        cuota_final = None

        # Buscar el mejor redondeo que cumpla condiciones
        for redondeo in [10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]:
            posible_cuota = round((capital / cuotas) / redondeo) * redondeo
            total_normales = posible_cuota * (cuotas - 1)
            ultima_cuota = capital - total_normales

            if 10000 <= ultima_cuota <= posible_cuota * 1.5:
                cuota_base = posible_cuota
                cuota_final = ultima_cuota
                break

        if cuota_base is None:
            # Último recurso: sin redondear, pero garantizando últimas condiciones mínimas
            cuota_base = capital // cuotas
            cuota_final = capital - cuota_base * (cuotas - 1)

        saldo = capital
        cuotas_db = []
        self.table.setRowCount(cuotas)
        fecha_primera_cuota = fecha_inicio + timedelta(days=30)

        for i in range(cuotas):
            nro_cuota = i + 1
            fecha = fecha_primera_cuota + timedelta(days=30 * i)

            cuota_valor = cuota_final if i == cuotas - 1 else cuota_base
            intereses = round(saldo * interes)
            cuota_mensual = cuota_valor + intereses
            saldo -= cuota_valor

            # Buscar si ya fue pagada
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT fecha_pago FROM liquidaciones
                WHERE credito_letra = ? AND nro_cuota = ?
            """, (self.credit["letra"], nro_cuota))
            fecha_pago_row = cursor.fetchone()
            fecha_pago_str = fecha_pago_row["fecha_pago"] if fecha_pago_row and fecha_pago_row["fecha_pago"] else ""

            row = [
                fecha.strftime("%Y-%m-%d"),
                str(nro_cuota),
                f"${format_miles_colombian_int(cuota_valor)}",
                f"${format_miles_colombian_int(intereses)}",
                f"${format_miles_colombian_int(cuota_mensual)}",
                f"${format_miles_colombian_int(max(0, saldo))}",
                fecha_pago_str
            ]

            for col, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, col, item)

            cuotas_db.append((
                self.credit["letra"],
                nro_cuota,
                fecha.strftime("%Y-%m-%d"),
                cuota_valor,
                intereses,
                cuota_mensual,
                max(0, saldo),
                None
            ))

        existing = self.db_manager.conn.execute(
            "SELECT COUNT(*) FROM liquidaciones WHERE credito_letra = ?",
            (self.credit["letra"],)
        ).fetchone()[0]

        if existing == 0:
            self.db_manager.guardar_liquidaciones(cuotas_db)



    def refresh_view(self):
        """Refresca la tabla de liquidación mostrando fechas de pago actualizadas."""
        self.table.clearContents()
        self.generate_liquidation_schedule()
