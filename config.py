from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QScrollArea
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
import os
import sys # <-- Importa sys


# --- Definición de BASE_APP_DIR para desarrollo y ejecutable ---

# 1. Base para archivos empaquetados (Assets, Styles)
if getattr(sys, 'frozen', False):
    STATIC_BASE_DIR = sys._MEIPASS
else:
    STATIC_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 2. Base para archivos de usuario (DB, Recibos, Liquidaciones)
if getattr(sys, 'frozen', False):
    DYNAMIC_DATA_BASE_DIR = os.path.dirname(sys.executable)
else:
    DYNAMIC_DATA_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- Definir el Año Fiscal ---
""" from datetime import date
today = date.today()
if today.month == 12:
    # Si estamos en Diciembre, el año fiscal es el siguiente año calendario.
    FISCAL_YEAR = str(today.year + 1)
else:
    # Si estamos de Enero a Noviembre, es el año calendario actual.
    FISCAL_YEAR = str(today.year) """

FISCAL_YEAR = "2025" # Para pruebas migracion final de anio

# Rutas que necesitan sys._MEIPASS para funcionar
ASSETS_DIR = os.path.join(STATIC_BASE_DIR, "assets")
STYLES_DIR = os.path.join(STATIC_BASE_DIR, "styles")
#  C:\App\Archivos_BGC\
DATA_ROOT_FOLDER = os.path.join(DYNAMIC_DATA_BASE_DIR, "Archivos_BGC")
#  C:\App\Archivos_BGC\2026\
YEAR_DATA_DIR = os.path.join(DATA_ROOT_FOLDER, FISCAL_YEAR)

# DB y Archivos de salida deben usar la carpeta del año fiscal
DB_PATH = os.path.join(YEAR_DATA_DIR, "BGC-software.db")
RECIBOS_OUTPUT_DIR = os.path.join(YEAR_DATA_DIR, "Recibos")
LIQUIDACIONES_OUTPUT_DIR = os.path.join(YEAR_DATA_DIR, "Liquidaciones")

# Asegura que la carpeta del año fiscal exista (la primera vez que se ejecuta)
if not os.path.exists(YEAR_DATA_DIR):
    os.makedirs(YEAR_DATA_DIR)

DB_FILE_NAME = "BGC-software.db"

DB_PATH_FINAL = os.path.join(YEAR_DATA_DIR, DB_FILE_NAME)  # RUTA FINAL: Apunta a la carpeta del año fiscal


# --- Colores globales ---

PRIMARY_COLOR = "#1a365d"     # Azul oscuro (fondo navbar)
SECONDARY_COLOR = "#8C5B2F"   # Marrón (hover y botón activo)
TEXT_COLOR = "#FFFFFF"        # Texto blanco
#e3e9f1 bordes


# --- Metodos Globlales ---

def load_styles(self, qss_path):
    """ Carga un archivo QSS y aplica los colores globales definidos."""
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

def load_svg_icon(relative_path: str, size: QSize = QSize(24, 24)) -> QIcon:
    """
    Carga un archivo SVG combinando la ruta base de assets con la ruta relativa.
    
    :param relative_path: La ruta del ícono *dentro* de la carpeta 'assets'. 
                          Ej: "icons/pig-money.svg"
    """
    # Combina la ruta absoluta donde PyInstaller colocó 'assets' con la ruta del ícono.
    absolute_path = os.path.join(ASSETS_DIR, relative_path)
    
    # Carga y Renderizado
    renderer = QSvgRenderer(absolute_path)
    if not renderer.isValid():
        # Manejo de error si el ícono no se encuentra
        print(f"Error: No se pudo cargar el ícono SVG en la ruta: {absolute_path}")
        return QIcon() # Retorna un ícono vacío para evitar fallos
        
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)

def format_miles_colombian_int(value: int) -> str:
    """
    Recibe un entero (100000) y devuelve '100.000'.
    """
    return f"{value:,}".replace(",", ".")

def parse_miles_colombian(text: str) -> int:
    """
    Recibe un texto con puntos (p.ej. '123.456') 
    y devuelve el entero 123456.
    Cualquier caracter no dígito se elimina.
    """
    clean = "".join(ch for ch in text if ch.isdigit())
    return int(clean) if clean else 0

def format_full_name_for_excel(nombres, apellidos, max_length=24):
    """
    Formatea un nombre completo (nombres + apellidos) para que se ajuste a una longitud máxima,
    reduciendo el segundo apellido o segundo nombre a una inicial si es necesario.
    """
    original_full_name = f"{nombres} {apellidos}"
    
    if len(original_full_name) <= max_length:
        return original_full_name

    parts_nombres = nombres.split()
    parts_apellidos = apellidos.split()

    # Intentar reducir solo el segundo apellido (si existe)
    if len(parts_apellidos) > 1:
        temp_apellidos = f"{parts_apellidos[0]} {parts_apellidos[1][0]}."
        temp_full_name = f"{nombres} {temp_apellidos}"
        if len(temp_full_name) <= max_length:
            return temp_full_name
    
    # Intentar reducir solo el segundo nombre (si existe)
    if len(parts_nombres) > 1:
        temp_nombres = f"{parts_nombres[0]} {parts_nombres[1][0]}."
        temp_full_name = f"{temp_nombres} {apellidos}"
        if len(temp_full_name) <= max_length:
            return temp_full_name

    # Intentar reducir segundo nombre Y segundo apellido (si ambos existen)
    if len(parts_nombres) > 1 and len(parts_apellidos) > 1:
        reduced_nombres = f"{parts_nombres[0]} {parts_nombres[1][0]}."
        reduced_apellidos = f"{parts_apellidos[0]} {parts_apellidos[1][0]}."
        final_name = f"{reduced_nombres} {reduced_apellidos}"
        if len(final_name) <= max_length:
            return final_name
            
    # Último recurso: si nada funcionó, truncar de la manera más sensata
    # Mantener primer nombre y primer apellido. Si hay espacio, agregar iniciales.
    final_parts = [parts_nombres[0]] if parts_nombres else []
    
    if len(parts_nombres) > 1:
        initial = f"{parts_nombres[1][0]}."
        if len(" ".join(final_parts + [initial, parts_apellidos[0] if parts_apellidos else ""])) <= max_length:
            final_parts.append(initial)

    if parts_apellidos:
        final_parts.append(parts_apellidos[0])

    if len(parts_apellidos) > 1:
        initial = f"{parts_apellidos[1][0]}."
        if len(" ".join(final_parts + [initial])) <= max_length:
            final_parts.append(initial)
            
    return " ".join(final_parts) # Podría ser un poco más sofisticado, pero esto ya cubre la mayoría de los casos.