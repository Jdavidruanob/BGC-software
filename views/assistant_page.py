from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIntValidator # ¡Importar QIntValidator!
import os

from config import load_styles, format_miles_colombian_int
# Asumiendo que NoScrollComboBox no es necesario aquí si solo usas QComboBox
# from common.widgets import NoScrollComboBox 

class AssistantPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.page_size = 10
        self.current_page = 0
        
        # --- NUEVOS ATRIBUTOS PARA FILTROS ---
        self.filter_start_date = None
        self.filter_end_date = None
        self.filter_operation_type = None
        self.filter_socio_name = None
        self.filter_numero = None # Nuevo atributo para el filtro por número
        # --- FIN NUEVOS ATRIBUTOS ---

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

        # --- Zona de Filtros ---
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QVBoxLayout(filters_frame)
        filters_layout.setContentsMargins(15, 15, 15, 15)
        filters_layout.setSpacing(10)

        # Fila 1 de filtros: Fechas, Número y Tipo
        date_numero_type_layout = QHBoxLayout() # Renombrado para incluir numero
        
        date_numero_type_layout.addWidget(QLabel("Fecha Inicio:"))
        self.date_start_edit = QDateEdit(calendarPopup=True)
        self.date_start_edit.setDate(QDate.currentDate().addDays(-30)) # Por defecto, los últimos 30 días
        self.date_start_edit.setDisplayFormat("yyyy-MM-dd")
        date_numero_type_layout.addWidget(self.date_start_edit)

        date_numero_type_layout.addWidget(QLabel("Fecha Fin:"))
        self.date_end_edit = QDateEdit(calendarPopup=True)
        self.date_end_edit.setDate(QDate.currentDate())
        self.date_end_edit.setDisplayFormat("yyyy-MM-dd")
        date_numero_type_layout.addWidget(self.date_end_edit)
        
        # --- NUEVO: Filtro por Número entre fechas y tipo ---
        date_numero_type_layout.addWidget(QLabel("Número:"))
        self.numero_search_input = QLineEdit()
        self.numero_search_input.setPlaceholderText("Número")
        self.numero_search_input.setValidator(QIntValidator()) # Asegura que solo se ingresen números enteros
        self.numero_search_input.setFixedWidth(80) # Establece un ancho fijo para que sea pequeño
        date_numero_type_layout.addWidget(self.numero_search_input)
        # --- FIN NUEVO ---

        date_numero_type_layout.addStretch() # Espaciador

        date_numero_type_layout.addWidget(QLabel("Tipo de Operación:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos", None)
        self.type_combo.addItem("Aporte", "Aporte")
        self.type_combo.addItem("Retiro", "Retiro")
        self.type_combo.addItem("Nuevo Credito", "Nuevo Credito")
        self.type_combo.addItem("Pago Credito", "Pago Credito")
        date_numero_type_layout.addWidget(self.type_combo)
        
        filters_layout.addLayout(date_numero_type_layout) # Usar el layout renombrado

        # Fila 2 de filtros: Socio y Botones
        socio_buttons_layout = QHBoxLayout()
        socio_buttons_layout.addWidget(QLabel("Socio:"))
        self.socio_search_input = QLineEdit()
        self.socio_search_input.setPlaceholderText("Buscar por nombre o apellido del socio")
        socio_buttons_layout.addWidget(self.socio_search_input)

        self.apply_filters_btn = QPushButton("Aplicar Filtros")
        self.apply_filters_btn.setObjectName("applyFiltersButton")
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        socio_buttons_layout.addWidget(self.apply_filters_btn)

        self.clear_filters_btn = QPushButton("Limpiar Filtros")
        self.clear_filters_btn.setObjectName("clearFiltersButton")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        socio_buttons_layout.addWidget(self.clear_filters_btn)
        
        filters_layout.addLayout(socio_buttons_layout)
        
        main_layout.addWidget(filters_frame)
        # --- Fin Zona de Filtros ---

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
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.setColumnWidth(0, 150) # Fecha
        self.table_widget.setColumnWidth(1, 150) # Tipo (para el badge)
        self.table_widget.setColumnWidth(2, 650) # Socio (más grande)
        self.table_widget.setColumnWidth(3, 80)  # Número
        self.table_widget.setColumnWidth(4, 80)  # Cuota
        self.table_widget.setColumnWidth(5, 130) # Monto (requiere espacio para números grandes)
        self.table_widget.setColumnWidth(6, 150) # Saldo en Caja (requiere espacio para números grandes)

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

        # Cargar la primera página con los filtros iniciales
        self.apply_filters() # Llama a apply_filters para cargar con las fechas por defecto

    def apply_filters(self):
        """
        Recopila los valores de los filtros y recarga la tabla desde la primera página.
        """
        self.filter_start_date = self.date_start_edit.date().toString("yyyy-MM-dd")
        self.filter_end_date = self.date_end_edit.date().toString("yyyy-MM-dd")
        self.filter_operation_type = self.type_combo.currentData() # currentData() devuelve el valor asociado al item
        self.filter_socio_name = self.socio_search_input.text().strip()
        
        # --- NUEVO: Capturar el filtro de número ---
        numero_text = self.numero_search_input.text().strip()
        if numero_text:
            try:
                self.filter_numero = int(numero_text)
            except ValueError:
                self.filter_numero = None # Si no es un número válido, no aplicar filtro
        else:
            self.filter_numero = None
        # --- FIN NUEVO ---

        # Reiniciar la tabla y la paginación para aplicar los nuevos filtros
        self.table_widget.setRowCount(0)
        self.current_page = 0
        self.load_more_btn.setEnabled(True)
        self.load_more_btn.setText("Cargar más operaciones")
        self.load_next_page()

    def clear_filters(self):
        """
        Limpia todos los filtros y recarga la tabla.
        """
        self.date_start_edit.setDate(QDate.currentDate().addDays(-30)) # Vuelve a 30 días atrás
        self.date_end_edit.setDate(QDate.currentDate())
        self.type_combo.setCurrentIndex(0) # Selecciona "Todos"
        self.socio_search_input.clear()
        self.numero_search_input.clear() # Limpiar el campo del filtro de número
        
        # Aplicar filtros después de limpiar para recargar la tabla
        self.apply_filters()

    def load_next_page(self):
        """
        Carga la siguiente página de operaciones aplicando los filtros actuales.
        """
        ops = self.db_manager.get_auxiliary_operations(
            limit=self.page_size, 
            offset=self.current_page * self.page_size,
            start_date=self.filter_start_date,
            end_date=self.filter_end_date,
            operation_type=self.filter_operation_type,
            socio_name=self.filter_socio_name,
            numero=self.filter_numero # Pasar el nuevo filtro 'numero'
        )

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
        """
        Añade una operación a la tabla en la primera fila.
        Útil para añadir operaciones en tiempo real después de un registro.
        """
        # Si hay filtros aplicados, la nueva operación podría no aparecer
        # o aparecer en una posición incorrecta si no está ordenada.
        # Para simplificar, la añadimos al principio y la visibilidad
        # dependerá de si cumple los filtros actuales.
        
        # Si la nueva operación no cumple los filtros actuales, no la añadimos.
        # Esto requiere recrear la lógica de filtrado aquí para cada operación.
        # Una alternativa más robusta es simplemente llamar a refresh_view() después de una nueva operación
        # si queremos que los filtros se apliquen inmediatamente.
        
        # Por ahora, la añadiremos directamente, lo que puede causar que aparezca
        # si los filtros no se han aplicado al instante.
        
        # Verifica si la operación cumple los filtros actuales
        if self._matches_current_filters(op):
            self.table_widget.insertRow(0)
            self.build_operation_row(op, 0)
        # else: no se añade a la vista actual

    def _matches_current_filters(self, op):
        """
        Verifica si una operación dada coincide con los filtros actualmente aplicados.
        Esta es una comprobación simple en el cliente.
        """
        # Convertir fechas a QDate para comparación
        op_date = QDate.fromString(op["fecha"], "yyyy-MM-dd")
        filter_start_date_obj = QDate.fromString(self.filter_start_date, "yyyy-MM-dd")
        filter_end_date_obj = QDate.fromString(self.filter_end_date, "yyyy-MM-dd")

        # Filtrar por fecha
        if not (filter_start_date_obj <= op_date <= filter_end_date_obj):
            return False

        # Filtrar por tipo de operación
        if self.filter_operation_type and op["tipo"] != self.filter_operation_type:
            return False

        # Filtrar por socio
        if self.filter_socio_name:
            socio_lower = op["socio"].lower()
            search_lower = self.filter_socio_name.lower()
            if search_lower not in socio_lower:
                return False
        
        # --- NUEVO: Filtrar por número en el cliente ---
        if self.filter_numero is not None:
            if op.get("numero") != self.filter_numero:
                return False
        # --- FIN NUEVO ---
        
        return True

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
        item_socio.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Alineación a la izquierda
        self.table_widget.setItem(row_index, 2, item_socio)
        
        # Número (QTableWidgetItem) - Centrado
        # Asegúrate de que 'numero' exista y sea un número.
        numero_display = str(op.get("numero", "")) if op.get("numero") is not None else ""
        item_numero = QTableWidgetItem(numero_display)
        item_numero.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 3, item_numero)

        # Cuota (QTableWidgetItem) - Centrado, con lógica
        item_cuota = QTableWidgetItem("")
        # Asegúrate de que 'cuota' esté presente en el diccionario 'op' antes de intentar acceder.
        # Ya se maneja en la lógica del if, pero es bueno tenerlo en mente.
        if op.get("tipo", "").lower() == "pago credito" and op.get("cuota") is not None:
            item_cuota.setText(str(op["cuota"]))
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
        """
        Refresca completamente la vista, aplicando los filtros actuales.
        Esto es útil si se ha añadido/modificado una operación desde otra parte.
        """
        print("🔁 Refrescando vista auxiliar con filtros actuales")
        self.apply_filters() # Llama a apply_filters para reiniciar y recargar