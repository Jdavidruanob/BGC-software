import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont

# Importar vistas y el gestor de base de datos
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager 

def main():
    app = QApplication(sys.argv)
    # Cargar fuente Inter Variable
    font_id = QFontDatabase.addApplicationFont("assets/fonts/InterVariable.ttf")
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
        print(f"✅ Fuente '{family}' cargada correctamente.")
    else:
        print("❌ No se pudo cargar la fuente Inter Variable.")

    # Inicializar y conectar la base de datos
    db_path = "BGC-software.db"
    db_manager = DBManager(db_path)

    if not db_manager.connect():
        print("❌ No se pudo conectar a la base de datos.")
        sys.exit(1)

    db_manager.create_tables() # Crea las tablas si no existen
    db_manager.add_member("10101010", "Ejemplo", "socio", "3111234567", None)

    # Crear ventana principal
    window = MainWindow()
    assistant_page = AssistantPage(db_manager)
    home_page = HomePage(db_manager, assistant_page, window)

    # Crear y agregar vistas
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
