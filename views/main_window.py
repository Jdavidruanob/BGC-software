import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QStackedWidget, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget  # <--- Agregar esta importación
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from config import load_styles, load_svg_icon, load_svg_icon_tinted, PRIMARY_COLOR, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from version import APP_VERSION
from views.widgets.update_banner import UpdateBanner
from views.widgets.env_banner import EnvBanner
from views.widgets.margenes import MARGEN_ESTRECHO, margen_lateral
import entorno

NAV_ICON_INACTIVO = "#94a3b8"   # slate-400: gris desactivado
NAV_ICON_ACTIVO = PRIMARY_COLOR  # azul oscuro (sobre la pastilla blanca)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # En pruebas el título lo dice también, para distinguir las ventanas en
        # la barra de tareas si se abren las dos a la vez.
        titulo = f"bgc software v{APP_VERSION}"
        if entorno.es_pruebas():
            titulo += "  —  🧪 PRUEBAS"
        self.setWindowTitle(titulo)
        self.setWindowState(Qt.WindowMaximized) # inicializar en ventana completa 
        self.views = {} # Diccionario para almacenar vistas,  clave: nombre, valor: widget
        
        # --- Widget central ---
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ----- Top Bar -----
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout()
        # Margen estrecho de arranque; se ensancha a 80 en `resizeEvent` cuando
        # hay sitio. Ver views/widgets/margenes.py.
        self._top_layout = top_layout
        top_layout.setContentsMargins(MARGEN_ESTRECHO, 17, MARGEN_ESTRECHO, 17)

       # ----- Logo con QSvgWidget (Vectorial y Nítido) -----
        logo_relative_path = "logo/BGC_logo_noche.svg"
        logo_absolute_path = os.path.join(ASSETS_DIR, logo_relative_path)

        if os.path.exists(logo_absolute_path):
            # 1. Crear el Widget SVG directamente con el archivo
            self.logo_widget = QSvgWidget(logo_absolute_path)
            
            # 2. Configurar el tamaño deseado (80x80)
            # Al ser un QSvgWidget, el vector se redibuja a este tamaño exacto sin pixelarse
            self.logo_widget.setFixedSize(60, 60)
            
            # 3. FONDO TRANSPARENTE (Crucial)
            # QSvgWidget a veces pinta un fondo negro o blanco por defecto.
            # Esto fuerza a que el fondo del widget sea transparente.
            self.logo_widget.setStyleSheet("background-color: transparent;")
            self.logo_widget.setAttribute(Qt.WA_TranslucentBackground)
            
            top_layout.addWidget(self.logo_widget, alignment=Qt.AlignLeft)
        
        else:
            # Fallback por si no encuentra el archivo
            print(f"⚠️ No se encontró el logo en: {logo_absolute_path}")
            logo_label = QLabel("🔷 BGC")
            logo_label.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")
            top_layout.addWidget(logo_label, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        # Botones de navegación
        self.btn_home = QPushButton(" Inicio")
        self.btn_assistant = QPushButton(" Auxiliar")
        self.btn_members = QPushButton(" Socios")
        self.btn_data = QPushButton(" Datos")

        # Ruta del ícono de cada botón (se tiñe según el estado activo/inactivo)
        self._nav_icon_path = {
            "home": "icons/home.svg",
            "assistant": "icons/library.svg",
            "members": "icons/users-group.svg",
            "data": "icons/chart-area-line.svg",
        }
        self._nav_btn = {
            "home": self.btn_home,
            "assistant": self.btn_assistant,
            "members": self.btn_members,
            "data": self.btn_data,
        }
        # Íconos en gris desactivado por defecto (el activo se resalta luego)
        for nombre, btn in self._nav_btn.items():
            btn.setIcon(load_svg_icon_tinted(self._nav_icon_path[nombre], NAV_ICON_INACTIVO))

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

        # Aviso de actualización (oculto hasta que haya una versión nueva).
        self.update_banner = UpdateBanner()

        # Aviso de entorno (solo visible en pruebas).
        self.env_banner = EnvBanner()

        # Layout principal
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.env_banner)
        main_layout.addWidget(self.update_banner)
        main_layout.addWidget(self.stack)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Comprobar actualizaciones en segundo plano (no bloquea el arranque).
        self.update_banner.start_check()

        # Indicador de "cargando" (badge central que aparece mientras se consulta)
        self._loading = QLabel("⏳  Cargando…", self)
        self._loading.setObjectName("loadingOverlay")
        self._loading.setAlignment(Qt.AlignCenter)
        self._loading.setStyleSheet(
            "#loadingOverlay{background: rgba(26,54,93,0.94); color: white;"
            " font-size: 18px; font-weight: bold; border-radius: 12px;"
            " padding: 16px 32px;}"
        )
        self._loading.hide()

        # Cargar estilos
        qss_path = os.path.join(STYLES_DIR, "main.qss") 
        load_styles(self, qss_path)

        # Configuración de botones 
        self.btn_home.setObjectName("NavBarButton")
        self.btn_assistant.setObjectName("NavBarButton")
        self.btn_members.setObjectName("NavBarButton")
        self.btn_data.setObjectName("NavBarButton")


    def resizeEvent(self, event):
        super().resizeEvent(event)
        lateral = margen_lateral(event.size().width())
        m = self._top_layout.contentsMargins()
        if m.left() != lateral:
            self._top_layout.setContentsMargins(lateral, m.top(), lateral, m.bottom())

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

            # Llama a refresh_view si existe, mostrando un cursor de espera
            # (indicador de "cargando") mientras se consultan datos. Como las
            # consultas bloquean el hilo de la UI, forzamos el repintado con
            # processEvents() ANTES de bloquear para que el cursor sí se vea.
            if hasattr(widget, "refresh_view"):
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self._show_loading()
                QApplication.processEvents()   # pinta el cambio de vista + badge antes de bloquear
                try:
                    widget.refresh_view()
                except Exception as e:
                    print(f"❌ Error al refrescar vista '{name}': {e}")
                finally:
                    self._loading.hide()
                    QApplication.restoreOverrideCursor()

    def _show_loading(self):
        """Muestra el badge de 'cargando' centrado sobre la ventana."""
        if not self.isVisible():
            return  # en el arranque la ventana aún no se ve
        self._loading.adjustSize()
        s = self._loading.size()
        self._loading.move((self.width() - s.width()) // 2,
                           (self.height() - s.height()) // 2)
        self._loading.raise_()
        self._loading.show()

            
    def highlight_active_button(self, active_name):
        """ Resalta el botón activo en la barra de navegación (texto e ícono). """
        for name, button in self._nav_btn.items():
            activo = (name == active_name)
            button.setProperty("active", activo)
            # El ícono hereda el color del texto: oscuro si está activo (sobre la
            # pastilla blanca), gris desactivado si no.
            color = NAV_ICON_ACTIVO if activo else NAV_ICON_INACTIVO
            button.setIcon(load_svg_icon_tinted(self._nav_icon_path[name], color))
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
