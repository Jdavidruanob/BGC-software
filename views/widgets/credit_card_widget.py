from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout # Importa QVBoxLayout
from PySide6.QtCore import Qt, Signal
import os
from config import load_styles, format_miles_colombian_int, BASE_APP_DIR # Asegúrate de importar format_miles_colombian_int

class CreditCardWidget(QFrame):
    clicked = Signal(int)  # Emitimos la letra del crédito al hacer clic

    def __init__(self, credito):
        super().__init__()
        self.setObjectName("CreditCardWidget")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80) # <--- **Altura Fija: Ajusta este valor si es necesario**
                                # 80px es un buen tamaño para una fila de información concisa

        self.letra = credito["letra"]
        capital = credito["capital"]
        interes = credito["interes"]
        cuotas = credito["no_cuotas"]

        # Usaremos un QVBoxLayout principal para centrar verticalmente si es necesario
        # y para tener un control más fino del padding/espacio si agregamos más elementos en el futuro.
        # Por ahora, contendrá un QHBoxLayout.
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(15, 0, 15, 0) # Padding horizontal, 0 vertical para controlar con fixedHeight
        main_v_layout.setAlignment(Qt.AlignCenter) # Centra el contenido verticalmente

        content_h_layout = QHBoxLayout() # Usamos QHBoxLayout para los elementos de texto
        content_h_layout.setSpacing(25) # Espaciado entre los diferentes datos (Letra, Capital, etc.)
        content_h_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Alinea a la izquierda y centra verticalmente

        # --- Creación de los QLabel con el formato deseado y sin íconos ---
        # Utilizaremos un solo QLabel grande o varios para mayor control de estilo.
        # Optemos por un solo QLabel con HTML para la flexibilidad del estilo.

        # Elimina los íconos y usa un formato conciso
        # Letra: x  Capital: x  Interes: x No cuotas: x
        summary_text = (
            f"<span style='font-weight: bold; color: #153A66;'>Letra:</span> {self.letra} &nbsp;&nbsp;&nbsp;"
            f"<span style='font-weight: bold; color: #153A66;'>Capital:</span> ${format_miles_colombian_int(capital)} &nbsp;&nbsp;&nbsp;"
            f"<span style='font-weight: bold; color: #153A66;'>Interés:</span> {interes * 100:.2f}% &nbsp;&nbsp;&nbsp;"
            f"<span style='font-weight: bold; color: #153A66;'>Cuotas:</span> {cuotas}"
        )
        
        lbl_summary = QLabel(summary_text)
        lbl_summary.setObjectName("creditSummaryLabel") # Nuevo objectName para un estilo específico
        lbl_summary.setWordWrap(False) # No queremos que se divida el texto en líneas
        
        # Agrega el label al layout horizontal
        content_h_layout.addWidget(lbl_summary)
        content_h_layout.addStretch() # Empuja el texto hacia la izquierda

        # Agrega el layout horizontal al layout vertical principal
        main_v_layout.addLayout(content_h_layout)

        # Cargar estilos QSS
        qss_path = os.path.join(BASE_APP_DIR, "styles", "credit_card_widget.qss")
        load_styles(self, qss_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.letra)
        super().mousePressEvent(event)