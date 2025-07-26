from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import os

from config import load_styles, format_miles_colombian_int

class AssistantPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.page_size = 10
        self.current_page = 0

        self.setObjectName("assistantPage")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 30, 80, 30)
        main_layout.setSpacing(15)

        # Top bar azul con título
        top_bar = QFrame()
        top_bar.setObjectName("assistantTopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("📘 Registro de Operaciones")
        title.setObjectName("assistantTitle")
        top_bar_layout.addWidget(title)
        top_bar_layout.addStretch()
        top_bar.setLayout(top_bar_layout)
        main_layout.addWidget(top_bar)

        # --- QTableWidget ---
        self.table_widget = QTableWidget()
        self.table_widget.setObjectName("operationsTable")
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setAlternatingRowColors(False) # Desactivar colores alternos

        column_headers = ["Fecha", "Tipo", "Socio", "Número", "Cuota", "Monto", "Saldo en Caja"]
        self.table_widget.setColumnCount(len(column_headers))
        self.table_widget.setHorizontalHeaderLabels(column_headers)

        header = self.table_widget.horizontalHeader()
        
        # --- CAMBIO CLAVE: Ajustar el modo de redimensionamiento de nuevo ---
        # Combinamos ResizeToContents para elementos pequeños y Stretch para los que necesitan espacio.
        # Damos un factor de estiramiento para Socio si queremos que sea significativamente más grande.
        
        # Si tienes PySide6 6.2 o superior, puedes usar setSectionResizeMode con el factor de estiramiento:
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Tipo
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Socio (se estira más)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Número
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Cuota
        header.setSectionResizeMode(5, QHeaderView.Stretch)          # Monto (se estira)
        header.setSectionResizeMode(6, QHeaderView.Stretch)          # Saldo en Caja (se estira)
        
        # Para que "Socio" sea MÁS grande que "Monto" y "Saldo en Caja"
        # Usamos `setSectionResizeMode(index, QHeaderView.Stretch)` para las columnas que deseamos estirar.
        # Si queremos control proporcional sobre ellas, necesitamos `QHeaderView.Custom` y calcular nosotros los anchos.
        # Pero generalmente, con múltiples `Stretch`, el espacio se distribuye equitativamente entre ellas.
        # Para forzar que Socio sea MÁS GRANDE, podemos darle un ancho mínimo considerable.
        header.setMinimumSectionSize(0) # Resetear cualquier mínimo previo
        header.setStretchLastSection(True) # Permitir que la última columna se estire para llenar el espacio restante
                                          # Esto es importante cuando tienes una mezcla de Stretch y ResizeToContents.

        # Alternativa para un "Socio" mucho más grande:
        # header.setSectionResizeMode(2, QHeaderView.Custom)
        # self.table_widget.setColumnWidth(2, 300) # Un ancho inicial grande para Socio
        # Y las demás Stretch o ResizeToContents.
        # Pero volvemos a Fixed sizes, lo que quieres evitar.

        # Intentemos con Stretch y ResizeToContents nuevamente, pero asegurando que los `QLabel` tengan espacio
        # Esto se logrará con padding en QSS y el `ResizeToContents` para el tipo.
        # Para Monto y Saldo en Caja, si el texto se corta, `Stretch` es la mejor opción.
        # Y para Socio, si queremos que sea "notablemente más grande", podemos darle un peso de estiramiento.

        # *** NUEVO INTENTO DE REDIMENSIONAMIENTO (más robusto) ***
        # Daremos "pesos" a las columnas que se estiran. Esto requiere un modo de redimensionamiento
        # específico para cada columna, y PySide/Qt distribuirá el espacio sobrante.
        header.setSectionResizeMode(QHeaderView.Interactive) # Permite al usuario redimensionar
        # Establecemos los anchos iniciales. Si no hay suficiente espacio, las columnas Interactive pueden crecer.
        self.table_widget.setColumnWidth(0, 150) # Fecha
        self.table_widget.setColumnWidth(1, 150) # Tipo (para el badge)
        self.table_widget.setColumnWidth(2, 650) # Socio (más grande)
        self.table_widget.setColumnWidth(3, 80)  # Número
        self.table_widget.setColumnWidth(4, 80)  # Cuota
        self.table_widget.setColumnWidth(5, 130) # Monto (requiere espacio para números grandes)
        self.table_widget.setColumnWidth(6, 150) # Saldo en Caja (requiere espacio para números grandes)

        # Si aún se cortan, es que los anchos iniciales son muy pequeños.
        # Con `Interactive` el usuario puede ajustarlos, pero queremos que se vean bien por defecto.
        # Para asegurarnos que los `QLabel` no se corten, el `padding` en QSS es clave.

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.verticalHeader().setDefaultSectionSize(50) # Altura de las filas

        main_layout.addWidget(self.table_widget)
        # --- FIN QTableWidget ---

        self.load_more_btn = QPushButton("Cargar más operaciones")
        self.load_more_btn.setObjectName("loadMoreButton")
        self.load_more_btn.clicked.connect(self.load_next_page)
        main_layout.addWidget(self.load_more_btn, alignment=Qt.AlignCenter)

        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "assistant_page.qss")
        load_styles(self, qss_path)

        self.load_next_page()

    def load_next_page(self):
        # Asegúrate de que tu `db_manager.get_auxiliary_operations` devuelva `cuota`
        # para los tipos de operación "pago credito". Si no, la columna "Cuota"
        # siempre estará vacía.
        ops = self.db_manager.get_auxiliary_operations(limit=self.page_size, offset=self.current_page * self.page_size)
        if not ops:
            self.load_more_btn.setEnabled(False)
            self.load_more_btn.setText("No hay más operaciones")
            return

        current_row_count = self.table_widget.rowCount()
        self.table_widget.setRowCount(current_row_count + len(ops))

        for i, op in enumerate(ops):
            row_index = current_row_count + i
            self.build_operation_row(op, row_index)
            
        self.current_page += 1

    def add_operation(self, op):
        self.table_widget.insertRow(0)
        self.build_operation_row(op, 0)
        
    def build_operation_row(self, op, row_index):
        # Fecha (QTableWidgetItem) - Centrado
        item_fecha = QTableWidgetItem(op["fecha"])
        item_fecha.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 0, item_fecha)
        
        # Tipo de operación (QLabel) - Centrado
        lbl_tipo = QLabel(op["tipo"])
        lbl_tipo.setObjectName(f"opTipo_{op['tipo'].lower().replace(' ', '_')}")
        lbl_tipo.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setCellWidget(row_index, 1, lbl_tipo)

        # Socio (QTableWidgetItem) - Izquierda
        item_socio = QTableWidgetItem(op["socio"])
        item_socio.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 2, item_socio)
        
        # Número (QTableWidgetItem) - Centrado
        item_numero = QTableWidgetItem(str(op["numero"]))
        item_numero.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 3, item_numero)

        # Cuota (QTableWidgetItem) - Centrado, con lógica
        item_cuota = QTableWidgetItem("")
        if op["tipo"].lower() == "pago credito" and "cuota" in op and op["cuota"] is not None:
            item_cuota.setText(str(op["cuota"]))
            print(str(op["cuota"]))
        item_cuota.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 4, item_cuota)

        # Monto (QLabel) - Derecha
        lbl_monto = QLabel(f"{format_miles_colombian_int(op['monto'])}")
        lbl_monto.setObjectName("opMonto")
        lbl_monto.setProperty("montoTipo", "negativo" if op["monto"] < 0 else "positivo")
        lbl_monto.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_widget.setCellWidget(row_index, 5, lbl_monto)

        # Saldo (QLabel) - Derecha
        lbl_saldo = QLabel(f"{format_miles_colombian_int(op['saldo'])}")
        lbl_saldo.setObjectName("opSaldo")
        lbl_saldo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_widget.setCellWidget(row_index, 6, lbl_saldo)

    def refresh_view(self):
        print("🔁 Refrescando vista auxiliar")
        self.table_widget.setRowCount(0)
        self.current_page = 0
        self.load_more_btn.setEnabled(True)
        self.load_more_btn.setText("Cargar más operaciones")
        self.load_next_page()