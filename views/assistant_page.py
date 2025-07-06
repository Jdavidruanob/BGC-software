from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QFrame
)
from PySide6.QtCore import Qt
import os

from config import load_styles, format_money_colombian

class AssistantPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.page_size = 10
        self.current_page = 0

        self.setObjectName("assistantPage")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(80, 30, 80, 30)
        main_layout.setSpacing(15)

        # Top bar azul con título
        top_bar = QFrame()
        top_bar.setObjectName("assistantTopBar")
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("📘 Registro de Operaciones")
        title.setObjectName("assistantTitle")
        top_bar_layout.addWidget(title)
        top_bar.setLayout(top_bar_layout)
        main_layout.addWidget(top_bar)

        # Encabezado de tabla
        header_row = QFrame()
        header_row.setObjectName("assistantHeader")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(20)

        for label in ["Fecha", "Tipo", "Socio", "Número", "Monto", "Saldo en Caja"]:
            lbl = QLabel(label)
            lbl.setObjectName("headerLabel")
            header_layout.addWidget(lbl)

        header_row.setLayout(header_layout)
        main_layout.addWidget(header_row)

        # Scroll de contenido
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(self.scroll_area)

        self.load_more_btn = QPushButton("Cargar más operaciones")
        self.load_more_btn.clicked.connect(self.load_next_page)
        main_layout.addWidget(self.load_more_btn, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "assistant_page.qss")
        load_styles(self, qss_path)

        self.load_next_page()

    def load_next_page(self):
        ops = self.db_manager.get_auxiliary_operations(limit=self.page_size, offset=self.current_page * self.page_size)
        for op in ops:
            self.scroll_layout.addWidget(self.build_operation_row(op))
        self.current_page += 1

    def build_operation_row(self, op):
        row = QFrame()
        row.setObjectName("operationRow")
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        lbl_fecha = QLabel(op["fecha"])
        lbl_fecha.setObjectName("opFecha")

        lbl_tipo = QLabel(op["tipo"])
        lbl_tipo.setObjectName(f"opTipo_{op['tipo'].lower().replace(' ', '_')}")
        lbl_tipo.setStyleSheet("padding: 4px 8px; border-radius: 6px;")

        lbl_socio = QLabel(op["socio"])
        lbl_socio.setObjectName("opSocio")

        lbl_numero = QLabel(str(op["numero"]))
        lbl_numero.setObjectName("opNumero")

        lbl_monto = QLabel(f"{format_money_colombian(op['monto'])}")
        lbl_monto.setObjectName("opMonto")
        lbl_monto.setProperty("montoTipo", "negativo" if op["monto"] < 0 else "positivo")

        lbl_saldo = QLabel(f"{format_money_colombian(op['saldo'])}")
        lbl_saldo.setObjectName("opSaldo")
        lbl_saldo.setStyleSheet("font-weight: bold;")

        layout.addWidget(lbl_fecha)
        layout.addWidget(lbl_tipo)
        layout.addWidget(lbl_socio)
        layout.addWidget(lbl_numero)
        layout.addWidget(lbl_monto)
        layout.addWidget(lbl_saldo)

        row.setLayout(layout)
        return row
