"""
Factory functions for common UI patterns.
Returns pre-configured widgets ready to be added to layouts.
"""
from PySide6.QtWidgets import QPushButton, QLabel, QLineEdit
from PySide6.QtCore import Qt, QSize
from config import load_svg_icon, PRIMARY_COLOR


def primary_button(text: str, icon_name: str = None) -> QPushButton:
    """Botón principal azul (RegisterButton). Opcional: ícono relativo a assets/."""
    btn = QPushButton(text)
    btn.setObjectName("RegisterButton")
    btn.setMinimumHeight(44)
    if icon_name:
        btn.setIcon(load_svg_icon(icon_name))
        btn.setIconSize(QSize(20, 20))
    return btn


def form_label(text: str) -> QLabel:
    """Etiqueta de campo de formulario (FormLabel)."""
    lbl = QLabel(text)
    lbl.setObjectName("FormLabel")
    return lbl


def text_input(placeholder: str = "", alignment=Qt.AlignLeft) -> QLineEdit:
    """Input de texto genérico (InputField)."""
    inp = QLineEdit()
    inp.setObjectName("InputField")
    if placeholder:
        inp.setPlaceholderText(placeholder)
    inp.setAlignment(alignment)
    return inp


def delete_button(icon_name: str = "icons/x.svg") -> QPushButton:
    """Botón de eliminar con borde rojo (DeleteButton)."""
    btn = QPushButton()
    btn.setObjectName("DeleteButton")
    btn.setIcon(load_svg_icon(icon_name))
    btn.setIconSize(QSize(20, 20))
    btn.setFixedSize(28, 28)
    btn.setToolTip("Eliminar")
    return btn


def add_button(text: str, object_name: str = "AddAporteButton") -> QPushButton:
    """Botón de agregar (texto azul con underline). object_name permite especificar
    AddAporteButton, AddPagoButton o AddLetraButton según el contexto."""
    btn = QPushButton(text)
    btn.setObjectName(object_name)
    btn.setIcon(load_svg_icon("icons/plus.svg"))
    btn.setIconSize(QSize(20, 20))
    return btn
