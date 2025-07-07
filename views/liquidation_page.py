from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
import os
from datetime import datetime, timedelta

from config import load_styles, format_money_colombian


class CreditLiquidationPage(QWidget):
    def __init__(self, credit, member_id, main_window):
        super().__init__()
        self.setObjectName("creditLiquidationPage")
        self.credit = credit
        self.setMinimumSize(900, 600)
        self.setWindowTitle("Liquidación del Crédito")
        self.main_window = main_window
        self.member_id = member_id

        layout = QVBoxLayout()
        layout.setContentsMargins(80, 30, 80, 30)
        layout.setSpacing(20)

        # Back button
        back_btn = QPushButton("← Volver")
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        view = f"member_detail_{member_id}"
        back_btn.clicked.connect(lambda: self.main_window.show_view(view))
        layout.addWidget(back_btn)
        layout.setAlignment(back_btn, Qt.AlignLeft)

        # Título
        title = QLabel("Liquidación del Crédito")
        title.setObjectName("liqTitle")
        layout.addWidget(title)

        # Datos del crédito
        info_layout = QHBoxLayout()
        info_layout.setSpacing(40)

        letra_label = QLabel(f"Letra: {credit['letra']}")
        capital_label = QLabel(f"Capital: ${format_money_colombian(credit['capital'])}")
        fecha_label = QLabel(f"Fecha: {credit['fecha_inicio'][:10]}")
        cuotas_label = QLabel(f"No. Cuotas: {credit['no_cuotas']}")

        for lbl in [letra_label, capital_label, fecha_label, cuotas_label]:
            lbl.setObjectName("liqInfoLabel")
            info_layout.addWidget(lbl)

        layout.addLayout(info_layout)

        # Socios
        socios_label = QLabel(f"👥 Socios participantes: {credit['socios']}")
        socios_label.setObjectName("liqSocioLabel")
        layout.addWidget(socios_label)

        # Tabla de liquidación
        self.liquidation_table = QTableWidget()
        self.liquidation_table.setColumnCount(7)
        self.liquidation_table.setHorizontalHeaderLabels([
            "Fecha", "Cuota", "Valor Cuota", "Intereses",
            "Cuota Mensual", "Saldo Capital", "Fecha Pago"
        ])
        self.liquidation_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.generate_liquidation_schedule()

        layout.addWidget(self.liquidation_table)
        self.setLayout(layout)

        # Estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "liquidation_page.qss")
        load_styles(self, qss_path)

    def generate_liquidation_schedule(self):
        capital = self.credit["capital"]
        interes = self.credit["interes"]
        cuotas = self.credit["no_cuotas"]
        fecha_inicio = datetime.strptime(self.credit["fecha_inicio"][:10], "%Y-%m-%d")

        # 1. Redondear la cuota base al múltiplo de 10.000 más cercano
        cuota_base = round((capital / cuotas) / 10000) * 10000

        # 2. Calcular total pagado con cuota_base
        total_redondeado = cuota_base * cuotas

        # 3. Calcular la diferencia con el capital real
        diferencia = total_redondeado - capital

        # Si la diferencia es negativa, significa que el redondeo quedó por debajo
        # Entonces subimos una de las cuotas (la última) para compensar
        cuotas_normales = cuotas - 1
        total_normales = cuota_base * cuotas_normales
        cuota_final = capital - total_normales

        # Aseguramos que cuota final sea redondeada también y no quede en 0
        if cuota_final < 10000:
            cuota_final = 10000
            cuotas_normales = cuotas - 1
            total_normales = capital - cuota_final
            cuota_base = round(total_normales / cuotas_normales / 10000) * 10000

        saldo = capital
        self.liquidation_table.setRowCount(cuotas)

        for i in range(cuotas):
            nro_cuota = i + 1
            fecha = fecha_inicio + timedelta(days=30 * i)

            if i == cuotas - 1:
                cuota_valor = cuota_final
            else:
                cuota_valor = cuota_base

            intereses = round(saldo * interes)
            cuota_mensual = cuota_valor + intereses
            saldo -= cuota_valor

            row = [
                fecha.strftime("%Y-%m-%d"),
                str(nro_cuota),
                f"${format_money_colombian(cuota_valor)}",
                f"${format_money_colombian(intereses)}",
                f"${format_money_colombian(cuota_mensual)}",
                f"${format_money_colombian(max(0, saldo))}",
                ""  # Fecha pago vacía
            ]

            for col, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.liquidation_table.setItem(i, col, item)

