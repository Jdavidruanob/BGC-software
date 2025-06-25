from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
import os

DEFAULT_PHOTO = "assets/icons/default_user.png"

class NewMemberDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Socio")
        self.setModal(True)
        self.setFixedSize(400, 320)

        self.name_input = QLineEdit()
        self.cc_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.photo_input = QLineEdit()

        # Botón para seleccionar imagen
        photo_btn = QPushButton("Seleccionar imagen")
        photo_btn.clicked.connect(self.select_photo)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(QLabel("Nombre completo:"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Cédula:"))
        layout.addWidget(self.cc_input)

        layout.addWidget(QLabel("Celular:"))
        layout.addWidget(self.phone_input)

        layout.addWidget(QLabel("Foto (opcional):"))
        photo_layout = QHBoxLayout()
        photo_layout.addWidget(self.photo_input)
        photo_layout.addWidget(photo_btn)
        layout.addLayout(photo_layout)

        # Botón de crear
        create_btn = QPushButton("Crear socio")
        create_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #0A2F66; color: white;")
        create_btn.clicked.connect(self.on_submit)
        layout.addWidget(create_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            self.photo_input.setText(file_path)

    def on_submit(self):
        if not self.name_input.text().strip() or not self.cc_input.text().strip():
            QMessageBox.warning(self, "Campos obligatorios", "Por favor ingrese al menos nombre y cédula.")
            return
        self.accept()

    def get_data(self):
        name = self.name_input.text().strip()
        cc = self.cc_input.text().strip()
        phone = self.phone_input.text().strip()
        photo = self.photo_input.text().strip() or DEFAULT_PHOTO
        return (cc, name, phone, photo)
