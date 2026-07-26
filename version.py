"""Versión de la aplicación.

Esta constante es la única fuente de verdad de la versión instalada. El
actualizador (`utils/updater.py`) la compara contra la última release publicada
en GitHub para decidir si hay una actualización.

Al publicar una nueva versión hay que subir este número Y crear una release en
GitHub con el mismo tag (ej. `v1.1.0`). El workflow de CI lo hace automático a
partir de este valor.
"""

APP_VERSION = "1.2.5"
