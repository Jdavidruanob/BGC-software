"""Franja que avisa cuando la app NO está trabajando contra la base real.

En producción no se muestra nada: la app se ve exactamente igual que siempre.
En pruebas aparece una banda ámbar permanente —sin botón de cerrar, a
propósito— indicando el entorno y contra qué base se está trabajando.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

import entorno


class EnvBanner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EnvBanner")

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 8, 24, 8)

        self.label = QLabel(
            f"🧪  MODO PRUEBAS — los cambios NO afectan la base real  ·  "
            f"{entorno.descripcion_conexion()}"
        )
        self.label.setObjectName("EnvBannerLabel")

        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet(
            "#EnvBanner { background-color: #f59e0b; border-bottom: 2px solid #b45309; }"
            "#EnvBannerLabel { color: #451a03; font-weight: 700; }"
        )

        # En producción el widget existe pero nunca se ve, así que el layout de
        # la ventana no cambia según el entorno.
        if entorno.es_produccion():
            self.hide()
