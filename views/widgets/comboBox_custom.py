import unicodedata

from PySide6.QtWidgets import QComboBox, QCompleter, QListView
from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel, QEvent, QTimer, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

from config import PRIMARY_COLOR

# Rol donde guardamos el texto "normalizado" (minúsculas, sin tildes) para buscar.
NORM_ROLE = Qt.UserRole + 100


def strip_accents(text) -> str:
    """Devuelve el texto en minúsculas y sin tildes, para búsquedas tolerantes.
    'José Ángel' -> 'jose angel'."""
    if text is None:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(text))
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_tildes.lower().strip()


class NoScrollComboBox(QComboBox):
    """QComboBox que ignora la rueda del mouse (evita cambiar el valor sin querer)."""

    def wheelEvent(self, event):
        event.ignore()


class _AccentInsensitiveProxy(QSortFilterProxyModel):
    """Filtra las filas cuyo texto normalizado (NORM_ROLE) contiene la búsqueda."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._needle = ""

    def set_needle(self, text):
        nuevo = strip_accents(text)
        if nuevo != self._needle:
            self._needle = nuevo
            self.invalidateFilter()

    def reset_needle(self):
        if self._needle:
            self._needle = ""
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._needle:
            return True
        idx = self.sourceModel().index(source_row, 0, source_parent)
        norm = self.sourceModel().data(idx, NORM_ROLE) or ""
        return self._needle in norm


class SearchableComboBox(QComboBox):
    """Combo de socio: filtra al escribir Y funciona como desplegable normal.

    Diseño (por qué así): el combo usa su modelo COMPLETO sin filtrar, de modo
    que la flecha despliega la lista entera como un QComboBox de toda la vida.
    El filtrado al escribir vive en un QCompleter con un proxy propio: su popup
    no roba el teclado (a diferencia del popup nativo), así que se puede seguir
    tecleando y la lista se refina en vivo, tolerante a mayúsculas y tildes.

    Es un reemplazo directo de un QComboBox normal para el uso que hacen los
    formularios: `addItem(texto, userData=...)`, `currentData()`, `clear()`,
    `count()`, `itemData(i)`, `setCurrentIndex(i)`.

    Añade la señal `selectionCommitted`, que se emite SOLO cuando el usuario
    elige un ítem (del buscador o del desplegable), no en cambios programáticos.
    Se usa para el auto-"Recibí de".
    """

    selectionCommitted = Signal()

    def __init__(self, parent=None, placeholder_text="Escribe para buscar…"):
        super().__init__(parent)
        self._source = QStandardItemModel(self)

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setFocusPolicy(Qt.StrongFocus)
        super().setModel(self._source)  # lista completa: el desplegable nativo no se filtra
        self.setView(QListView(self))
        self.setMaxVisibleItems(12)

        # Proxy SOLO para el buscador (el modelo del combo queda intacto).
        self._proxy = _AccentInsensitiveProxy(self)
        self._proxy.setSourceModel(self._source)

        self._completer = QCompleter(self._proxy, self)
        # Unfiltered: el completer no filtra por prefijo; muestra el proxy tal
        # cual (que ya filtra por "contiene", sin tildes).
        self._completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._completer.setMaxVisibleItems(12)
        popup = QListView()
        popup.setStyleSheet(
            "QListView { background: #ffffff; border: 1px solid #cbd5e1;"
            " font-size: 16px; padding: 4px; outline: none; }"
            "QListView::item { min-height: 30px; padding: 4px 8px; }"
            f"QListView::item:selected {{ background: {PRIMARY_COLOR}; color: white; }}"
        )
        self._completer.setPopup(popup)
        self.setCompleter(self._completer)

        self._committed_row = -1   # fila (modelo fuente) de la selección válida
        self._emit_guard = False   # evita doble selectionCommitted en la misma activación
        self._placeholder = placeholder_text

        self.lineEdit().setPlaceholderText(placeholder_text)
        self.lineEdit().installEventFilter(self)
        self.lineEdit().textEdited.connect(self._on_text_edited)
        self.lineEdit().returnPressed.connect(self._on_return_pressed)
        self._completer.activated[QModelIndex].connect(self._on_completer_activated)
        self.activated.connect(self._on_combo_activated)
        self.currentIndexChanged.connect(self._on_index_changed)

        # Empezar sin selección para que se vea el placeholder y se pueda buscar.
        super().setCurrentIndex(-1)

    # ------------------------------------------------------------------ API drop-in
    def addItem(self, text, userData=None):
        item = QStandardItem(str(text))
        item.setEditable(False)
        item.setData(userData, Qt.UserRole)
        item.setData(strip_accents(text), NORM_ROLE)
        self._source.appendRow(item)

    def clear(self):
        self._proxy.reset_needle()
        self._source.clear()
        self._committed_row = -1
        if self.lineEdit():
            self.lineEdit().clear()

    def populate_socios(self, socios):
        """Conveniencia: llena el combo con dicts de socio.

        Si ya había un socio seleccionado y sigue en la lista nueva, se
        mantiene seleccionado (por ejemplo al refrescar el formulario al
        navegar de vuelta a la página, para no perder el "Recibí de" de un
        recibo a medio llenar). Si no había selección o el socio ya no
        existe, queda sin selección como antes.
        """
        previous = self.currentData()
        prev_id = previous.get("id") if previous else None
        self.clear()
        for socio in socios:
            self.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)
        if prev_id is None or not self.set_socio_by_id(prev_id):
            self.setCurrentIndex(-1)

    def currentData(self, role=Qt.UserRole):
        # Nos apoyamos en la fila comprometida (independiente del texto a medias).
        if 0 <= self._committed_row < self._source.rowCount():
            return self._source.item(self._committed_row).data(role)
        return None

    def currentText(self):
        if 0 <= self._committed_row < self._source.rowCount():
            return self._source.item(self._committed_row).text()
        return ""

    def setCurrentIndex(self, index):
        """`index` es una fila del modelo fuente (el modelo del combo es el fuente)."""
        self._proxy.reset_needle()
        if index is None or index < 0:
            self._committed_row = -1
            super().setCurrentIndex(-1)
            if self.lineEdit():
                self.lineEdit().clear()
            return
        self._commit_source_row(index)

    def set_socio_by_id(self, socio_id) -> bool:
        """Selecciona (sin emitir selectionCommitted) el socio con ese id. Programático."""
        for r in range(self._source.rowCount()):
            data = self._source.item(r).data(Qt.UserRole)
            if data and data.get("id") == socio_id:
                self._commit_source_row(r)
                return True
        return False

    # ------------------------------------------------------------------ internos
    def _commit_source_row(self, source_row):
        self._proxy.reset_needle()
        self._committed_row = source_row
        super().setCurrentIndex(source_row)
        if self.lineEdit():
            self.lineEdit().setText(self._source.item(source_row).text())

    def _commit_user(self, source_row):
        """Commit disparado por el usuario. El guard evita emitir dos veces si
        Qt y el completer reportan la misma activación por caminos distintos."""
        if source_row is None or source_row < 0:
            return
        self._commit_source_row(source_row)
        if not self._emit_guard:
            self._emit_guard = True
            QTimer.singleShot(0, lambda: setattr(self, "_emit_guard", False))
            self.selectionCommitted.emit()

    def _on_text_edited(self, text):
        # El QLineEdit ya se encarga de mostrar el popup del completer; aquí
        # solo actualizamos el filtro.
        self._proxy.set_needle(text)

    def _on_return_pressed(self):
        # Enter con el filtro activo elige la primera coincidencia visible
        # (flujo rápido de teclado: "harv" + Enter).
        if self._proxy._needle and self._proxy.rowCount() > 0:
            src_row = self._proxy.mapToSource(self._proxy.index(0, 0)).row()
            self._commit_user(src_row)

    def _on_completer_activated(self, index):
        # `index` pertenece al completionModel del completer: mapear dos veces
        # hasta el modelo fuente (soporta nombres duplicados, no usa findText).
        proxy_idx = self._completer.completionModel().mapToSource(index)
        src_idx = self._proxy.mapToSource(proxy_idx)
        if src_idx.isValid():
            self._commit_user(src_idx.row())

    def _on_combo_activated(self, row):
        # El usuario eligió del desplegable nativo (modelo = fuente, sin mapear).
        self._commit_user(row)

    def _on_index_changed(self, row):
        # Mantener la fila comprometida al día en cambios de índice legítimos
        # (navegación con flechas, activaciones internas de Qt).
        if row >= 0:
            self._committed_row = row

    def showPopup(self):
        # Al abrir el desplegable nativo, cerrar el del buscador y limpiar filtro.
        self._completer.popup().hide()
        self._proxy.reset_needle()
        super().showPopup()

    def eventFilter(self, obj, event):
        if obj is self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            # Tras el clic: mostrar la lista completa en el popup del buscador
            # (no el nativo: este no roba el teclado y deja seguir escribiendo),
            # y dejar el texto seleccionado para que teclear lo reemplace.
            QTimer.singleShot(0, self._abrir_buscador)
        elif obj is self.lineEdit() and event.type() == QEvent.FocusOut:
            # Si dejó texto a medias sin elegir, restauramos la última selección.
            self._restore_committed()
        return super().eventFilter(obj, event)

    def _abrir_buscador(self):
        self._proxy.reset_needle()
        if self._committed_row >= 0 and self.lineEdit().text():
            self.lineEdit().selectAll()
        popup = self._completer.popup()
        popup.setMinimumWidth(self.width())
        self._completer.complete()

    def _restore_committed(self):
        self._proxy.reset_needle()
        if 0 <= self._committed_row < self._source.rowCount():
            super().setCurrentIndex(self._committed_row)
            if self.lineEdit():
                self.lineEdit().setText(self._source.item(self._committed_row).text())
        else:
            super().setCurrentIndex(-1)
            if self.lineEdit():
                self.lineEdit().clear()

    def wheelEvent(self, event):
        event.ignore()
