# views/liquidation_page.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import os
from datetime import datetime
from config import load_styles, format_miles_colombian_int, STYLES_DIR

class CreditLiquidationPage(QWidget):
    def __init__(self, credit, member_id, main_window, db_manager):
        super().__init__()
        self.setObjectName("creditLiquidationPage")
        self.credit = credit
        self.main_window = main_window
        self.member_id = member_id
        self.db_manager = db_manager

        self.setMinimumSize(900, 600)
        self.setWindowTitle("Liquidación del Crédito")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(80, 30, 80, 30)
        main_layout.setSpacing(15)

        # Top bar
        top_bar = QFrame()
        top_bar.setObjectName("liqTopBar")
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        back_btn = QPushButton("← Volver")
        back_btn.setObjectName("liqBackButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.show_view(f"member_detail_{member_id}"))

        title = QLabel("🧾 Liquidación del Crédito")
        title.setObjectName("liqTitle")

        top_bar_layout.addWidget(back_btn)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(title)
        top_bar_layout.addStretch()
        top_bar.setLayout(top_bar_layout)
        main_layout.addWidget(top_bar)

        # Info del crédito
        credit_info = QFrame()
        credit_info.setObjectName("liqHeader")
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(20, 5, 20, 5)
        info_layout.setSpacing(20)

        fields = [
            f"Letra: {credit['letra']}",
            f"Capital: ${format_miles_colombian_int(credit['capital'])}",
            f"Fecha: {credit['fecha_inicio'][:10]}",
            f"Cuotas: {credit['no_cuotas']}"
        ]
        for f in fields:
            lbl = QLabel(f)
            lbl.setObjectName("liqInfoLabel")
            info_layout.addWidget(lbl)

        credit_info.setLayout(info_layout)
        main_layout.addWidget(credit_info)

        socios_label = QLabel(f"👥 Socios participantes: {credit['socios']}")
        socios_label.setObjectName("liqSocios")
        main_layout.addWidget(socios_label)

        # Tabla
        headers = [
            "Fecha Venc.", "Cuota", "Valor Capital", "Intereses",
            "Total Cuota", "Saldo Restante", "Estado / Pago" 
        ]
        self.table = QTableWidget(0, len(headers))
        self.table.setObjectName("liqTableWidget") # ID para el QSS
        self.table.setHorizontalHeaderLabels(headers)
        
        # Ocultar header vertical (números de fila)
        self.table.verticalHeader().setVisible(False)
        
        # Ajustar columnas
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # --- DESACTIVAR INTERACCIÓN (Evita el azul y el click) ---
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus) # <--- IMPORTANTE: Quita el foco azul al hacer click
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False) # Opcional: Quita la rejilla para un look más limpio
        self.table.setAlternatingRowColors(True)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        qss_path = os.path.join(STYLES_DIR, "liquidation_page.qss")
        load_styles(self, qss_path)

        # Cargar datos
        self.load_liquidation_from_db()

    def load_liquidation_from_db(self):
        """Lee cuotas de la BD y aplica colores a TODA LA FILA según estado."""
        letra = self.credit["letra"]
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT fecha_vencimiento, nro_cuota, valor_cuota, interes_mes, 
                       cuota_mensual, saldo_capital, fecha_pago
                FROM liquidaciones
                WHERE credito_letra = ?
                ORDER BY nro_cuota ASC
            """, (letra,))
            
            cuotas = cursor.fetchall()
            self.table.setRowCount(len(cuotas))
            
            hoy_str = datetime.now().strftime("%Y-%m-%d")

            for i, c in enumerate(cuotas):
                # Datos básicos
                f_venc = c["fecha_vencimiento"]
                nro = str(c["nro_cuota"])
                v_cap = f"${format_miles_colombian_int(c['valor_cuota'])}"
                v_int = f"${format_miles_colombian_int(c['interes_mes'])}"
                v_total = f"${format_miles_colombian_int(c['cuota_mensual'])}"
                v_saldo = f"${format_miles_colombian_int(c['saldo_capital'])}"
                
                f_pago = c["fecha_pago"] 

                # LÓGICA DE ESTADO
                estado_text = "Pendiente"
                color_texto = QColor("#333333") # Negro suave por defecto
                es_bold = False

                if f_pago:
                    # PAGADA: Verde y solo fecha
                    estado_text = f_pago 
                    color_texto = QColor("#2E7D32") # Verde
                    es_bold = True
                else:
                    # NO PAGADA
                    if f_venc < hoy_str:
                        # VENCIDA: Rojo
                        estado_text = "VENCIDA"
                        color_texto = QColor("#D32F2F") # Rojo
                        es_bold = True
                    else:
                        # PENDIENTE: Negro
                        estado_text = "Pendiente"

                # Armar fila
                row_data = [f_venc, nro, v_cap, v_int, v_total, v_saldo, estado_text]

                for col, val in enumerate(row_data):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Aplicar color a toda la fila
                    item.setForeground(color_texto)
                    
                    # Aplicar negrita si corresponde (Pagada o Vencida)
                    if es_bold:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    
                    # Nos aseguramos de quitar flags de selección por si acaso
                    item.setFlags(Qt.ItemIsEnabled) 
                    
                    self.table.setItem(i, col, item)

        except Exception as e:
            print(f"❌ Error al cargar liquidación visual: {e}")


    def get_current_balance(self, credit_data):
        """Calcula el saldo actual basandose en la ultima cuota pagada."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT saldo_capital 
                FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NOT NULL 
                ORDER BY nro_cuota DESC LIMIT 1
            """, (credit_data['letra'],))
            row = cursor.fetchone()
            return row['saldo_capital'] if row else credit_data['capital']
        except:
            return credit_data['capital']

    def refresh_view(self):
        self.table.clearContents()
        self.load_liquidation_from_db()