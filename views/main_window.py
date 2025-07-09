import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from config import load_styles, load_svg_icon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() 
        self.setWindowTitle("bgc software")
        self.setWindowState(Qt.WindowMaximized) # inicializar en ventana completa 
        self.views = {} # Diccionario para almacenar vistas,  clave: nombre, valor: widget
        
        # --- Widget central ---
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ----- Top Bar -----
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 17.5, 80, 17.5) # Margen Topbar, right, top, left, bottom

        # Logo
        logo_label = QLabel("🔷 BGC")
        logo_label.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")
        logo_label.setObjectName("logoLabel")
        
        top_layout.addWidget(logo_label, alignment=Qt.AlignLeft)
        top_layout.addStretch()

        # Botones con íconos PNG
        icons_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
        # Inicio
        self.btn_home = QPushButton(" Inicio")
        self.btn_home.setIcon(load_svg_icon("assets/icons/home.svg")) # Usa la función load_svg_icon para cargar el ícono SVG
        # Auxiliar
        self.btn_assistant = QPushButton(" Auxiliar")
        self.btn_assistant.setIcon(QIcon(os.path.join(icons_dir, "library.svg")))
        # Socios
        self.btn_members = QPushButton(" Socios")
        self.btn_members.setIcon(QIcon(os.path.join(icons_dir, "users-group.svg")))
        # Datos
        self.btn_data = QPushButton(" Datos")
        self.btn_data.setIcon(QIcon(os.path.join(icons_dir, "chart-area-line.svg")))

        # Configuración de botones
        for btn in [self.btn_home, self.btn_assistant, self.btn_members, self.btn_data]:
            btn.setIconSize(QSize(24, 24))
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top_layout.addWidget(btn, alignment=Qt.AlignRight)

        top_bar.setLayout(top_layout) # Layout de la barra superior

        # Stack para vistas
        self.stack = QStackedWidget() # QStackedWidget es un contenedor que permite apilar widgets uno encima del otro

        # Conexiones
        self.btn_home.clicked.connect(lambda: self.show_view("home"))
        self.btn_assistant.clicked.connect(lambda: self.show_view("assistant"))
        self.btn_members.clicked.connect(lambda: self.show_view("members"))
        self.btn_data.clicked.connect(lambda: self.show_view("data"))

        # Layout principal
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.stack)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Cargar estilos
        qss_path = os.path.join(os.path.dirname(__file__), "..",  "styles", "main.qss")
        load_styles(self, qss_path)

        # Configuración de botones 
        self.btn_home.setObjectName("NavBarButton")
        self.btn_assistant.setObjectName("NavBarButton")
        self.btn_members.setObjectName("NavBarButton")
        self.btn_data.setObjectName("NavBarButton")


    def add_view(self, name, widget):
        """ Agrega una vista al stack y al diccionario de vistas. """
        self.views[name] = widget
        self.stack.addWidget(widget)

    def show_view(self, name):
        """Muestra la vista y la refresca si tiene método 'refresh_view'."""
        if name in self.views:
            widget = self.views[name]
            self.stack.setCurrentWidget(widget)
            self.highlight_active_button(name)

            # Llama a refresh_view si existe
            if hasattr(widget, "refresh_view"):
                try:
                    widget.refresh_view()
                except Exception as e:
                    print(f"❌ Error al refrescar vista '{name}': {e}")

            
    def highlight_active_button(self, active_name):
        """ Resalta el botón activo en la barra de navegación. """
        buttons = {
            "home": self.btn_home,
            "assistant": self.btn_assistant,
            "members": self.btn_members,
            "data": self.btn_data,
        }

        for name, button in buttons.items():
            if name == active_name:
                button.setProperty("active", True)
            else:
                button.setProperty("active", False)

            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
