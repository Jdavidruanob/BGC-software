from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtGui import QIcon

def show_success(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("")
    msg.setWindowIcon(QIcon.fromTheme("dialog-information"))  # Icono de información del sistema
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox { background-color: #e6fffa; }
        QLabel { font-size: 17px; font-weight: bold; color: #047857; background: transparent; }
        QPushButton { min-width: 80px; font-size: 15px; font-weight: bold; }
    """)
    return msg.exec()

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