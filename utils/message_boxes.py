from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtGui import QIcon
import os

def show_success(parent, title, text, file_path=None):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setWindowIcon(QIcon.fromTheme("dialog-information"))
    msg.setText(text)

    # Si se proporciona una ruta de archivo, agregamos un botón 'Abrir Archivo'
    if file_path:
        # Definimos los botones
        abrir_button = msg.addButton("Abrir Archivo", QMessageBox.ActionRole)
        ok_button = msg.addButton("Aceptar", QMessageBox.AcceptRole)

        # Conectamos la acción del botón "Abrir"
        def open_file_on_click():
            try:
                # Usa os.startfile para abrir el archivo
                # Nota: Esto es solo para Windows. Para otros OS, se necesitaría 'os.system("open...")' (macOS) o 'os.system("xdg-open...")' (Linux).
                os.startfile(file_path)
            except Exception as e:
                # Manejo de errores si el archivo no se puede abrir
                QMessageBox.warning(parent, "Error al abrir", f"No se pudo abrir el archivo:\n{e}")

        # Conectamos el botón 'Abrir' a la función
        abrir_button.clicked.connect(open_file_on_click)

        # Establecemos el botón por defecto para la acción 'Aceptar'
        msg.setDefaultButton(ok_button)
    else:
        # Lógica original para un mensaje de éxito simple
        msg.setStandardButtons(QMessageBox.Ok)
    
    msg.setStyleSheet("""
            QMessageBox { background-color: #e6fffa; }
            QLabel { font-size: 17px; font-weight: bold; color: #047857; background: transparent; }
            QPushButton { min-width: 80px; font-size: 15px; font-weight: bold; }
        """)
    msg.exec()

def show_error(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("")
    msg.setWindowIcon(QIcon.fromTheme("dialog-error"))  # Icono de error del sistema
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox { background-color: #fef2f2; }
        QLabel { font-size: 17px; font-weight: bold; color: #b91c1c; background: transparent; }
        QPushButton { min-width: 80px; font-size: 15px; font-weight: bold; }
    """)
    return msg.exec()

def show_warning(parent, title, text, ask_confirmation=False):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(" ")
    msg.setWindowIcon(QIcon.fromTheme("dialog-warning"))  # Icono de advertencia del sistema
    msg.setText(text)
    if ask_confirmation:
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    else:
        msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox { background-color: #fef9c3; }
        QLabel { font-size: 17px; font-weight: bold; color: #b45309; background: transparent; }
        QPushButton { min-width: 80px; font-size: 15px; font-weight: bold; }
    """)
    return msg.exec()

def show_info(parent, title, text, ask_confirmation=False):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("")
    msg.setWindowIcon(QIcon.fromTheme("dialog-information"))  # Icono de información del sistema
    msg.setText(text)
    if ask_confirmation:
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    else:
        msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox { background-color: #eff6ff; }
        QLabel { font-size: 17px; font-weight: bold; color: #1d4ed8; background: transparent; }
        QPushButton { min-width: 80px; font-size: 15px; font-weight: bold; }
    """)
    return msg.exec()