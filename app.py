import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager  # Nueva importación

def main():
    app = QApplication(sys.argv)

    # Inicializar y conectar la base de datos
    db_path = "BGC-software.db"
    db_manager = DBManager(db_path)

    if not db_manager.connect():
        print("❌ No se pudo conectar a la base de datos.")
        sys.exit(1)

    db_manager.create_tables()

    # Crear ventana principal
    window = MainWindow()

    # Crear y agregar vistas (se pasa db_manager si es necesario)
    window.add_view("home", HomePage())
    window.add_view("assistant", AssistantPage())
    window.add_view("members", MembersPage(db_manager))  # Se pasa db_manager
    window.add_view("data", DataPage())

    window.show_view("home")
    window.show()

    print("✅ Aplicación iniciada correctamente.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
