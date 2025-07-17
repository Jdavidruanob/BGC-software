from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt, QSize
import os

from config import load_svg_icon, load_styles, format_miles_colombian_int
from views.widgets.message_boxes import show_warning, show_success, show_error, show_info
from config import PRIMARY_COLOR
from views.widgets.new_member_dialog import NewMemberDialog
from views.widgets.credit_card_widget import CreditCardWidget
from views.liquidation_page import CreditLiquidationPage

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
        main_layout.setContentsMargins(80, 30, 80, 30)
        main_layout.setSpacing(20) 

        header_layout = QHBoxLayout()

        # Botón de regreso
        back_btn = QPushButton("←")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(lambda: self.main_window.show_view("members"))
        header_layout.addWidget(back_btn)

        # Título justo a la derecha del botón
        title = QLabel("Perfil de Socio")
        title.setObjectName("title-member-detail")
        header_layout.addWidget(title)
        header_layout.addStretch()  # Añade espacio entre el título y el botón

        main_layout.addLayout(header_layout)

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(40)

        self.left_panel = self.create_left_panel()
        self.right_panel = self.create_right_panel()

        self.content_layout.addWidget(self.left_panel, 1)
        self.content_layout.addWidget(self.right_panel, 2)

        main_layout.addLayout(self.content_layout)
        self.setLayout(main_layout)

        # Cargar estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "member_detail_page.qss")
        load_styles(self, qss_path)

    def create_left_panel(self):
        """Crea el panel izquierdo con la información del socio."""

        member = self.db_manager.get_member_by_id(self.member_id)
        if not member:
            show_error(self, "Error", "No se pudo cargar la información del socio.")
            return QWidget()

        widget = QFrame()
        widget.setObjectName("leftPanel")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(12)

        # Foto circular con margen
        avatar_container = QWidget()
        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.setContentsMargins(0, 10, 0, 5)
        #avatar_container.setStyleSheet("background-color: red;")  # Fondo transparente
        avatar_container.setLayout(avatar_layout)

        photo_label = QLabel()
        photo_label.setFixedSize(175, 175)
        photo_label.setAlignment(Qt.AlignCenter)
        photo_label.setScaledContents(True)

        photo_path = member["photo_path"] or "assets/images/default_user.png"
        if not os.path.exists(photo_path):
            photo_path = "assets/images/default_user.png"

        avatar_pixmap = self.create_rounded_avatar(photo_path, size=175, border=3, border_color=PRIMARY_COLOR)
        photo_label.setPixmap(avatar_pixmap)

        avatar_layout.addWidget(photo_label)

        # Nombre y número del socio
        name_label = QLabel(f"{member['nombres']} {member['apellidos']}")
        name_label.setObjectName("memberName")
        name_label.setAlignment(Qt.AlignCenter)

        id_label = QLabel(f"Socio #{member['id']}")
        id_label.setAlignment(Qt.AlignCenter)
        id_label.setObjectName("memberId")

        #data_labels = ["Telefono:", "Fecha de ingreso:", "Saldo de aportes:"]

        data_labels = [
            ("Teléfono:", member["celular"]),   
            ("Fecha de ingreso:", member["created_at"][:10]),
            ("Saldo de aportes:", f"${format_miles_colombian_int(member['saldo'])}")
        ]

        layout.addWidget(avatar_container)
        layout.addWidget(name_label)
        layout.addWidget(id_label)
        
        for label, value in data_labels:
            row_widget = QWidget()
            row = QHBoxLayout()
            row.setObjectName("memberInfoRow")
            row.setContentsMargins(0, 5, 0, 5)  # Márgenes entre filas

            label_widget = QLabel(label)
            label_widget.setObjectName("memberInfoLabel")
            value_widget = QLabel(value)
            value_widget.setObjectName("memberInfoValue")

            row.addWidget(label_widget, alignment=Qt.AlignLeft)
            row.addStretch()
            row.addWidget(value_widget, alignment=Qt.AlignRight)

            row_widget.setLayout(row)
            row_widget.setObjectName("memberInfoRowWidget")
            layout.addWidget(row_widget)

        # Botones
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 20, 0, 0)  # Márgenes para los botones
        edit_btn = QPushButton("  Editar")
        edit_btn.setObjectName("editMemberButton")
        edit_btn.setIcon(load_svg_icon("assets/icons/edit.svg"))
        edit_btn.clicked.connect(self.on_edit_member)

        delete_btn = QPushButton("  Eliminar")
        delete_btn.setObjectName("deleteMemberButton")
        delete_btn.setIcon(load_svg_icon("assets/icons/trash.svg"))
        delete_btn.clicked.connect(self.on_delete_member)              
        button_row.addWidget(edit_btn)
        button_row.addWidget(delete_btn)

        layout.addLayout(button_row)
        widget.setLayout(layout)

        return widget

    def create_rounded_avatar(self, photo_path, size=175, border=3, border_color="#153A66"):
        inner_diameter = size - 2 * border
        pixmap = QPixmap(photo_path).scaled(
            inner_diameter, inner_diameter,
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        final = QPixmap(size, size)
        final.fill(Qt.transparent)

        painter = QPainter(final)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        pen = QPen(QColor(border_color))
        pen.setWidth(border)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        offset = int(border // 2)
        diameter = size - border
        painter.drawEllipse(offset, offset, diameter, diameter)

        path = QPainterPath()
        path.addEllipse(border, border, inner_diameter, inner_diameter)
        painter.setClipPath(path)
        painter.drawPixmap(border, border, pixmap)
        painter.end()

        return final

    def on_edit_member(self):
        member = self.db_manager.get_member_by_id(self.member_id)
        if not member:
            show_error(self, "Error", "No se pudo cargar la información del socio.")
            return

        # Abre el diálogo con los datos actuales
        dialog = NewMemberDialog(self)
        dialog.first_name_input.setText(member["nombres"])
        dialog.last_name_input.setText(member["apellidos"])
        dialog.cc_input.setText(member["cc"])
        dialog.phone_input.setText(member["celular"])
        dialog.salde_input.setText(str(member["saldo"]) if member["saldo"] is not None else "")
        dialog.photo_input.setText(member["photo_path"] or "")

        dialog.setWindowTitle("Editar Socio")
        dialog.findChild(QPushButton, "CreateMemberButton").setText("Guardar cambios")

        if dialog.exec():
            cc, nombres, apellidos, phone, photo, salde = dialog.get_data()
            if nombres and apellidos:
                if self.db_manager.update_member(self.member_id, nombres, apellidos, cc, phone, photo, salde):
                    show_success(self, "Actualizado", "Socio actualizado correctamente.")
                    # Elimina la vista de detalle en caché para este socio
                    view_name = f"member_detail_{self.member_id}"
                    if hasattr(self.main_window, "views") and view_name in self.main_window.views:
                        del self.main_window.views[view_name]
                    # Refresca la vista actual y la lista de socios
                    self.main_window.show_view("members")
                    if hasattr(self.main_window, "views") and "members" in self.main_window.views:
                        members_page = self.main_window.views["members"]
                        if hasattr(members_page, "refresh_members"):
                            members_page.refresh_members()
                else:
                    show_error(self, "Error", "No se pudo actualizar el socio.")

    def on_delete_member(self):
        reply = show_warning(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de que deseas eliminar este socio? Esta acción no se puede deshacer.",
            ask_confirmation=True
        )
        if reply == QMessageBox.Yes:
            if self.db_manager.delete_member(self.member_id):
                show_success(self, "Eliminado", "Socio eliminado correctamente.")
                # Refrescar la lista de socios en MembersPage
                if hasattr(self.main_window, "views") and "members" in self.main_window.views:
                    members_page = self.main_window.views["members"]
                    if hasattr(members_page, "refresh_members"):
                        members_page.refresh_members()
                self.main_window.show_view("members")
            else:
                show_error(self, "Error", "No se pudo eliminar el socio.")

    def create_right_panel(self):
        """Crea el panel derecho con las tarjetas de créditos activos del socio."""

        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        credits = self.db_manager.get_active_credits_by_member(self.member_id)

        if credits:
            for credit in credits:
                credit_widget = CreditCardWidget(credit)
                credit_widget.clicked.connect(lambda _, letra=credit["letra"]: self.on_credit_card_clicked(letra))
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

    def on_credit_card_clicked(self, letra):
        credit = self.db_manager.get_credit_by_letra(letra)
        if not credit:
            show_error(self, "Error", "No se encontró el crédito.")
            return

        view_name = f"liquidation_credit_{letra}"
        if view_name not in self.main_window.views:
            liquidation_view = CreditLiquidationPage(credit, member_id = self.member_id, main_window=self.main_window, db_manager=self.db_manager)
            self.main_window.add_view(view_name, liquidation_view)
        self.main_window.show_view(view_name)

    def build_credit_card(self, credito):
        card = QFrame()
        card.setObjectName("CreditCard")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(15, 15, 15, 15)

        # Acceder usando claves del diccionario sqlite3.Row
        letra = credito["letra"]
        capital = credito["capital"]
        interes = credito["interes"]
        cuotas = credito["no_cuotas"]

        lbl_letra = QLabel(f"🆔 Crédito #{letra}")
        lbl_letra.setObjectName("creditCardTitle")

        lbl_capital = QLabel(f"💰 Capital: ${capital:,.0f}")
        lbl_capital.setObjectName("creditCardLabel")

        lbl_interes = QLabel(f"📈 Interés mensual: {interes * 100:.2f}%")
        lbl_interes.setObjectName("creditCardLabel")

        lbl_cuotas = QLabel(f"📅 Cuotas totales: {cuotas}")
        lbl_cuotas.setObjectName("creditCardLabel")

        layout.addWidget(lbl_letra)
        layout.addSpacing(5)
        layout.addWidget(lbl_capital)
        layout.addWidget(lbl_interes)
        layout.addWidget(lbl_cuotas)

        card.setLayout(layout)
        return card
    
    def refresh_view(self):
        """Refresca los paneles izquierdo y derecho al mostrarse."""
        print("🔁 Refrescando vista member_detail")
        # Eliminar widgets antiguos
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.takeAt(i).widget()
            if w:
                w.setParent(None)

        # Reconstruir paneles
        self.left_panel = self.create_left_panel()
        self.right_panel = self.create_right_panel()
        self.content_layout.addWidget(self.left_panel, 1)
        self.content_layout.addWidget(self.right_panel, 2)
