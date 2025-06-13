# financial_cooperative/presenters/main_presenter.py
from views.main_window import MainWindow

class MainPresenter:
    def __init__(self, main_window: MainWindow):
        self.main_window = main_window
        self.main_window.navigate_requested.connect(self.handle_navigation)

        # Aquí podrías instanciar los presenters de cada página si tuvieran lógica inicial
        # self.home_presenter = HomePresenter(self.main_window.home_page, self.model)
        # etc.

    def handle_navigation(self, page_name: str):
        """
        Maneja la solicitud de navegación y cambia la página en la vista.
        """
        self.main_window.set_current_page(page_name)
        print(f"Navegando a la página: {page_name}")

    def show_main_window(self):
        self.main_window.show()