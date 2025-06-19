import sys
from db.db_manager import DBManager

def main():
    # Ruta de la base de datos
    db_path = "BGC-base-de-datos.db"

    # Inicializar y conectar el DBManager
    db_manager = DBManager(db_path)
    if not db_manager.connect():
        print("No se pudo conectar a la base de datos.")
        sys.exit(1)

    # Inicializar las tablas
    db_manager.create_tables()

    print("¡Aplicación inicializada correctamente!")
    db_manager.close()

if __name__ == "__main__":
    main()