from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction
import os

from .widgets.member_card import MemberCard
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR
from views.main_window import load_svg_icon
from views.widgets.new_member_dialog import NewMemberDialog



class MembersPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager  # Guardamos referencia a la base de datos

        main_layout = QVBoxLayout() # Layout principal

        # --- Encabezado: Título + Botón "Nuevo Socio"
        header_layout = QHBoxLayout() 
        header_layout.setContentsMargins(80, 20, 80, 30)

        title = QLabel("Socios")
        title.setObjectName("title-members")
        header_layout.addWidget(title)

        header_layout.addStretch()

        new_btn = QPushButton("  Nuevo Socio")
        new_btn.setObjectName("newMemberButton")
        new_btn.setFixedHeight(45)
        new_btn.setIconSize(QSize(18, 18))
        new_btn.setIcon(load_svg_icon("assets/icons/users-plus.svg"))
        new_btn.clicked.connect(self.open_new_member_dialog)
        header_layout.addWidget(new_btn)

        main_layout.addLayout(header_layout)

        # --- Barra de búsqueda con márgenes laterales
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(80, 0, 80, 30)  # Aplica el margen aquí

        search_box = QLineEdit()
        search_box.setObjectName("searchBox-members")
        search_box.setPlaceholderText(" Buscar socio por nombre")

        # Ícono dentro del QLineEdit
        search_icon = load_svg_icon("assets/icons/search.svg")
        search_action = QAction(search_icon, "", search_box)
        search_box.addAction(search_action, QLineEdit.LeadingPosition)

        search_layout.addWidget(search_box)
        main_layout.addLayout(search_layout)

        # --- Área de tarjetas con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        grid = QGridLayout()

        # 🔄 Cargar socios desde la base de datos
        socios = self.db_manager.get_all_members()

        for i, (member_id, name, photo, info) in enumerate(socios):
            card = MemberCard(member_id, name, photo, info)
            grid.addWidget(card, i // 4, i % 4)

        grid.setObjectName("gridLayout-members")
        grid.setContentsMargins(80, 0, 80, 0)

        content_widget.setLayout(grid)
        content_widget.setObjectName("contentWidget-members")
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)
        self.load_styles()

    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "members_page.qss")
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

    def open_new_member_dialog(self):
        dialog = NewMemberDialog(self)
        if dialog.exec():
            cc, nombres, apellidos, phone, photo = dialog.get_data()
            if nombres and apellidos and cc:
                self.db_manager.add_member(cc, nombres, apellidos, phone, photo)
                self.refresh_members()


    def refresh_members(self):
        # Elimina y reconstruye las tarjetas
        scroll = self.findChild(QScrollArea)
        if scroll:
            content_widget = QWidget()
            grid = QGridLayout()

            socios = self.db_manager.get_all_members()
            for i, (member_id, name, photo, info) in enumerate(socios):
                card = MemberCard(member_id, name, photo, info)
                grid.addWidget(card, i // 4, i % 4) # Adjust the grid layout as needed
            content_widget.setLayout(grid)
            scroll.setWidget(content_widget)


