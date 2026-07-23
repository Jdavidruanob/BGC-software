import unicodedata

from PySide6.QtWidgets import QComboBox, QListView
from PySide6.QtCore import Qt, QSortFilterProxyModel, QEvent, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

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
    """Combo de socio buscable: escribir para filtrar, tolerante a mayúsculas y tildes.

    Es un reemplazo directo de un QComboBox normal para el uso que hacen los
    formularios: `addItem(texto, userData=...)`, `currentData()`, `clear()`,
    `count()`, `itemData(i)`, `setCurrentIndex(i)`.

    Añade la señal `selectionCommitted`, que se emite SOLO cuando el usuario elige
    un ítem del desplegable (no en cambios programáticos). Se usa para el
    auto-"Recibí de".
    """

    selectionCommitted = Signal()

    def __init__(self, parent=None, placeholder_text="Escribe para buscar…"):
        super().__init__(parent)
        self._source = QStandardItemModel(self)
        self._proxy = _AccentInsensitiveProxy(self)
        self._proxy.setSourceModel(self._source)
        self.setModel(self._proxy)
        self.setModelColumn(0)

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setView(QListView(self))
        # Desactivamos el autocompletado nativo: filtramos nosotros con el proxy.
        self.setCompleter(None)

        self._committed_row = -1  # fila (en el modelo fuente) de la selección válida
        self._placeholder = placeholder_text

        self.lineEdit().setPlaceholderText(placeholder_text)
        self.lineEdit().installEventFilter(self)
        self.lineEdit().textEdited.connect(self._on_text_edited)
        self.activated.connect(self._on_user_activated)
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
        """Conveniencia: llena el combo con dicts de socio y lo deja sin selección."""
        self.clear()
        for socio in socios:
            self.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)
        self.setCurrentIndex(-1)

    def currentData(self, role=Qt.UserRole):
        # Nos apoyamos en la fila comprometida (independiente del estado del filtro).
        if 0 <= self._committed_row < self._source.rowCount():
            return self._source.item(self._committed_row).data(role)
        return None

    def currentText(self):
        if 0 <= self._committed_row < self._source.rowCount():
            return self._source.item(self._committed_row).text()
        return ""

    def setCurrentIndex(self, index):
        """`index` es una fila del modelo (con el filtro vacío coincide con la fuente)."""
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
        proxy_idx = self._proxy.mapFromSource(self._source.index(source_row, 0))
        super().setCurrentIndex(proxy_idx.row())
        if self.lineEdit():
            self.lineEdit().setText(self._source.item(source_row).text())

    def _on_text_edited(self, text):
        self._proxy.set_needle(text)
        if not self.view().isVisible():
            self.showPopup()

    def _on_user_activated(self, proxy_row):
        # El usuario eligió un ítem del desplegable (filtrado).
        src_row = self._proxy.mapToSource(self._proxy.index(proxy_row, 0)).row()
        self._commit_source_row(src_row)
        self.selectionCommitted.emit()

    def _on_index_changed(self, proxy_row):
        # Mantener _committed_row al día cuando el índice cambia sin filtro activo.
        if not self._proxy._needle and proxy_row >= 0:
            src_row = self._proxy.mapToSource(self._proxy.index(proxy_row, 0)).row()
            if src_row >= 0:
                self._committed_row = src_row

    def eventFilter(self, obj, event):
        if obj is self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                # Al hacer clic, abrir el desplegable con la lista completa.
                self._proxy.reset_needle()
                self.lineEdit().clear()
                self.showPopup()
                return True
            if event.type() == QEvent.FocusOut:
                # Si dejó texto a medias sin elegir, restauramos la última selección.
                self._restore_committed()
        return super().eventFilter(obj, event)

    def _restore_committed(self):
        self._proxy.reset_needle()
        if 0 <= self._committed_row < self._source.rowCount():
            proxy_idx = self._proxy.mapFromSource(self._source.index(self._committed_row, 0))
            super().setCurrentIndex(proxy_idx.row())
            if self.lineEdit():
                self.lineEdit().setText(self._source.item(self._committed_row).text())
        else:
            super().setCurrentIndex(-1)
            if self.lineEdit():
                self.lineEdit().clear()

    def wheelEvent(self, event):
        event.ignore()
