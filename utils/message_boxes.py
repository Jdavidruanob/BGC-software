from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtGui import QIcon, QColor
from PySide6.QtCore import Qt
import os

# --- Colores Base ---
COLOR_SUCCESS_BORDER = "#56c96d" # Verde para borde y texto
COLOR_INFO_BORDER = "#3e7bbe"    # Azul para borde y texto
COLOR_WARNING_BORDER = "#f4c356" # Naranja para borde y texto
COLOR_ERROR_BORDER = "#ef5c54"   # Rojo para borde y texto

# --- Colores de Fondo Suaves ---
BG_COLOR_SUCCESS = "#f1f9f4" # Verde pálido (fondo de la caja)
BG_COLOR_INFO = "#e7eefa"    # Azul pálido
BG_COLOR_WARNING = "#fef7ea" # Amarillo pálido
BG_COLOR_ERROR = "#fcefea"   # Rojo pálido

# Color y tamaño solicitados para el texto del cuerpo (el mensaje dinámico)
TEXT_BODY_COLOR = "#5f6667"
TEXT_TITLE_COLOR = "#1c2020" 
TEXT_BODY_SIZE = "18px"
TEXT_TITLE_SIZE = "22px"
TITLE_MARGIN_BOTTOM = "6px" # Margen entre el título fijo y el mensaje

def get_base_style(border_color, background_color):
    """Retorna la plantilla QSS con colores y bordes dinámicos."""
    return f"""
        QMessageBox {{ 
            /* Estilo de la caja: Borde inferior y lateral, esquinas redondeadas */
            background-color: {background_color}; 
            border: 2px solid {border_color};
            border-top-left-radius: 0px; 
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 15px; 
        }}
        
        QLabel {{ 
            /* Este QLabel contiene TODO el texto. Usamos HTML/CSS interno
            para estilizar el título (18px) y el cuerpo (16px, gris). 
            */
            font-size: {TEXT_BODY_SIZE}; /* Tamaño del texto del cuerpo base (16px) */
            color: {TEXT_BODY_COLOR}; /* Color del texto del cuerpo (#666b69) */
            background: transparent; 
            margin-top: 10px;
        }}
        
        /* Estilo de los botones */
        QPushButton {{ 
            min-width: 80px; 
            padding: 8px 15px;
            font-size: 14px; 
            font-weight: 600;
            border-radius: 8px; /* Botones redondeados */
            
            /* Colores del botón igual al fondo de la caja */
            background-color: {background_color}; 
            color: #1f2937; /* Texto del botón oscuro */
            
            /* Borde del botón igual al borde principal de la caja */
            border: 1px solid {border_color}; 
        }}
        
        QPushButton:hover {{
            /* Efecto hover sutil */
            background-color: #ffffff;
        }}
    """

# --- FUNCIONES DE MENSAJE REFACTORIZADAS ---

def show_success(parent, title, text, file_path=None):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question) 
    msg.setWindowTitle(" ") 
    msg.setWindowIcon(QIcon.fromTheme("dialog-information")) 
    
    msg.setStyleSheet(get_base_style(COLOR_SUCCESS_BORDER, BG_COLOR_SUCCESS))
    
    # 🔑 Ajuste clave: Se separa el título (span) del texto (p) para aplicar estilos diferentes
    msg.setText(f"<span style='font-size: {TEXT_TITLE_SIZE}; color: {TEXT_TITLE_COLOR}; font-weight: bold;'>¡Éxito!</span>"
                f"<p style='margin-top: {TITLE_MARGIN_BOTTOM};'>{text}</p>")

    # Lógica de botones (Aceptar y Abrir Archivo)
    if file_path:
        abrir_button = msg.addButton("Abrir Archivo", QMessageBox.ActionRole)
        ok_button = msg.addButton("Aceptar", QMessageBox.AcceptRole)

        def open_file_on_click():
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(parent, "Error al abrir", f"No se pudo abrir el archivo:\n{e}")

        abrir_button.clicked.connect(open_file_on_click)
        msg.setDefaultButton(ok_button)
    else:
        msg.setStandardButtons(QMessageBox.Ok)
    
    msg.exec()


def show_error(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(" ")
    msg.setWindowIcon(QIcon.fromTheme("dialog-error")) 
    
    msg.setStyleSheet(get_base_style(COLOR_ERROR_BORDER, BG_COLOR_ERROR))
    msg.setText(f"<span style='font-size: {TEXT_TITLE_SIZE}; color: {TEXT_TITLE_COLOR}; font-weight: bold;'>¡Error!</span>"
                f"<p style='margin-top: {TITLE_MARGIN_BOTTOM};'>{text}</p>")
    msg.setStandardButtons(QMessageBox.Ok)
    
    return msg.exec()


def show_warning(parent, title, text, ask_confirmation=False):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(" ")
    msg.setWindowIcon(QIcon.fromTheme("dialog-warning")) 
    
    msg.setStyleSheet(get_base_style(COLOR_WARNING_BORDER, BG_COLOR_WARNING))
    msg.setText(f"<span style='font-size: {TEXT_TITLE_SIZE}; color: {TEXT_TITLE_COLOR}; font-weight: bold;'>¡Advertencia!</span>"
                f"<p style='margin-top: {TITLE_MARGIN_BOTTOM};'>{text}</p>")
    
    if ask_confirmation:
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    else:
        msg.setStandardButtons(QMessageBox.Ok)
        
    return msg.exec()


def show_info(parent, title, text, ask_confirmation=False):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(" ")
    msg.setWindowIcon(QIcon.fromTheme("dialog-question")) 
    
    msg.setStyleSheet(get_base_style(COLOR_INFO_BORDER, BG_COLOR_INFO))
    msg.setText(f"<span style='font-size: {TEXT_TITLE_SIZE}; color: {TEXT_TITLE_COLOR}; font-weight: bold;'>¡Información!</span>"
                f"<p style='margin-top: {TITLE_MARGIN_BOTTOM};'>{text}</p>")
    
    if ask_confirmation:
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    else:
        msg.setStandardButtons(QMessageBox.Ok)
        
    return msg.exec()