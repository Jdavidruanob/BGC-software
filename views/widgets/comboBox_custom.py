from PySide6.QtWidgets import QComboBox, QLineEdit, QStyledItemDelegate, QListView
from PySide6.QtCore import Qt, QSortFilterProxyModel, QEvent, QTimer, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QMouseEvent

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None, placeholder_text="-- Seleccionar --"):
        super().__init__(parent)
        
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setFocusPolicy(Qt.StrongFocus)
        self.placeholder_text = placeholder_text
        
        # 1. Configuración del Modelo
        self.source_model = QStandardItemModel()
        
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)
        
        self.setModel(self.proxy_model)
        
        # 2. Configuración de la VISTA (El desplegable)
        # Usamos un QListView explícito para tener control total
        self.list_view = QListView(self)
        self.setView(self.list_view)
        
        # 3. Desactivar COMPLETAMENTE el autocompletado nativo
        self.setCompleter(None)
        
        # 4. Configurar el LineEdit
        self.lineEdit().setPlaceholderText(placeholder_text)
        self.lineEdit().installEventFilter(self)
        
        # Conectamos la señal de escritura
        self.lineEdit().textEdited.connect(self.on_text_edited)
        
        # Variables de estado
        self.last_valid_index = -1
        self.is_filtering = False
        
        # Inicializar
        self.add_default_option()

    def add_default_option(self):
        if self.source_model.rowCount() == 0:
            item = QStandardItem(self.placeholder_text)
            item.setData(None, Qt.UserRole)
            self.source_model.appendRow(item)

    def populate_socios(self, socios_data):
        self.source_model.clear()
        self.add_default_option()
        
        for socio in socios_data:
            text = f"#{socio['id']} - {socio['nombres']} {socio['apellidos']}"
            item = QStandardItem(text)
            item.setData(socio, Qt.UserRole)
            self.source_model.appendRow(item)
            
        self.setCurrentIndex(0)
        self.last_valid_index = 0

    def eventFilter(self, obj, event):
        """
        Maneja el clic en el input.
        """
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            # Si hacemos clic, abrimos el popup limpio
            self.show_search_popup()
            return True # Importante: Consumimos el evento para evitar parpadeos nativos
        
        return super().eventFilter(obj, event)

    def show_search_popup(self):
        """Prepara el popup para buscar."""
        # Guardar índice actual
        self.last_valid_index = self.currentIndex()
        
        # Resetear filtro (mostrar todo) SIN cerrar
        self.proxy_model.setFilterFixedString("")
        
        # Limpiar texto visualmente
        self.lineEdit().setText("")
        
        # Mostrar el popup manualmente
        super().showPopup()

    def on_text_edited(self, text):
        """
        Filtra sin causar el 'reinicio' visual.
        """
        self.is_filtering = True
        
        # Actualizar el filtro
        self.proxy_model.setFilterFixedString(text)
        
        # Si al filtrar no quedan resultados o el combo intenta cerrarse, forzamos que se vea
        if self.count() > 0:
            if not self.view().isVisible():
                super().showPopup()
        else:
            # Opcional: Si no hay resultados, ocultar
            self.hidePopup()
            
        self.is_filtering = False

    def hidePopup(self):
        """
        Controlamos cuándo se cierra realmente el popup.
        """
        # Si estamos en medio de un proceso de filtrado, NO cerramos
        if self.is_filtering:
            return
            
        super().hidePopup()
        
        # Al cerrar, validamos lo que quedó
        self.validate_selection()

    def validate_selection(self):
        """Restaura el valor si el usuario no seleccionó nada válido."""
        current_text = self.currentText()
        
        # Verificar si el texto actual coincide con una opción
        # Usamos findText con MatchExactly para ser precisos
        idx = self.findText(current_text, Qt.MatchExactly) # Ojo: MatchFixedString a veces falla con Proxy
        
        if idx == -1:
            # No es válido (escribió a medias y se fue)
            if self.last_valid_index >= 0:
                self.setCurrentIndex(self.last_valid_index)
                
                # Forzar visualización del texto
                if self.last_valid_index < self.count():
                    # Obtenemos el texto real del modelo a través del proxy
                    # Nota: currentIndex es sobre el proxy
                    real_text = self.itemText(self.last_valid_index)
                    self.lineEdit().setText(real_text)
            else:
                self.setCurrentIndex(0)
                self.lineEdit().setText("")
        else:
            # Selección válida
            self.last_valid_index = idx

    def currentData_safe(self):
        idx = self.currentIndex()
        if idx < 0: return None
        return self.itemData(idx, Qt.UserRole)

    def wheelEvent(self, event):
        event.ignore()