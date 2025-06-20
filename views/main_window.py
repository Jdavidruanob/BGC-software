from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema BGC")
        self.resize(1000, 600)

        self.views = {}

        # Top-level layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ----- Top Bar -----
        top_bar = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 10)

        # Logo (Left)
        logo_label = QLabel("🔷 BGC")
        logo_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        top_layout.addWidget(logo_label, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        # Top-right navigation buttons
        self.btn_home = QPushButton("Inicio")
        self.btn_assistant = QPushButton("Auxiliar")
        self.btn_members = QPushButton("Socios")
        self.btn_data = QPushButton("Datos")

        for btn in [self.btn_home, self.btn_assistant, self.btn_members, self.btn_data]:
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top_layout.addWidget(btn, alignment=Qt.AlignRight)

        top_bar.setLayout(top_layout)

        # Stack for pages
        self.stack = QStackedWidget()

        # Navigation signals
        self.btn_home.clicked.connect(lambda: self.show_view("home"))
        self.btn_assistant.clicked.connect(lambda: self.show_view("assistant"))
        self.btn_members.clicked.connect(lambda: self.show_view("members"))
        self.btn_data.clicked.connect(lambda: self.show_view("data"))

        # Final layout
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.stack)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def add_view(self, name, widget):
        self.views[name] = widget
        self.stack.addWidget(widget)

    def show_view(self, name):
        if name in self.views:
            self.stack.setCurrentWidget(self.views[name])
