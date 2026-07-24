"""Actualizador de la app: consulta la última release en GitHub y, si hay una
versión más nueva, descarga el instalador y lo ejecuta.

Diseño (por qué así):
- El repo es PÚBLICO, así que se puede consultar la API de releases de GitHub
  sin token ni credenciales embebidas.
- Los datos NO viven en la app (están en PostgreSQL en la nube), así que
  reemplazar el .exe/instalador nunca toca los datos del usuario. Lo único
  delicado es el ORDEN cuando cambia la estructura de la base: primero se migra
  la base (vía la API) y después se publica la actualización de la app.
- La descarga y ejecución del instalador cierra la app y la vuelve a abrir ya
  actualizada (el instalador de Inno Setup maneja el "app en ejecución").

Nada aquí bloquea ni rompe la app: cualquier fallo (sin internet, GitHub caído,
release sin instalador) simplemente devuelve None y la app sigue normal.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.request

from version import APP_VERSION

# owner/repo del proyecto (repo público).
_REPO = "Jdavidruanob/BGC-software"
_GITHUB_API_LATEST = f"https://api.github.com/repos/{_REPO}/releases/latest"


def _parse_version(texto: str) -> tuple[int, int, int]:
    """'v1.2.3' -> (1, 2, 3). Tolera prefijos y basura: lo que no sea número se
    trata como 0, para que una comparación nunca lance excepción."""
    limpio = texto.strip().lstrip("vV")
    partes: list[int] = []
    for trozo in limpio.split("."):
        digitos = "".join(c for c in trozo if c.isdigit())
        partes.append(int(digitos) if digitos else 0)
    while len(partes) < 3:
        partes.append(0)
    return (partes[0], partes[1], partes[2])


def check_for_update(timeout: float = 6.0) -> dict | None:
    """Devuelve {'version', 'url', 'notas'} si hay una versión más nueva que la
    instalada; None si está al día o si algo falla (sin internet, etc.)."""
    try:
        req = urllib.request.Request(
            _GITHUB_API_LATEST,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "BGC-software-updater",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except Exception:
        return None

    tag = data.get("tag_name") or ""
    if _parse_version(tag) <= _parse_version(APP_VERSION):
        return None

    # Buscar el instalador (.exe) entre los assets de la release.
    url_instalador = None
    for asset in data.get("assets", []):
        nombre = str(asset.get("name", "")).lower()
        if nombre.endswith(".exe"):
            url_instalador = asset.get("browser_download_url")
            break
    if not url_instalador:
        return None

    return {
        "version": tag.lstrip("vV"),
        "url": url_instalador,
        "notas": data.get("body") or "",
    }


def download_installer(url: str) -> str | None:
    """Descarga el instalador a una carpeta temporal. Devuelve la ruta o None."""
    try:
        destino = os.path.join(tempfile.gettempdir(), "BGC-software-Setup.exe")
        req = urllib.request.Request(url, headers={"User-Agent": "BGC-software-updater"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(destino, "wb") as f:
            while True:
                trozo = resp.read(65536)
                if not trozo:
                    break
                f.write(trozo)
        return destino
    except Exception:
        return None


def launch_installer_and_exit(installer_path: str) -> None:
    """Lanza el instalador y cierra la app para que pueda reemplazar los
    archivos. El instalador vuelve a abrir la app al terminar."""
    subprocess.Popen([installer_path], close_fds=True)
    sys.exit(0)
