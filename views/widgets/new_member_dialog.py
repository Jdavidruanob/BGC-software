from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
import os
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR

DEFAULT_PHOTO = "assets/images/default_user.png"

class NewMemberDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Socio")
        self.setModal(True)
        self.setFixedSize(600, 550)
        self.setObjectName("NewMemberDialog")

        self.first_name_input = QLineEdit()
        self.first_name_input.setObjectName("InputField")

        self.last_name_input = QLineEdit()
        self.last_name_input.setObjectName("InputField")

        self.cc_input = QLineEdit()
        self.cc_input.setObjectName("InputField")

        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("InputField")

        self.photo_input = QLineEdit()
        self.photo_input.setObjectName("InputField")

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
        self.load_styles()

    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), ".." , "..","styles", "new_member_dialog.qss")
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

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            self.photo_input.setText(file_path)

    def on_submit(self):
        if not self.first_name_input.text().strip() or not self.last_name_input.text().strip() or not self.cc_input.text().strip():
            QMessageBox.warning(self, "Campos obligatorios", "Por favor ingrese nombres, apellidos y cédula.")
            return
        self.accept()

    def get_data(self):
        nombres = self.first_name_input.text().strip()
        apellidos = self.last_name_input.text().strip()
        cc = self.cc_input.text().strip()
        phone = self.phone_input.text().strip()
        photo = self.photo_input.text().strip() or DEFAULT_PHOTO
        return (cc, nombres, apellidos, phone, photo)
