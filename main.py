# financial_cooperative/main.py
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from presenters.main_presenter import MainPresenter
from models.database import DatabaseManager

if __name__ == "__main__":
    app = QApplication(sys.argv)

    db_manager = DatabaseManager()
    if not db_manager.connect():
        sys.exit(1) # Salir si no se puede conectar a la BD

    main_window = MainWindow()
    main_presenter = MainPresenter(main_window)
    main_presenter.show_main_window()

    exit_code = app.exec()
    db_manager.close() # Asegurarse de cerrar la conexión a la BD al salir
    sys.exit(exit_code)