# constants

PRIMARY_COLOR = "#1a365d"     # Azul oscuro (fondo navbar)
SECONDARY_COLOR = "#8C5B2F"   # Marrón (hover y botón activo)
TEXT_COLOR = "#FFFFFF"        # Texto blanco
#e3e9f1 bordes
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

def format_miles_colombian_int(value: int) -> str:
    """
    Recibe un entero (100000) y devuelve '100.000'.
    """
    return f"{value:,}".replace(",", ".")

def parse_miles_colombian(text: str) -> int:
    """
    Recibe un texto con puntos (p.ej. '123.456') 
    y devuelve el entero 123456.
    Cualquier caracter no dígito se elimina.
    """
    clean = "".join(ch for ch in text if ch.isdigit())
    return int(clean) if clean else 0
