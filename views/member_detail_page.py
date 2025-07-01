import os

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QScrollArea
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize

from views.main_window import load_svg_icon

class MemberDetailPage(QWidget):
    def __init__(self, db_manager, member_id, main_window):
        super().__init__()
        self.db_manager = db_manager
        self.member_id = member_id
        self.main_window = main_window  # ✅ Para volver o cambiar vista

        self.setObjectName("memberDetailPage")
        self.setMinimumSize(900, 600)
        self.setWindowTitle("Perfil de Socio")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # ✅ Botón de regreso
        back_btn = QPushButton("⟵ Volver")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(lambda: self.main_window.show_view("members"))
        back_btn.setFixedWidth(100)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Paneles izquierdo y derecho
        panel_layout = QHBoxLayout()
        panel_layout.setSpacing(40)

        self.left_panel = self.create_left_panel()
        self.right_panel = self.create_right_panel()

        panel_layout.addWidget(self.left_panel, 1)
        panel_layout.addWidget(self.right_panel, 2)

        main_layout.addLayout(panel_layout)
        self.setLayout(main_layout)

        self.load_styles()

    def create_left_panel(self):
        member = self.db_manager.get_member_by_id(self.member_id)
        if not member:
            QMessageBox.critical(self, "Error", "No se pudo cargar la información del socio.")
            return QWidget()

        widget = QFrame()
        widget.setObjectName("leftPanel")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)

        # Foto
        pixmap = QPixmap(member["photo_path"] or "assets/images/default_user.png")
        photo_label = QLabel()
        photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        photo_label.setAlignment(Qt.AlignCenter)

        # Nombre
        name_label = QLabel(f"{member['nombres']} {member['apellidos']}")
        name_label.setObjectName("memberName")
        name_label.setAlignment(Qt.AlignCenter)

        # Cédula y otros
        data_labels = [
            ("Socio ID:", str(member["id"])),
            ("Cédula:", member["cc"]),
            ("Teléfono:", member["celular"]),
            ("Fecha de ingreso:", member["created_at"][:10]),
            ("Saldo de aportes:", f"${member['saldo']:,}")
        ]

        layout.addWidget(photo_label)
        layout.addWidget(name_label)

        for label, value in data_labels:
            row = QLabel(f"<b>{label}</b> {value}")
            row.setObjectName("memberInfoRow")
            layout.addWidget(row)

        # Botones
        button_row = QHBoxLayout()
        edit_btn = QPushButton("  Editar")
        edit_btn.setIcon(load_svg_icon("assets/icons/edit.svg"))

        delete_btn = QPushButton("  Eliminar")
        delete_btn.setIcon(load_svg_icon("assets/icons/trash.svg"))
        delete_btn.setStyleSheet("background-color: #FEE2E2; color: #B91C1C;")

        button_row.addWidget(edit_btn)
        button_row.addWidget(delete_btn)

        layout.addLayout(button_row)
        widget.setLayout(layout)

        return widget

    def create_right_panel(self):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        credits = self.db_manager.get_active_credits_by_member(self.member_id)

        if credits:
            for credit in credits:
                credit_widget = self.build_credit_card(credit)
                layout.addWidget(credit_widget)
        else:
            no_credit_label = QLabel("Este socio no tiene créditos activos.")
            no_credit_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_credit_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(layout)
        scroll.setWidget(scroll_content)

        return scroll

    def build_credit_card(self, credit):
        letra = credit["letra"]
        capital = credit["capital"]
        cuotas = credit["no_cuotas"]

        card = QFrame()
        card.setObjectName("creditCard")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(6)

        title = QLabel(f"Crédito #{letra}")
        title.setObjectName("creditTitle")

        body = QLabel(f"Capital: ${capital:,}\nCuotas: {cuotas}")
        body.setObjectName("creditInfo")

        card.mousePressEvent = lambda e: self.on_credit_click(letra)

        layout.addWidget(title)
        layout.addWidget(body)
        card.setLayout(layout)
        return card

    def on_credit_click(self, letra):
        print(f"📄 Abrir detalle del crédito {letra}...")
        # Aquí puedes navegar a la vista del crédito usando self.main_window

    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "member_detail_page.qss")
        try:
            with open(qss_path, "r") as f:
                qss = f.read()
                self.setStyleSheet(qss)
        except Exception as e:
            print(f"❌ Error cargando estilos de {qss_path}: {e}")
