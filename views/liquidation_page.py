from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QFrame
)
from PySide6.QtCore import Qt
import os
from datetime import datetime, timedelta

from config import load_styles, format_money_colombian


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
            f"Capital: ${format_money_colombian(credit['capital'])}",
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

         # Encabezado de columnas (estilo tabla)
        header_row = QFrame()
        header_row.setObjectName("liqTableHeader")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(20)

        headers = [
            "Fecha", "Cuota", "Valor Cuota", "Intereses",
            "Total Mensual", "Saldo Capital", "Fecha Pago"
        ]

        for h in headers:
            lbl = QLabel(h)
            lbl.setObjectName("liqTableHeaderLabel")
            header_layout.addWidget(lbl)

        header_row.setLayout(header_layout)
        main_layout.addWidget(header_row)


        # Scroll para las cuotas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

        # Estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "liquidation_page.qss")
        load_styles(self, qss_path)

        # Generar cuotas
        self.generate_liquidation_schedule()

    def generate_liquidation_schedule(self):
        capital = self.credit["capital"]
        interes = self.credit["interes"]
        cuotas = self.credit["no_cuotas"]
        fecha_inicio = datetime.strptime(self.credit["fecha_inicio"][:10], "%Y-%m-%d")

        cuota_base = round((capital / cuotas) / 10000) * 10000
        total_redondeado = cuota_base * cuotas
        diferencia = total_redondeado - capital

        cuotas_normales = cuotas - 1
        total_normales = cuota_base * cuotas_normales
        cuota_final = capital - total_normales

        if cuota_final < 10000:
            cuota_final = 10000
            cuotas_normales = cuotas - 1
            total_normales = capital - cuota_final
            cuota_base = round(total_normales / cuotas_normales / 10000) * 10000

        saldo = capital

        cuotas_db = []

        for i in range(cuotas):
            nro_cuota = i + 1
            fecha = fecha_inicio + timedelta(days=30 * i)

            cuota_valor = cuota_final if i == cuotas - 1 else cuota_base
            intereses = round(saldo * interes)
            cuota_mensual = cuota_valor + intereses
            saldo -= cuota_valor

            # Agregar visual
            self.scroll_layout.addWidget(self.build_row(
                fecha.strftime("%Y-%m-%d"),
                nro_cuota,
                cuota_valor,
                intereses,
                cuota_mensual,
                max(0, saldo),
                None  # fecha_pago (a futuro vendrá desde la base de datos)
            ))


            # Preparar para guardar en BD
            cuotas_db.append((
                self.credit["letra"],
                nro_cuota,
                fecha.strftime("%Y-%m-%d"),
                cuota_valor,
                intereses,
                cuota_mensual,
                max(0, saldo),
                None  # fecha_pago por ahora es NULL
            ))

        # Guardar en la BD si aún no existen
        existing = self.db_manager.conn.execute(
            "SELECT COUNT(*) FROM liquidaciones WHERE credito_letra = ?",
            (self.credit["letra"],)
        ).fetchone()[0]

        if existing == 0:
            self.db_manager.guardar_liquidaciones(cuotas_db)


    def build_row(self, fecha, nro_cuota, valor_cuota, intereses, total, saldo, fecha_pago=None):
        row = QFrame()
        row.setObjectName("liqRow")
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        items = [
            fecha,
            str(nro_cuota),
            f"${format_money_colombian(valor_cuota)}",
            f"${format_money_colombian(intereses)}",
            f"${format_money_colombian(total)}",
            f"${format_money_colombian(saldo)}",
            fecha_pago or " "  # Mostrar "—" si aún no tiene fecha de pago
        ]

        for i in items:
            lbl = QLabel(i)
            lbl.setObjectName("liqItem")
            layout.addWidget(lbl)

        row.setLayout(layout)
        return row
