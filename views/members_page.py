import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

from .widgets.member_card import MemberCard
from config import load_styles, load_svg_icon
from views.widgets.new_member_dialog import NewMemberDialog
from views.member_detail_page import MemberDetailPage
from views.widgets.message_boxes import show_success, show_error, show_warning, show_info


class MembersPage(QWidget):
    def __init__(self, db_manager, main_window):
        super().__init__()
        self.db_manager = db_manager
        self.main_window = main_window

        main_layout = QVBoxLayout()

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

        # --- Barra de búsqueda
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(80, 0, 80, 30)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox-members")
        self.search_box.setPlaceholderText(" Buscar socio por nombre")
        self.search_box.textChanged.connect(self.filter_members)

        search_icon = load_svg_icon("assets/icons/search.svg")
        search_action = QAction(search_icon, "", self.search_box)
        self.search_box.addAction(search_action, QLineEdit.LeadingPosition)

        search_layout.addWidget(self.search_box)
        main_layout.addLayout(search_layout)

        # --- Área con scroll y tarjetas
        scroll = QScrollArea()
        scroll.setContentsMargins(80, 0, 80, 0)
        scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.cards_layout = QGridLayout()

        self.content_widget.setLayout(self.cards_layout)
        self.content_widget.setContentsMargins(80, 0, 80, 0)
        self.content_widget.setObjectName("contentWidget-members")
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout) 

        # cargar estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "members_page.qss")
        load_styles(self, qss_path)

        self.refresh_members()  # Cargar al iniciar

    def open_new_member_dialog(self):
        """ Abre el diálogo para crear un nuevo socio """
        dialog = NewMemberDialog(self)
        if dialog.exec():
            cc, nombres, apellidos, phone, photo, saldo = dialog.get_data()
            if nombres and apellidos:
                self.db_manager.add_member(cc, nombres, apellidos, phone, photo, saldo)
                show_success(self, " ", "Socio creado exitosamente.")
                self.refresh_members()

    def refresh_members(self):
        """ Refresca la lista de socios desde la base de datos """
        socios = self.db_manager.get_all_members()
        self.update_member_cards(socios)

    def update_member_cards(self, members):
        """ Actualiza las tarjetas de socios en la interfaz """
        # Limpiar layout
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Agregar nuevas tarjetas
        for i, (member_id, name, photo, info) in enumerate(members):
            card = MemberCard(member_id, name, photo, info)
            card.clicked.connect(lambda _, member_id=member_id: self.open_member_detail(member_id))
            self.cards_layout.addWidget(card, i // 4, i % 4)

    def filter_members(self, text):
        """ Filtra los socios por el texto ingresado en la barra de búsqueda """
        if text.strip() == "":
            socios = self.db_manager.get_all_members()
        else:
            socios = self.db_manager.search_members_by_name(text)
        self.update_member_cards(socios)

    def open_member_detail(self, member_id):
        """ Abre la vista de detalle del socio seleccionado """
        view_name = f"member_detail_{member_id}"
        if view_name not in self.main_window.views:
            detail_view = MemberDetailPage(self.db_manager, member_id, self.main_window)
            self.main_window.add_view(view_name, detail_view)
        self.main_window.show_view(view_name)
