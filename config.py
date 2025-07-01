# constants

PRIMARY_COLOR = "#153A66"     # Azul oscuro (fondo navbar)
SECONDARY_COLOR = "#8C5B2F"   # Marrón (hover y botón activo)
TEXT_COLOR = "#FFFFFF"        # Texto blanco

# functions globlaes

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QScrollArea
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

def load_styles(self, qss_path):
        try:
            with open(qss_path, "r") as f:
                qss = f.read() % {
                    "PRIMARY_COLOR": PRIMARY_COLOR,
                    "SECONDARY_COLOR": SECONDARY_COLOR,
                    "TEXT_COLOR": TEXT_COLOR
                }
                self.setStyleSheet(qss)
        except Exception as e:
            print(f"❌ Error cargando estilos de {qss_path}: {e}")


def load_svg_icon(path: str, size: QSize = QSize(24, 24)) -> QIcon:
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)