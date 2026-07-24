"""Aviso de actualización: una barra discreta que aparece arriba SOLO si hay
una versión más nueva publicada. El usuario puede actualizar cuando quiera o
ignorarla; no bloquea nada.

La comprobación y la descarga corren en hilos aparte para no congelar la
interfaz mientras se habla con GitHub.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from utils import updater


class _CheckThread(QThread):
    """Consulta GitHub en segundo plano. Emite el dict de la actualización, o
    None si está al día / falla."""

    resultado = Signal(object)

    def run(self) -> None:
        self.resultado.emit(updater.check_for_update())


class _DownloadThread(QThread):
    """Descarga el instalador en segundo plano. Emite la ruta o None."""

    listo = Signal(object)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        self.listo.emit(updater.download_installer(self._url))


class UpdateBanner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        self._url: str | None = None
        self._check_thread: _CheckThread | None = None
        self._download_thread: _DownloadThread | None = None

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 10, 24, 10)

        self.label = QLabel()
        self.label.setObjectName("UpdateBannerLabel")

        self.btn_update = QPushButton("Actualizar ahora")
        self.btn_update.setObjectName("UpdateBannerButton")
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.clicked.connect(self._on_update_clicked)

        self.btn_dismiss = QPushButton("Ahora no")
        self.btn_dismiss.setObjectName("UpdateBannerDismiss")
        self.btn_dismiss.setCursor(Qt.PointingHandCursor)
        self.btn_dismiss.clicked.connect(self.hide)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.btn_update)
        layout.addWidget(self.btn_dismiss)
        self.setLayout(layout)

        # Fallback de estilo por si el .qss no define el objectName (barra ámbar
        # discreta, legible sobre tema claro u oscuro).
        self.setStyleSheet(
            "#UpdateBanner { background-color: #fef3c7; border-bottom: 1px solid #f59e0b; }"
            "#UpdateBannerLabel { color: #92400e; font-weight: 600; }"
            "#UpdateBannerButton { background-color: #f59e0b; color: white;"
            " border: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; }"
            "#UpdateBannerDismiss { background-color: transparent; color: #92400e;"
            " border: none; padding: 6px 10px; }"
        )

        self.hide()  # oculto hasta que se confirme que hay actualización

    def start_check(self) -> None:
        """Arranca la comprobación en segundo plano. Llamar al iniciar la app."""
        self._check_thread = _CheckThread(self)
        self._check_thread.resultado.connect(self._on_check_result)
        self._check_thread.start()

    def _on_check_result(self, info: object) -> None:
        if not isinstance(info, dict):
            return  # al día o sin conexión: no mostramos nada
        self._url = info.get("url")
        version = info.get("version", "")
        self.label.setText(f"🔔 Hay una nueva versión disponible ({version}). ")
        self.show()

    def _on_update_clicked(self) -> None:
        if not self._url:
            return
        self.btn_update.setEnabled(False)
        self.btn_dismiss.setEnabled(False)
        self.label.setText("⬇️ Descargando la actualización, un momento…")
        self._download_thread = _DownloadThread(self._url)
        self._download_thread.listo.connect(self._on_download_done)
        self._download_thread.start()

    def _on_download_done(self, ruta: object) -> None:
        if not isinstance(ruta, str):
            self.label.setText("⚠️ No se pudo descargar la actualización. Intenta más tarde.")
            self.btn_update.setEnabled(True)
            self.btn_dismiss.setEnabled(True)
            return
        # Lanza el instalador y cierra la app (el instalador la reabre).
        updater.launch_installer_and_exit(ruta)
