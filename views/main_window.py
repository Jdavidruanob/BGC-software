from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QStackedWidget, QSizePolicy
)
import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from config import PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter

# Function to load SVG icons
def load_svg_icon(path: str, size: QSize = QSize(24, 24)) -> QIcon:
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("bgc software")
        self.resize(1100, 700)
        self.views = {}
        
        # --- Widget central ---
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ----- Top Bar -----
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 10)

        # Logo
        logo_label = QLabel("🔷 BGC")
        logo_label.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")
        top_layout.addWidget(logo_label, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        # Botones con íconos PNG
        icons_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
        print("Ruta de iconos:", icons_dir)
        print("Home icon exists:", os.path.exists(os.path.join(icons_dir, "home.svg")))

        self.btn_home = QPushButton(" Inicio")
        self.btn_home.setIcon(load_svg_icon("assets/icons/home.svg"))

        self.btn_assistant = QPushButton(" Auxiliar")
        self.btn_assistant.setIcon(QIcon(os.path.join(icons_dir, "library.svg")))

        self.btn_members = QPushButton(" Socios")
        self.btn_members.setIcon(QIcon(os.path.join(icons_dir, "users-group.svg")))

        self.btn_data = QPushButton(" Datos")
        self.btn_data.setIcon(QIcon(os.path.join(icons_dir, "chart-area-line.svg")))

        for btn in [self.btn_home, self.btn_assistant, self.btn_members, self.btn_data]:
            btn.setIconSize(QSize(24, 24))
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top_layout.addWidget(btn, alignment=Qt.AlignRight)

        top_bar.setLayout(top_layout)

        # Stack para vistas
        self.stack = QStackedWidget()

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

        self.load_styles()

    def load_styles(self):
        with open("style.qss", "r") as f:
            qss = f.read() % {
                "PRIMARY_COLOR": PRIMARY_COLOR,
                "SECONDARY_COLOR": SECONDARY_COLOR,
                "TEXT_COLOR": TEXT_COLOR
            }
            self.setStyleSheet(qss)

    def add_view(self, name, widget):
        self.views[name] = widget
        self.stack.addWidget(widget)

    def show_view(self, name):
        if name in self.views:
            self.stack.setCurrentWidget(self.views[name])
