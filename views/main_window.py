# financial_cooperative/views/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QIcon, QFont

# Importa tus páginas
from views.home_page import HomePage
from views.auxiliary_page import AuxiliaryPage
from views.partners_page import PartnersPage
from views.data_page import DataPage

class MainWindow(QMainWindow):
    # Señal para notificar al Presenter sobre la navegación
    navigate_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cooperativa Familiar")
        self.setGeometry(100, 100, 1200, 800) # Tamaño inicial de la ventana
        self.setObjectName("MainWindow") # Para aplicar QSS global

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._create_navbar()
        self._create_stacked_widget()
        self._add_pages_to_stacked_widget()

        self.main_layout.addLayout(self.navbar_layout)
        self.main_layout.addWidget(self.stacked_widget)

        self.load_global_qss()

        # Establecer la página de inicio por defecto
        self.stacked_widget.setCurrentIndex(0) # O el índice de tu página de Inicio

    def _create_navbar(self):
        self.navbar_layout = QHBoxLayout()
        self.navbar_layout.setContentsMargins(0, 0, 0, 0)
        self.navbar_layout.setSpacing(0) # Eliminar espaciado entre botones

        font = QFont("Arial", 12) # Puedes ajustar la fuente

        # Botón Inicio
        self.btn_home = QPushButton("Inicio")
        self.btn_home.setObjectName("NavbarButton")
        self.btn_home.setFont(font)
        self.btn_home.clicked.connect(lambda: self.navigate_requested.emit("home"))
        self.navbar_layout.addWidget(self.btn_home)

        # Botón Auxiliar
        self.btn_auxiliary = QPushButton("Auxiliar")
        self.btn_auxiliary.setObjectName("NavbarButton")
        self.btn_auxiliary.setFont(font)
        self.btn_auxiliary.clicked.connect(lambda: self.navigate_requested.emit("auxiliary"))
        self.navbar_layout.addWidget(self.btn_auxiliary)

        # Botón Socios
        self.btn_partners = QPushButton("Socios")
        self.btn_partners.setObjectName("NavbarButton")
        self.btn_partners.setFont(font)
        self.btn_partners.clicked.connect(lambda: self.navigate_requested.emit("partners"))
        self.navbar_layout.addWidget(self.btn_partners)

        # Botón Datos
        self.btn_data = QPushButton("Datos")
        self.btn_data.setObjectName("NavbarButton")
        self.btn_data.setFont(font)
        self.btn_data.clicked.connect(lambda: self.navigate_requested.emit("data"))
        self.navbar_layout.addWidget(self.btn_data)

        # Espaciador para empujar los botones a la izquierda si es necesario
        # self.navbar_layout.addStretch()

    def _create_stacked_widget(self):
        self.stacked_widget = QStackedWidget()

    def _add_pages_to_stacked_widget(self):
        self.home_page = HomePage()
        self.auxiliary_page = AuxiliaryPage()
        self.partners_page = PartnersPage()
        self.data_page = DataPage()

        self.stacked_widget.addWidget(self.home_page)      # Index 0
        self.stacked_widget.addWidget(self.auxiliary_page) # Index 1
        self.stacked_widget.addWidget(self.partners_page)  # Index 2
        self.stacked_widget.addWidget(self.data_page)      # Index 3

    def set_current_page(self, page_name):
        # Mapea el nombre de la página al índice del stacked widget
        page_map = {
            "home": 0,
            "auxiliary": 1,
            "partners": 2,
            "data": 3,
        }
        index = page_map.get(page_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
        else:
            print(f"Página '{page_name}' no encontrada.")

    def load_global_qss(self):
        try:
            with open("resources/qss/global.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("global.qss no encontrado. Usando estilos predeterminados.")