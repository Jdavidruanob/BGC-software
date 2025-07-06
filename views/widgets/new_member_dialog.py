import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from config import load_styles, load_svg_icon, format_miles_colombian
from views.widgets.message_boxes import show_warning, show_success, show_error, show_info

DEFAULT_PHOTO = "assets/images/default_user.png"

class NewMemberDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Socio")
        self.setModal(True)
        self.setFixedSize(550, 650)
        self.setObjectName("NewMemberDialog")

        self.first_name_input = QLineEdit()
        self.first_name_input.setObjectName("InputField")

        self.last_name_input = QLineEdit()
        self.last_name_input.setObjectName("InputField")

        self.cc_input = QLineEdit()
        self.cc_input.setObjectName("InputField")

        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("InputField")

        self.salde_input = QLineEdit()
        self.salde_input.setObjectName("InputField")

        self.photo_input = QLineEdit()
        self.photo_input.setObjectName("InputField")
        self.salde_input.textChanged.connect(self.on_saldo_changed)

        photo_btn = QPushButton("Seleccionar imagen")
        photo_btn.setObjectName("PhotoButton")
        photo_btn.clicked.connect(self.select_photo)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        for label_text, widget in [
            ("Nombres:", self.first_name_input),
            ("Apellidos:", self.last_name_input),
            ("Cédula:", self.cc_input),
            ("Celular:", self.phone_input),
            ("Saldo:", self.salde_input),
            ("Foto (opcional):", None)
        ]:
            label = QLabel(label_text)
            label.setObjectName("FormLabel")
            layout.addWidget(label)
            if widget:
                layout.addWidget(widget)
            elif label_text.startswith("Foto"):
                photo_layout = QHBoxLayout()
                photo_layout.addWidget(self.photo_input)
                photo_layout.addWidget(photo_btn)
                layout.addLayout(photo_layout)

        create_btn = QPushButton("Crear socio")
        create_btn.setObjectName("CreateMemberButton")
        create_btn.clicked.connect(self.on_submit)
        layout.addWidget(create_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        qss_path = os.path.join(os.path.dirname(__file__), ".." , "..", "styles", "new_member_dialog.qss")
        load_styles(self, qss_path)

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            self.photo_input.setText(file_path)

    def on_submit(self):
        if not self.first_name_input.text().strip() or not self.last_name_input.text().strip():
            show_warning(self, "warning", "Por favor ingrese al menos un nombre y un apellido.")
            return
        # Puedes agregar más validaciones aquí si lo deseas
        self.accept()

    def get_data(self):
        nombres = self.first_name_input.text().strip()
        apellidos = self.last_name_input.text().strip()
        cc = self.cc_input.text().strip()
        phone = self.phone_input.text().strip()
        saldo = self.salde_input.text().strip() or "0"
        photo = self.photo_input.text().strip() or DEFAULT_PHOTO
        
        return (cc, nombres, apellidos, phone, photo, saldo)
    
    def on_saldo_changed(self, text):
        if not text:
            return
        cursor_pos = self.salde_input.cursorPosition()
        # Solo números
        clean = ''.join(c for c in text if c.isdigit())
        formatted = format_miles_colombian(clean)
        if formatted != text:
            self.salde_input.blockSignals(True)
            self.salde_input.setText(formatted)
            # Ajusta el cursor al final
            self.salde_input.setCursorPosition(len(formatted))
            self.salde_input.blockSignals(False)
