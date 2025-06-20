import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage

def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    # Create and add views
    window.add_view("home", HomePage())
    window.add_view("assistant", AssistantPage())
    window.add_view("members", MembersPage())
    window.add_view("data", DataPage())

    # Show initial view
    window.show_view("home")
    window.show()

    print("✅ Aplicación iniciada correctamente.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
