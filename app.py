# importar librerías necesarias
import sys

# Forzar salida UTF-8 para que los emojis de los print no rompan la consola de
# Windows (cp1252). Sin esto, `python app.py` falla al arrancar.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont, QIcon
import os 

# Importar vistas y el gestor de base de datos
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager
from services.aporte_service import AporteService
from services.retiro_service import RetiroService
from services.devolucion_total_service import DevolucionTotalService
from services.credito_service import CreditoService
from services.pago_service import PagoService
from services.combinado_service import CombinadoService
from services.caja_service import CajaService
from services.reversion_service import ReversionService
from services.salario_service import SalarioService
# Importar configuraciones
from config import (
    DYNAMIC_DATA_BASE_DIR,
    ASSETS_DIR,
    DB_PATH_FINAL,
    FISCAL_YEAR,
    DB_FILE_NAME,
    BASE_FONT_PT,
    RECIBOS_OUTPUT_DIR,
)
from utils.sync_recibos import sincronizar_recibos
import entorno

def main():
    app = QApplication(sys.argv)

    # 🎯 CARGAR LOGO SVG
    logo_path = os.path.join(ASSETS_DIR, "logo_BGC_grande.svg")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
        print(f"✅ Logo SVG cargado: {logo_path}")
    else:
        print(f"⚠️ Logo no encontrado en: {logo_path}")

    # Cargar fuente Inter Variable
    font_path = os.path.join(ASSETS_DIR, "fonts", "InterVariable.ttf") 
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        base_font = QFont(family)
        base_font.setPointSize(BASE_FONT_PT)   # letra base más grande (adulto mayor)
        app.setFont(base_font)
        print(f"✅ Fuente '{family}' cargada correctamente.")
    else:
        fallback = app.font()
        fallback.setPointSize(BASE_FONT_PT)
        app.setFont(fallback)
        print("❌ No se pudo cargar la fuente Inter Variable.")


    # Conectar a la base de datos compartida en la nube (PostgreSQL).
    # La estructura de la base la administra la API: la app NO crea tablas,
    # NO inicializa config ni ejecuta la "migración anual". Solo lee y escribe
    # datos sobre lo que ya existe. La URL viene de DATABASE_URL (.env).
    db_manager = DBManager()
    if not db_manager.connect():
        print("❌ No se pudo conectar a la base de datos.")
        # Mensaje VISIBLE: la app es --windowed (sin consola), así que sin este
        # diálogo un fallo de conexión se vería como "la app no abre" sin más.
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Sin conexión a la base de datos",
            "No se pudo conectar a la base de datos.\n\n"
            "Revisa que tengas internet y que el archivo «.env» con la línea "
            "DATABASE_URL esté en la misma carpeta del programa.",
        )
        sys.exit(1)

    # Contra qué base se está trabajando. Se imprime DESPUÉS de conectar
    # porque es `connect()` quien carga el .env (y con él APP_ENV).
    print(f"🌐 Entorno: {entorno.resumen()}")

    # Sincronizar la carpeta de recibos con la base: baja los que falten y
    # borra los que ya no existan en la base. No bloquea el arranque si falla.
    sincronizar_recibos(db_manager.conn, RECIBOS_OUTPUT_DIR)

    # Construir servicios inyectando repos desde db_manager
    aporte_svc = AporteService(db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo)
    retiro_svc = RetiroService(db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo)
    credito_svc = CreditoService(db_manager.db_conn, db_manager.creditos_repo, db_manager.auxiliar_repo, db_manager.config_repo)
    pago_svc = PagoService(db_manager.db_conn, db_manager.liquidaciones_repo, db_manager.auxiliar_repo, db_manager.config_repo)
    combinado_svc = CombinadoService(db_manager.db_conn, db_manager.liquidaciones_repo, db_manager.auxiliar_repo, db_manager.config_repo)
    caja_svc = CajaService(db_manager.config_repo, db_manager.auxiliar_repo)
    devolucion_total_svc = DevolucionTotalService(
        db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo,
        db_manager.socios_repo, db_manager.creditos_repo,
    )

    salario_svc = SalarioService(
        db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo,
        db_manager.socios_repo,
    )

    reversion_svc = ReversionService(db_manager.db_conn, db_manager.liquidaciones_repo)

    # Create main window
    window = MainWindow()
    assistant_page = AssistantPage(db_manager, reversion_svc)
    home_page = HomePage(aporte_svc, retiro_svc, pago_svc, credito_svc, combinado_svc,
                         caja_svc, db_manager, assistant_page, window,
                         devolucion_total_svc=devolucion_total_svc,
                         salario_svc=salario_svc)

    # Create and add new views to the main window
    window.add_view("home", home_page)
    window.add_view("assistant", assistant_page)
    window.add_view("members", MembersPage(db_manager, window))  # Se pasa db_manager y window para acceso a la ventana principal
    window.add_view("data", DataPage(db_manager))

    window.show_view("home")
    window.show() # Mostrar la ventana principal

    print("✅ Aplicación iniciada correctamente.")

    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
