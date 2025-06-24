# views/members_page.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit, QScrollArea
from PySide6.QtCore import Qt
from .widgets.member_card import MemberCard
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR
from views.main_window import load_svg_icon
class MembersPage(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()

        # Título
        title = QLabel("Socios")
        title.setObjectName("Title-members")
        main_layout.addWidget(title)

        # Top bar: búsqueda + botón
        top_bar = QHBoxLayout()
        top_bar.setObjectName("topBar-members")
        search_box = QLineEdit()
        search_box.setObjectName("searchBox-members")
        search_box.setPlaceholderText("🔍 Buscar socio por nombre...")
        search_box.setFixedHeight(35)

        new_btn = QPushButton("  Nuevo Socio")
        new_btn.setObjectName("newMemberButton")
        new_btn.setFixedHeight(35)
        new_btn.setIconSize(QSize(18, 18))
        new_btn.setIcon(load_svg_icon("assets/icons/users-plus.svg"))  # Asegúrate de tener el icono en la ruta correcta
        
          # Asegúrate de tener el icono en la ruta correcta
        top_bar.addWidget(search_box)
        top_bar.addStretch()
        top_bar.addWidget(new_btn)
        main_layout.addLayout(top_bar)

        # Área de tarjetas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        grid = QGridLayout()

        # Datos mock (esto se conectará a tu modelo después)
        socios = [
            ("Juan Pérez", "assets/photos/juan.png", "1 crédito activo"),
            ("María González", "assets/photos/maria.png", "2 créditos activos"),
            ("Carlos Rodríguez", "assets/photos/carlos.png", "Sin créditos activos"),
            ("Ana Martínez", "assets/photos/ana.png", "1 crédito activo"),
            ("Luis Torres", "assets/photos/luis.png", "1 crédito activo"),
            ("Carmen Sánchez", "assets/photos/carmen.png", "Sin créditos activos"),
            ("Roberto Díaz", "assets/photos/roberto.png", "1 crédito activo"),
            ("Elena Vargas", "assets/photos/elena.png", "Sin créditos activos"),
            ("Sofía López", "assets/photos/sofia.png", "2 créditos activos"),
            ("Miguel Fernández", "assets/photos/miguel.png", "1 crédito activo"),
            ("Laura Jiménez", "assets/photos/laura.png", "Sin créditos activos"),
            ("Andrés Ramírez", "assets/photos/andres.png", "1 crédito activo"),
            ("Patricia Morales", "assets/photos/patricia.png", "2 créditos activos"),
            ("Javier Herrera", "assets/photos/javier.png", "Sin créditos activos"),
            ("Lucía Castro", "assets/photos/lucia.png", "1 crédito activo")

        ]

        for i, (name, photo, info) in enumerate(socios):
            card = MemberCard(name, photo, info)
            grid.addWidget(card, i // 4, i % 4)

        content_widget.setLayout(grid)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self.load_styles()
        self.setLayout(main_layout)

    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "..",  "styles", "members_page.qss")
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
