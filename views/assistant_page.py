from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIntValidator # ¡Asegúrate de que QIntValidator esté importado!
import os

from config import load_styles, format_miles_colombian_int, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR

class AssistantPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.page_size = 100        # ajuste razonable
        self.current_page = 0
        self.no_more_pages = False
        self.loading = False
        
        # --- ATRIBUTOS PARA FILTROS ---
        self.filter_start_date = None
        self.filter_end_date = None
        self.filter_operation_type = None
        self.filter_socio_name = None
        self.filter_numero = None 
        self.filter_id_credito = None # Cambiado a filter_id_credito para claridad, almacenará el texto de "Cuota/Letra"
        # --- FIN ATRIBUTOS ---

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

        # Fila 1 de filtros: Fechas, Número y Cuota/Letra
        date_number_cuota_layout = QHBoxLayout() 
        
        date_number_cuota_layout.addWidget(QLabel("Fecha Inicio:"))
        self.date_start_edit = QDateEdit(calendarPopup=True)
        self.date_start_edit.setDate(QDate(QDate.currentDate().year() - 1, 11, 30)) # 30 noviembre del año pasado
        self.date_start_edit.setDisplayFormat("yyyy-MM-dd")
        date_number_cuota_layout.addWidget(self.date_start_edit)

        date_number_cuota_layout.addWidget(QLabel("Fecha Fin:"))
        self.date_end_edit = QDateEdit(calendarPopup=True)
        self.date_end_edit.setDate(QDate(QDate.currentDate().year(), 11, 30)) # 30 noviembre del año pasado
        self.date_end_edit.setDisplayFormat("yyyy-MM-dd")
        date_number_cuota_layout.addWidget(self.date_end_edit)
        
        # Filtro por Número Recibo
        date_number_cuota_layout.addWidget(QLabel("Número Recibo:")) 
        self.numero_search_input = QLineEdit()
        self.numero_search_input.setPlaceholderText("Recibo")
        self.numero_search_input.setValidator(QIntValidator()) 
        self.numero_search_input.setFixedWidth(80) 
        date_number_cuota_layout.addWidget(self.numero_search_input)
        
        # --- NUEVO: Filtro por Cuota/Letra (que usará id_credito para la DB) ---
        date_number_cuota_layout.addWidget(QLabel("Letra:")) # Etiqueta para el usuario
        self.cuota_letra_search_input = QLineEdit()
        self.cuota_letra_search_input.setPlaceholderText("ID o número de cuota")
        # ¡IMPORTANTE!: Removemos QIntValidator aquí, ya que id_credito es TEXT (alfanumérica)
        # Esto permite buscar por "CR001", "Letra A", etc.
        self.cuota_letra_search_input.setFixedWidth(120) 
        date_number_cuota_layout.addWidget(self.cuota_letra_search_input)
        # --- FIN NUEVO ---

        date_number_cuota_layout.addStretch() # Espaciador

        date_number_cuota_layout.addWidget(QLabel("Tipo Operación:")) 
        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos", None)
        self.type_combo.addItem("Aporte", "Aporte")
        self.type_combo.addItem("Retiro", "Retiro")
        self.type_combo.addItem("Nuevo Credito", "Nuevo Credito")
        self.type_combo.addItem("Pago Credito", "Pago Credito")
        date_number_cuota_layout.addWidget(self.type_combo)
        
        filters_layout.addLayout(date_number_cuota_layout) 

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

        # --- QTableWidget (manteniendo tus columnas originales) ---
        self.table_widget = QTableWidget()
        self.table_widget.setObjectName("operationsTable")
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setAlternatingRowColors(False) 

        # Tus encabezados de columna originales (sin la columna "Letra Crédito" visible)
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
        self.table_widget.setColumnWidth(5, 130) # Monto
        self.table_widget.setColumnWidth(6, 183.5) # Saldo en Caja

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.verticalHeader().setDefaultSectionSize(50) 
        
        # Conectar scroll para auto-load (carga más cuando esté cerca del final)
        self.table_widget.verticalScrollBar().valueChanged.connect(self.on_table_scroll) 
        # ValueChanged emite el valor actual del scrollbar
        # Así podemos detectar cuando está cerca del final
        # .conect() conecta la señal al slot on_table_scroll
        # recibiendo self.on_table_scroll() que devuelve None y no interfiere con la señal. pero si recibe el valor del scrollbar.
        # no es necesario pasar value porque QT lo hace automáticamente con connect().
        
        """ # Botón opcional "Cargar más" (fallback)
        self.load_more_btn = QPushButton("Cargar más operaciones")
        self.load_more_btn.setObjectName("loadMoreButton")
        self.load_more_btn.clicked.connect(self.load_next_page)
        self.load_more_btn.setVisible(False)  # visible solo si hay más
        main_layout.addWidget(self.load_more_btn, alignment=Qt.AlignCenter) """

        main_layout.addWidget(self.table_widget)

        # --- FIN QTableWidget ---

        #self.load_more_btn = QPushButton("Cargar más operaciones")
        #self.load_more_btn.setObjectName("loadMoreButton")
        #self.load_more_btn.clicked.connect(self.load_next_page)
        #main_layout.addWidget(self.load_more_btn, alignment=Qt.AlignCenter)

        qss_path = os.path.join(STYLES_DIR, "assistant_page.qss")
        load_styles(self, qss_path)

        # Cargar la primera página con los filtros iniciales
        self.apply_filters() 


    def load_next_page(self):
        # Evita llamadas concurrentes
        #print("➡️ load_next_page called")  # FIXME
        #print(f"no_more_pages: {self.no_more_pages}, loading: {self.loading}")  # FIXME
        if self.no_more_pages or self.loading:
            return
        self.loading = True
        #self.load_more_btn.setEnabled(False)

        try:
            ops = self.db_manager.get_auxiliary_operations(
                limit=self.page_size,
                offset=self.current_page * self.page_size,
                start_date=self.filter_start_date,
                end_date=self.filter_end_date,
                operation_type=self.filter_operation_type,
                socio_name=self.filter_socio_name,
                numero=self.filter_numero,
                letra_credito=self.filter_id_credito
            )

            if not ops:
                self.no_more_pages = True
                return

            current_row_count = self.table_widget.rowCount()
            self.table_widget.setRowCount(current_row_count + len(ops))

            for i, op in enumerate(ops):
                row_index = current_row_count + i
                self.build_operation_row(op, row_index)

            self.current_page += 1
            #print(f"len(ops) < page_size: {len(ops)} < {self.page_size}") # FIXME
            if len(ops) < self.page_size:
                
                self.no_more_pages = True
                
        finally:
            self.loading = False

    def on_table_scroll(self, value):
        """
        Detecta cuando el scrollbar está cerca del final y pide la siguiente página.
        """
        #print("🔽 Scroll value:", value)  # FIXME
        if self.no_more_pages or self.loading:
            return
        sb = self.table_widget.verticalScrollBar()
        threshold = 100  # Ajusta este valor si es necesario
        
        #print(f"sb.maximum(): {sb.maximum()}, threshold: {threshold}")  # FIXME
        
        if value >= sb.maximum() - threshold:
            self.load_next_page()

    def apply_filters(self):
        """
        Recopila los valores de los filtros y recarga la tabla desde la primera página.
        """
        self.filter_start_date = self.date_start_edit.date().toString("yyyy-MM-dd")
        self.filter_end_date = self.date_end_edit.date().toString("yyyy-MM-dd")
        self.filter_operation_type = self.type_combo.currentData() 
        self.filter_socio_name = self.socio_search_input.text().strip()
        
        # Capturar el filtro de número de recibo
        numero_text = self.numero_search_input.text().strip()
        if numero_text:
            try:
                self.filter_numero = int(numero_text)
            except ValueError:
                self.filter_numero = None 
        else:
            self.filter_numero = None

        # --- NUEVO: Capturar el filtro de id_credito (desde el campo "Cuota/Letra") ---
        # Si el usuario ingresa un valor en "Cuota/Letra", lo usamos para filtrar por id_credito.
        # No intentamos convertirlo a int aquí, ya que id_credito es TEXT en la DB.
        self.filter_id_credito = self.cuota_letra_search_input.text().strip()
        if not self.filter_id_credito:
            self.filter_id_credito = None
        # --- FIN NUEVO ---

        # Reiniciar la tabla y la paginación para aplicar los nuevos filtros
        self.table_widget.setRowCount(0)
        self.current_page = 0
        self.no_more_pages = False             # <-- reiniciar paginación
        #self.load_more_btn.setVisible(False)
        self.load_next_page()

    def clear_filters(self):
        """
        Limpia todos los filtros y recarga la tabla.
        """
        self.date_start_edit.setDate(QDate(QDate.currentDate().year() - 1, 11, 30)) 
        self.date_end_edit.setDate(QDate(QDate.currentDate().year(), 11, 30))
        self.type_combo.setCurrentIndex(0) 
        self.socio_search_input.clear()
        self.numero_search_input.clear() 
        self.cuota_letra_search_input.clear() # Limpiar el campo del filtro de cuota/letra (id_credito)
        
        self.apply_filters()

    def add_operation(self, op):
        """
        Agrega una nueva operación a la tabla si cumple con los filtros actuales.
        Para mantener la coherencia con los filtros aplicados y la paginación,
        lo mejor es refrescar toda la vista.
        """
        self.refresh_view() 
        
    def _matches_current_filters(self, op):
        """
        Verifica si una operación dada coincide con los filtros actualmente aplicados.
        Este método es útil si decides añadir operaciones una por una sin recargar toda la tabla.
        Si add_operation() siempre llama a refresh_view(), este método no es estrictamente necesario.
        """
        op_date = QDate.fromString(op["fecha"], "yyyy-MM-dd")
        filter_start_date_obj = QDate.fromString(self.filter_start_date, "yyyy-MM-dd")
        filter_end_date_obj = QDate.fromString(self.filter_end_date, "yyyy-MM-dd")

        if not (filter_start_date_obj <= op_date <= filter_end_date_obj):
            return False
        if self.filter_operation_type and op["tipo"] != self.filter_operation_type:
            return False
        if self.filter_socio_name:
            socio_lower = op["socio"].lower()
            search_lower = self.filter_socio_name.lower()
            if search_lower not in socio_lower:
                return False
        if self.filter_numero is not None:
            if op.get("numero") != self.filter_numero:
                return False
        
        # --- NUEVO en _matches_current_filters (filtrando por id_credito) ---
        if self.filter_id_credito: # Si hay un valor en el filtro de Cuota/Letra
            # Comprueba si la operación tiene un 'id_credito' y si coincide
            if op.get("id_credito", "") != self.filter_id_credito:
                return False
        # --- FIN NUEVO ---
        return True

    def build_operation_row(self, op, row_index):
        """
        Construye una fila en el QTableWidget con los datos de una operación.
        No se añade una nueva columna visible para 'id_credito' aquí.
        """
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
        item_socio.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter) 
        self.table_widget.setItem(row_index, 2, item_socio)
        
        # Número (QTableWidgetItem) - Centrado
        numero_display = str(op.get("numero", "")) if op.get("numero") is not None else ""
        item_numero = QTableWidgetItem(numero_display)
        item_numero.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table_widget.setItem(row_index, 3, item_numero)

        # Cuota (QTableWidgetItem) - Centrado, con lógica para mostrar solo en Pagos Credito
        item_cuota = QTableWidgetItem("")
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

        # No se añade ni se manipula la columna 7, ya que la has eliminado de los encabezados.

    def refresh_view(self):
        """
        Método conveniente para forzar un refresco completo de la vista de operaciones.
        """
        print("🔁 Refrescando vista auxiliar con filtros actuales")
        self.apply_filters()