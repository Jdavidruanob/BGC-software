# importar librerías necesarias
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont
import os 

# Importar vistas y el gestor de base de datos
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager 
# Importar configuraciones
from config import (
    DYNAMIC_DATA_BASE_DIR, 
    ASSETS_DIR, 
    DB_PATH_FINAL,
    FISCAL_YEAR, 
    DB_FILE_NAME
)

def main():
    app = QApplication(sys.argv)
    # Cargar fuente Inter Variable
    font_path = os.path.join(ASSETS_DIR, "fonts", "InterVariable.ttf") 
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
        print(f"✅ Fuente '{family}' cargada correctamente.")
    else:
        print("❌ No se pudo cargar la fuente Inter Variable.")

    # Inicializar y conectar la base de datos
    db_path = os.path.join(DYNAMIC_DATA_BASE_DIR, "BGC-software.db")
    db_manager = DBManager(db_path)

    db_needs_migration = False  # Flag para saber si se necesita migración anual
    db_created_now = False      # Flag para saber si la creamos en este instante
    
    # Verificar si la base de datos del año fiscal actual ya existe
    if not os.path.exists(DB_PATH_FINAL):
        print(f"⚠️ Base de datos no encontrada para el año fiscal {FISCAL_YEAR}. Creando nueva DB.")
        db_created_now = True

        # Determinar si existe un año anterior para migrardb_created_now = False # Nuevo flag para saber si la creamos en este instante
        prev_fiscal_year = str(int(FISCAL_YEAR) - 1)
        prev_year_db_folder = os.path.join(os.path.dirname(os.path.dirname(DB_PATH_FINAL)), prev_fiscal_year)
        
        # Si la carpeta del año anterior existe, entonces SÍ es un RESET de año.
        if os.path.exists(prev_year_db_folder):
            db_needs_migration = True
            print(f"✅ Se detectó la carpeta del año anterior ({prev_fiscal_year}). Se necesita migración de saldos.")
            

    # Inicializar y conectar la base de datos
    db_manager = DBManager(DB_PATH_FINAL)

    # El db_manager.connect() creará el archivo DB_PATH_FINAL si no existía.
    if not db_manager.connect():
        print("❌ No se pudo conectar a la base de datos.")
        sys.exit(1)
        
    # 5. Crear la estructura de tablas. Es crucial si el archivo se acaba de crear.
    db_manager.create_tables()  # No sujeta a condicion IF porque dentro de ella ya tiene "if not exists"
    
    # 6. Ejecutar Migración SI y SOLO SI es un reset de año
    # También añadimos una condición para que solo migre si la DB fue creada ahora.
    if db_needs_migration and db_created_now:
        # Construir la ruta al archivo DB del año anterior
        print("Se necesita migracion")
        """ prev_db_path = os.path.join(
            os.path.dirname(os.path.dirname(DB_PATH_FINAL)), prev_fiscal_year, DB_FILE_NAME
        )
        db_manager.run_annual_migration(prev_db_path) """

    # 7. Reseteo de secuencias
    # Esto solo debe correr en la DB nueva. Lo envolvemos en la lógica de creación.
    if db_created_now and not db_needs_migration:
        db_manager.set_sequence_start_value("recibos", 0) 
        
        db_manager.set_sequence_start_value("creditos", 437)
    
            
    # Example members
    """ db_manager.add_member("10101010", "Jose David", " Ruano Burbano", "3111234567", None)
    db_manager.add_member("10101010", "Nathalia Soledad", "Burbano Padilla", "3111234567", None)
    db_manager.add_member("10101010", "Karoll Marcela", "Burabano Padilla", "3111234567", None)
    db_manager.add_member("10101010", "Julieta", "Hoyos Burbano", "3111234567", None)
    db_manager.add_member("10101010", "David Leonardo", "Montilla ibarra", "3111234567", None)
    db_manager.add_member("10101010", "Renata", "Jimenez Burbano", "3111234567", None) """

    # Create main window
    window = MainWindow()
    assistant_page = AssistantPage(db_manager)
    home_page = HomePage(db_manager, assistant_page, window)

    # Create and add new views to the main window
    window.add_view("home", home_page)
    window.add_view("assistant", assistant_page)
    window.add_view("members", MembersPage(db_manager, window))  # Se pasa db_manager y window para acceso a la ventana principal
    window.add_view("data", DataPage())

    window.show_view("home")
    window.show() # Mostrar la ventana principal

    print("✅ Aplicación iniciada correctamente.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
