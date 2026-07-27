"""Layout que acomoda los widgets en fila y baja a la siguiente cuando no caben.

Se usa para la barra de operaciones de la pantalla de Inicio. Un `QHBoxLayout`
normal exige, como ancho mínimo, la SUMA de todos sus botones: al agregar una
operación más la ventana pasó a pedir más ancho que la pantalla y se salía del
monitor. Con este layout el mínimo es el del botón más ancho, así que la
ventana nunca se pasa por más operaciones que se agreguen: simplemente se
reparten en dos filas cuando no caben en una.

Es la implementación estándar de "flow layout" de Qt, traducida a PySide6.
"""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidget

ESPACIADO_POR_DEFECTO = 8


class FlowLayout(QLayout):
    def __init__(self, parent=None, margen=0, espaciado=ESPACIADO_POR_DEFECTO):
        super().__init__(parent)
        self._items = []
        self._espaciado = espaciado
        self.setContentsMargins(margen, margen, margen, margen)

    # --- API que QLayout exige implementar --------------------------------
    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    # --- Alto en función del ancho ----------------------------------------
    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, ancho):
        return self._acomodar(QRect(0, 0, ancho, 0), solo_medir=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._acomodar(rect, solo_medir=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        """El del ítem más ancho, NO la suma. Es lo que evita que la ventana
        crezca más allá de la pantalla."""
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    # --- Cálculo ----------------------------------------------------------
    def _acomodar(self, rect, solo_medir):
        m = self.contentsMargins()
        area = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y = area.x(), area.y()
        alto_fila = 0

        for item in self._items:
            medida = item.sizeHint()
            siguiente_x = x + medida.width() + self._espaciado
            # Si no cabe y ya hay algo en esta fila, se baja a la siguiente.
            if siguiente_x - self._espaciado > area.right() and alto_fila > 0:
                x = area.x()
                y = y + alto_fila + self._espaciado
                siguiente_x = x + medida.width() + self._espaciado
                alto_fila = 0

            if not solo_medir:
                item.setGeometry(QRect(QPoint(x, y), medida))

            x = siguiente_x
            alto_fila = max(alto_fila, medida.height())

        return y + alto_fila - rect.y() + m.bottom()


class FlowWidget(QWidget):
    """Contenedor para un `FlowLayout`.

    Hace falta porque el alto-según-ancho no se propaga solo: hay que declararlo
    en la política de tamaño del widget y reenviar `heightForWidth` al layout.
    Sin esto el contenedor reserva el alto de una sola fila y los botones de la
    segunda quedan cortados.
    """

    def __init__(self, parent=None, margenes=(20, 20, 20, 20), espaciado=ESPACIADO_POR_DEFECTO):
        super().__init__(parent)
        self._flow = FlowLayout(espaciado=espaciado)
        self._flow.setContentsMargins(*margenes)
        self.setLayout(self._flow)

        politica = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        politica.setHeightForWidth(True)
        self.setSizePolicy(politica)

    def addWidget(self, widget):
        self._flow.addWidget(widget)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, ancho):
        return self._flow.heightForWidth(ancho)

    def sizeHint(self):
        return self._flow.sizeHint()

    def minimumSizeHint(self):
        return self._flow.minimumSize()
