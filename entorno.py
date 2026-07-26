"""En qué entorno está corriendo la app: producción o pruebas.

Existe una sola base de datos real (producción, en Railway) y una copia de
pruebas. Trabajar en la de pruebas creyendo que es producción —o al revés— es
el error caro, así que el entorno se declara explícitamente y se muestra
siempre en pantalla.

Cómo se decide, en orden:

1. La variable `APP_ENV` del `.env` (`produccion` o `pruebas`). Es la fuente de
   verdad; si está puesta, manda.
2. Si no está, se compara el host:puerto de `DATABASE_URL` contra la lista de
   bases conocidas (`_BASES_CONOCIDAS`).
3. Si tampoco se reconoce, se asume **producción**. Es el default prudente:
   equivocarse creyendo que estás en pruebas cuando en realidad estás en la
   base real es el fallo que hay que evitar.

Este módulo no importa Qt a propósito, para que también lo puedan usar los
scripts de mantenimiento y cualquier proceso sin interfaz.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

PRODUCCION = "produccion"
PRUEBAS = "pruebas"

# Etiquetas que puede traer APP_ENV. Se normaliza a minúsculas y sin espacios.
_ALIAS = {
    "produccion": PRODUCCION,
    "producción": PRODUCCION,
    "prod": PRODUCCION,
    "production": PRODUCCION,
    "live": PRODUCCION,
    "real": PRODUCCION,
    "pruebas": PRUEBAS,
    "prueba": PRUEBAS,
    "dev": PRUEBAS,
    "desarrollo": PRUEBAS,
    "development": PRUEBAS,
    "test": PRUEBAS,
    "testing": PRUEBAS,
    "staging": PRUEBAS,
    "local": PRUEBAS,
}

# Bases conocidas por host:puerto, para el caso en que falte APP_ENV.
# Ambas viven en el mismo host de Railway; lo que las distingue es el puerto.
_BASES_CONOCIDAS = {
    "sakura.proxy.rlwy.net:42792": PRODUCCION,
    "sakura.proxy.rlwy.net:54722": PRUEBAS,
}


def _normalizar(valor: str | None) -> str | None:
    if not valor:
        return None
    return _ALIAS.get(valor.strip().lower())


def _host_puerto(dsn: str | None) -> str | None:
    """'host:puerto' de una URL de conexión, o None si no se puede leer.

    Nunca devuelve la contraseña: solo se usa el netloc sin credenciales.
    """
    if not dsn:
        return None
    try:
        p = urlparse(dsn)
        if not p.hostname:
            return None
        return f"{p.hostname}:{p.port}" if p.port else p.hostname
    except Exception:
        return None


def get_entorno() -> str:
    """`PRODUCCION` o `PRUEBAS`. Ver el orden de decisión arriba."""
    declarado = _normalizar(os.environ.get("APP_ENV"))
    if declarado:
        return declarado

    conocido = _BASES_CONOCIDAS.get(_host_puerto(os.environ.get("DATABASE_URL")) or "")
    if conocido:
        return conocido

    return PRODUCCION


def es_produccion() -> bool:
    return get_entorno() == PRODUCCION


def es_pruebas() -> bool:
    return get_entorno() == PRUEBAS


def etiqueta() -> str:
    """Texto corto para títulos de ventana y logs."""
    return "PRODUCCIÓN" if es_produccion() else "PRUEBAS"


def color() -> str:
    """Color del indicador: ámbar en pruebas, azul de la marca en producción."""
    return "#1a365d" if es_produccion() else "#f59e0b"


def descripcion_conexion() -> str:
    """'host:puerto/base' de la conexión actual, SIN contraseña.

    Pensado para mostrarse en pantalla y en logs: sirve para confirmar de un
    vistazo contra qué base se está trabajando sin filtrar credenciales.
    """
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return "sin DATABASE_URL"
    try:
        p = urlparse(dsn)
        base = (p.path or "").lstrip("/") or "?"
        return f"{_host_puerto(dsn)}/{base}"
    except Exception:
        return "conexión no reconocible"


def resumen() -> str:
    """Una línea para el arranque: entorno + a qué base apunta."""
    return f"{etiqueta()} · {descripcion_conexion()}"
