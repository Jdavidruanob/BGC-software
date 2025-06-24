from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class MemberCard(QWidget):
    def __init__(self, name, photo_path, credit_info):
        super().__init__()

        self.setObjectName("MemberCard")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Foto del socio
        self.photo_label = QLabel()
        self.photo_label.setObjectName("PhotoLabel")
        pixmap = QPixmap(photo_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.photo_label.setPixmap(pixmap)
        self.photo_label.setFixedSize(100, 100)
        self.photo_label.setAlignment(Qt.AlignCenter)

        # Nombre del socio
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
        self.setFixedSize(200, 180)

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
