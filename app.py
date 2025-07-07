import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager  # Nueva importación
from PySide6.QtGui import QFontDatabase, QFont
import os


def main():
    app = QApplication(sys.argv)

    # ✅ 1. Cargar fuente Inter Variable
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

    db_manager.create_tables()
    """ db_manager.add_credit(
        socio_ids=[3],  # 👈 Lista, incluso si es un solo socio
        capital=20000000,
        interes=0.01,        # 1.5% mensual
        no_cuotas=36
    ) """


    # Crear ventana principal
    window = MainWindow()

    # Crear y agregar vistas (se pasa db_manager si es necesario)
    window.add_view("home", HomePage())
    window.add_view("assistant", AssistantPage(db_manager))
    window.add_view("members", MembersPage(db_manager, window))  # Se pasa db_manager
    window.add_view("data", DataPage())

    window.show_view("home")
    window.show()

    print("✅ Aplicación iniciada correctamente.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
