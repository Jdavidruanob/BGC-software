from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt


class FormAporte(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.socios_data = []

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("📥 Registro de Aporte")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 12px;")

        self.combo_socios = QComboBox()
        self.combo_socios.setMinimumWidth(300)

        layout.addWidget(title)
        layout.addWidget(QLabel("Recibí de:"))
        layout.addWidget(self.combo_socios)

        self.setLayout(layout)
        self.load_socios()

    def load_socios(self):
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_socios.clear()

            if not self.socios_data:
                QMessageBox.warning(self, "Sin socios", "No hay socios registrados en la base de datos.")
                return

            for socio in self.socios_data:
                nombre_completo = f"{socio['nombres']} {socio['apellidos']}"
                cc = socio['cc']
                self.combo_socios.addItem(f"{nombre_completo} (CC: {cc})", userData=socio)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista de socios:\n{e}")

    def refresh(self):
        self.load_socios()

    def get_socio_seleccionado(self):
        """Devuelve el diccionario completo del socio seleccionado"""
        return self.combo_socios.currentData()
