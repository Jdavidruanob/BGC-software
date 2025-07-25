import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont
import sqlite3 
import os # Necesitas os para la ruta
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

    #db_manager.add_member("10101010", "Ejemplo", "socio", "3111234567", None)
    db_manager.set_sequence_start_value("recibos", 230)
    db_manager.set_sequence_start_value("creditos", 437) 

    """ print("\n--- INICIANDO DIAGNÓSTICO DE BASE DE DATOS ---")

    # Re-conectar para asegurar que estamos en el mismo estado de la DB
    # (aunque db_manager.conn ya debería estar conectado)
    conn_check = sqlite3.connect(db_path)
    conn_check.row_factory = sqlite3.Row # Para leer resultados como diccionarios
    cursor_check = conn_check.cursor()

    # 1. Verificar esquema de la tabla 'recibos'
    print("\n--- Esquema de tabla 'recibos' ---")
    cursor_check.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recibos';")
    recibos_schema = cursor_check.fetchone()
    if recibos_schema:
        print(recibos_schema[0])
    else:
        print("Tabla 'recibos' no encontrada en la base de datos.")

    # 2. Verificar esquema de la tabla 'creditos'
    print("\n--- Esquema de tabla 'creditos' ---")
    cursor_check.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='creditos';")
    creditos_schema = cursor_check.fetchone()
    if creditos_schema:
        print(creditos_schema[0])
    else:
        print("Tabla 'creditos' no encontrada en la base de datos.")

    # 3. Verificar el contenido de la tabla 'sqlite_sequence'
    print("\n--- Contenido de la tabla 'sqlite_sequence' ---")
    cursor_check.execute("SELECT * FROM sqlite_sequence;")
    sqlite_seq_data = cursor_check.fetchall()
    if sqlite_seq_data:
        for row in sqlite_seq_data:
            print(dict(row))
    else:
        print("La tabla sqlite_sequence está vacía (posiblemente no hay tablas con AUTOINCREMENT o están recién creadas).")

    # 4. Verificar el máximo ID actual en 'creditos'
    print("\n--- Máximo ID actual en 'creditos' ---")
    cursor_check.execute("SELECT MAX(letra) FROM creditos;")
    max_letra_creditos = cursor_check.fetchone()[0]
    print(f"MAX(letra) en 'creditos': {max_letra_creditos}")

    # 5. Verificar el máximo ID actual en 'recibos'
    print("\n--- Máximo ID actual en 'recibos' ---")
    cursor_check.execute("SELECT MAX(id) FROM recibos;")
    max_id_recibos = cursor_check.fetchone()[0]
    print(f"MAX(id) en 'recibos': {max_id_recibos}")

    conn_check.close()
    print("\n--- DIAGNÓSTICO DE BASE DE DATOS FINALIZADO ---")
    # Fin del bloque de diagnóstico """
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
