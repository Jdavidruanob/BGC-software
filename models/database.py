# financial_cooperative/models/database.py
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QMessageBox
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self):
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(DATABASE_PATH)

    def connect(self):
        if not self.db.open():
            QMessageBox.critical(
                None,
                "Error de Conexión",
                f"No se pudo conectar a la base de datos: {self.db.lastError().text()}",
            )
            return False
        self._create_tables() # Crear tablas si no existen
        return True

    def _create_tables(self):
        query = QSqlQuery(self.db)
        # Ejemplo de tabla de usuarios, puedes agregar más
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            );
            """
        )
        # Puedes agregar más CREATE TABLE aquí para tus otros modelos

    def close(self):
        if self.db.isOpen():
            self.db.close()
            print("Conexión a la base de datos cerrada.")

# Para pruebas (opcional, quitar en producción)
if __name__ == "__main__":
    db_manager = DatabaseManager()
    if db_manager.connect():
        print("Conexión a la base de datos exitosa y tablas creadas/verificadas.")
        # Aquí podrías hacer alguna operación de prueba con la base de datos
        db_manager.close()