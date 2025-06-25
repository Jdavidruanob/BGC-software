from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os

from .widgets.member_card import MemberCard
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR
from views.main_window import load_svg_icon
from views.widgets.new_member_dialog import NewMemberDialog



class MembersPage(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager  # Guardamos referencia a la base de datos

        main_layout = QVBoxLayout()

        # --- Encabezado: Título + Botón "Nuevo Socio"
        header_layout = QHBoxLayout()

        title = QLabel("Socios")
        title.setObjectName("Title-members")
        header_layout.addWidget(title)

        header_layout.addStretch()

        new_btn = QPushButton("  Nuevo Socio")
        new_btn.setObjectName("newMemberButton")
        new_btn.setFixedHeight(35)
        new_btn.setIconSize(QSize(18, 18))
        new_btn.setIcon(load_svg_icon("assets/icons/users-plus.svg"))
        new_btn.clicked.connect(self.open_new_member_dialog)
        header_layout.addWidget(new_btn)

        main_layout.addLayout(header_layout)

        # --- Barra de búsqueda
        search_box = QLineEdit()
        search_box.setObjectName("searchBox-members")
        search_box.setPlaceholderText("🔍 Buscar socio por nombre...")
        search_box.setFixedHeight(35)
        main_layout.addWidget(search_box)

        # --- Área de tarjetas con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        grid = QGridLayout()

        # 🔄 Cargar socios desde la base de datos
        socios = self.db_manager.get_all_members()

        for i, (name, photo, info) in enumerate(socios):
            card = MemberCard(name, photo, info)
            grid.addWidget(card, i // 4, i % 4)

        content_widget.setLayout(grid)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self.load_styles()
        self.setLayout(main_layout)

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
            cc, name, phone, photo = dialog.get_data()
            if name and cc:
                self.db_manager.add_member(cc, name, phone, photo)
                self.refresh_members()

    def refresh_members(self):
        # Elimina y reconstruye las tarjetas
        scroll = self.findChild(QScrollArea)
        if scroll:
            content_widget = QWidget()
            grid = QGridLayout()

            socios = self.db_manager.get_all_members()
            for i, (name, photo, info) in enumerate(socios):
                card = MemberCard(name, photo, info)
                grid.addWidget(card, i // 4, i % 4)

            content_widget.setLayout(grid)
            scroll.setWidget(content_widget)


