from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
import os
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR
from PySide6.QtGui import QPainterPath, QRegion

from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen

class MemberCard(QPushButton):  # ya estás usando QPushButton para que sea clickeable
    def __init__(self, member_id, name, photo_path, credit_info):
        super().__init__()
        self.member_id = member_id
        self.setObjectName("MemberCard")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Foto del socio
        self.photo_label = QLabel()
        self.photo_label.setObjectName("PhotoLabel")
        self.photo_label.setFixedSize(115, 115)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setScaledContents(True) # Esto ayuda a mantener centrado el contenido

        if not os.path.exists(photo_path) or not photo_path:
            photo_path = "assets/images/default_user.png"

        # Usa el método mejorado para crear el avatar circular con borde suave
        avatar_pixmap = self.create_rounded_avatar(photo_path, size=135, border=3, border_color=PRIMARY_COLOR)
        self.photo_label.setPixmap(avatar_pixmap)

        # Nombre
        self.name_label = QLabel(name)
        self.name_label.setObjectName("NameLabel")
        self.name_label.setAlignment(Qt.AlignCenter)

        # Info de crédito
        self.credit_label = QLabel(credit_info)
        self.credit_label.setObjectName("CreditLabel")
        self.credit_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.photo_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.credit_label)

        self.setLayout(layout)
        self.setFixedSize(325, 225)  # Tamaño fijo de la tarjeta
        self.load_styles()

        
    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "..", "..", "styles", "member_card.qss")
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

    def create_rounded_avatar(self, photo_path, size=135, border=3, border_color="#153A66"):
        # Cargar imagen y escalarla exactamente al círculo interior
        inner_diameter = size - 2 * border
        pixmap = QPixmap(photo_path).scaled(
            inner_diameter, inner_diameter,
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        # Crear pixmap final transparente
        final = QPixmap(size, size)
        final.fill(Qt.transparent)

        painter = QPainter(final)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Dibujar borde
        pen = QPen(QColor(border_color))
        pen.setWidth(border)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        offset = int(border / 2)
        diameter = size - border
        painter.drawEllipse(offset, offset, diameter, diameter)

        # Dibujar imagen circular centrada
        path = QPainterPath()
        path.addEllipse(border, border, inner_diameter, inner_diameter)
        painter.setClipPath(path)
        painter.drawPixmap(border, border, pixmap)
        painter.end()
        return final