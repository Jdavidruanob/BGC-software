import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap

from config import (
    load_styles, load_svg_icon, format_miles_colombian_int,
    STYLES_DIR, ASSETS_DIR,
)
from views.widgets.new_member_dialog import NewMemberDialog
from views.member_detail_page import MemberDetailPage
from views.widgets.comboBox_custom import strip_accents
from utils.message_boxes import show_success, show_error, show_warning

DEFAULT_PHOTO = os.path.join(ASSETS_DIR, "images", "default_user.png")


class _NumericItem(QTableWidgetItem):
    """Ítem de tabla que ordena por un valor numérico (no por texto)."""

    def __init__(self, text, value):
        super().__init__(text)
        self._value = value
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def __lt__(self, other):
        try:
            return self._value < other._value
        except AttributeError:
            return super().__lt__(other)


class MembersPage(QWidget):
    """Sección de socios estilo POS: tabla con saldo, créditos y acciones
    (ver, editar, eliminar), búsqueda tolerante a tildes y orden por columnas."""

    COL_FOTO, COL_NOMBRE, COL_SALDO, COL_CREDITOS, COL_ACCIONES = range(5)

    def __init__(self, db_manager, main_window):
        super().__init__()
        self.db_manager = db_manager
        self.main_window = main_window
        self._all_members = []   # lista completa de dicts (para filtrar en memoria)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(80, 20, 80, 20)
        main_layout.setSpacing(16)

        # --- Barra superior: Nuevo socio + búsqueda ---
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        new_btn = QPushButton("  Nuevo Socio")
        new_btn.setObjectName("newMemberButton")
        new_btn.setFixedHeight(45)
        new_btn.setIconSize(QSize(18, 18))
        new_btn.setIcon(load_svg_icon("icons/users-plus.svg"))
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self.open_new_member_dialog)
        top_bar.addWidget(new_btn)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox-members")
        self.search_box.setPlaceholderText(" Buscar socio por nombre o apellido")
        self.search_box.textChanged.connect(self._render_filtered)
        search_action = QAction(load_svg_icon("icons/search.svg"), "", self.search_box)
        self.search_box.addAction(search_action, QLineEdit.LeadingPosition)
        top_bar.addWidget(self.search_box, 1)

        main_layout.addLayout(top_bar)

        # --- Tabla POS ---
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("membersTable")
        self.table.setHorizontalHeaderLabels(["", "Socio", "Saldo de aportes", "Créditos", "Acciones"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_FOTO, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_NOMBRE, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_SALDO, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_CREDITOS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_ACCIONES, QHeaderView.Fixed)
        self.table.setColumnWidth(self.COL_FOTO, 56)
        self.table.setColumnWidth(self.COL_ACCIONES, 150)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        qss_path = os.path.join(STYLES_DIR, "members_page.qss")
        load_styles(self, qss_path)

        self.refresh_members()

    # ------------------------------------------------------------------ datos
    def refresh_members(self):
        """Refresca la lista completa de socios desde la base y redibuja la tabla."""
        try:
            self._all_members = self.db_manager.get_all_members_full()
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")
            self._all_members = []
        self._render_filtered()

    def _render_filtered(self):
        needle = strip_accents(self.search_box.text())
        if needle:
            filtrados = [
                m for m in self._all_members
                if needle in strip_accents(f"{m['nombres']} {m['apellidos']}")
            ]
        else:
            filtrados = list(self._all_members)
        self._render_rows(filtrados)

    def _render_rows(self, members):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(members))
        for row, m in enumerate(members):
            member_id = m["id"]
            nombre = f"{m['nombres']} {m['apellidos']}"
            saldo = m.get("saldo") or 0
            creditos = m.get("creditos") or 0

            # Foto (miniatura). NOTA: hoy se lee de photo_path; cuando la API
            # agregue la columna socios.foto (BYTEA) se leerá de ahí.
            foto_item = QTableWidgetItem()
            foto_item.setIcon(QIcon(self._thumbnail(m.get("photo_path"))))
            foto_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            foto_item.setData(Qt.UserRole, member_id)
            self.table.setItem(row, self.COL_FOTO, foto_item)

            nombre_item = QTableWidgetItem(nombre)
            nombre_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            nombre_item.setData(Qt.UserRole, member_id)
            self.table.setItem(row, self.COL_NOMBRE, nombre_item)

            saldo_item = _NumericItem(f"${format_miles_colombian_int(saldo)}", saldo)
            saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, self.COL_SALDO, saldo_item)

            cred_item = _NumericItem(str(creditos), creditos)
            cred_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_CREDITOS, cred_item)

            self.table.setCellWidget(row, self.COL_ACCIONES,
                                     self._build_actions(member_id, nombre))
        self.table.setSortingEnabled(True)

    def _thumbnail(self, photo_path, size=40):
        path = photo_path if (photo_path and os.path.exists(photo_path)) else DEFAULT_PHOTO
        pm = QPixmap(path)
        if pm.isNull():
            pm = QPixmap(DEFAULT_PHOTO)
        return pm.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    def _build_actions(self, member_id, nombre):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(6)

        def _btn(icon, tip, obj_name, slot):
            b = QPushButton()
            b.setIcon(load_svg_icon(icon))
            b.setIconSize(QSize(18, 18))
            b.setFixedSize(32, 32)
            b.setToolTip(tip)
            b.setObjectName(obj_name)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            return b

        lay.addWidget(_btn("icons/library.svg", "Ver socio y créditos", "posVerButton",
                           lambda: self.open_member_detail(member_id)))
        lay.addWidget(_btn("icons/edit.svg", "Editar socio", "posEditButton",
                           lambda: self.on_edit_member(member_id)))
        lay.addWidget(_btn("icons/trash.svg", "Eliminar socio", "posDeleteButton",
                           lambda: self.on_delete_member(member_id, nombre)))
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ acciones
    def open_new_member_dialog(self):
        dialog = NewMemberDialog(self)
        if dialog.exec():
            nombres, apellidos, phone, photo, saldo = dialog.get_data()
            if nombres and apellidos:
                self.db_manager.add_member(nombres, apellidos, phone, photo, saldo)
                show_success(self, " ", "Socio creado exitosamente.")
                self.refresh_members()

    def on_edit_member(self, member_id):
        member = self.db_manager.get_member_by_id(member_id)
        if not member:
            show_error(self, "Error", "No se pudo cargar la información del socio.")
            return
        dialog = NewMemberDialog(self)
        dialog.setWindowTitle("Editar Socio")
        dialog.first_name_input.setText(member["nombres"])
        dialog.last_name_input.setText(member["apellidos"])
        dialog.phone_input.setText(member["celular"] or "")
        dialog.salde_input.setText(
            format_miles_colombian_int(member["saldo"]) if member["saldo"] is not None else ""
        )
        dialog.photo_input.setText(member["photo_path"] or "")
        btn = dialog.findChild(QPushButton, "CreateMemberButton")
        if btn:
            btn.setText("Guardar cambios")

        if dialog.exec():
            nombres, apellidos, phone, photo, saldo = dialog.get_data()
            if nombres and apellidos:
                if self.db_manager.update_member(member_id, nombres, apellidos, phone, photo, saldo):
                    show_success(self, "Actualizado", "Socio actualizado correctamente.")
                    self.refresh_members()
                else:
                    show_error(self, "Error", "No se pudo actualizar el socio.")

    def on_delete_member(self, member_id, nombre):
        reply = show_warning(
            self, "Confirmar eliminación",
            f"¿Estás seguro de eliminar a {nombre}? Esta acción no se puede deshacer.",
            ask_confirmation=True,
        )
        if reply != QMessageBox.Yes:
            return

        # Blindaje: no eliminar socios con historial (créditos, recibos o movimientos),
        # para no dejar la base en estado inconsistente.
        hist = self.db_manager.member_history_counts(member_id)
        if hist["creditos"] or hist["recibos"] or hist["movimientos"]:
            show_error(
                self, "No se puede eliminar",
                f"{nombre} tiene historial y no se puede eliminar:\n\n"
                f"• Créditos: {hist['creditos']}\n"
                f"• Recibos: {hist['recibos']}\n"
                f"• Movimientos: {hist['movimientos']}\n\n"
                "Eliminarlo descuadraría la base. Solo se pueden eliminar socios sin historial.",
            )
            return

        if self.db_manager.delete_member(member_id):
            show_success(self, "Eliminado", "Socio eliminado correctamente.")
            self.refresh_members()
        else:
            show_error(self, "Error", "No se pudo eliminar el socio.")

    def open_member_detail(self, member_id):
        view_name = f"member_detail_{member_id}"
        if view_name not in self.main_window.views:
            detail_view = MemberDetailPage(self.db_manager, member_id, self.main_window)
            self.main_window.add_view(view_name, detail_view)
        self.main_window.show_view(view_name)

    def _on_row_double_clicked(self, index):
        item = self.table.item(index.row(), self.COL_NOMBRE)
        if item is not None:
            member_id = item.data(Qt.UserRole)
            if member_id is not None:
                self.open_member_detail(member_id)

    # ------------------------------------------------------------------ compat
    def filter_members(self, text):
        """Compatibilidad: el filtrado real lo hace la barra de búsqueda en memoria."""
        self._render_filtered()

    def update_member_cards(self, members):
        """Compatibilidad con llamadas antiguas: redibuja desde la lista completa."""
        self.refresh_members()

    def refresh_view(self):
        print("🔁 Refrescando vista members")
        self.refresh_members()
