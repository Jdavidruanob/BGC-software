# importar librerías necesarias
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont, QIcon
import os 

# Importar vistas y el gestor de base de datos
from views.main_window import MainWindow
from views.home_page import HomePage
from views.assistant_page import AssistantPage
from views.members_page import MembersPage
from views.data_page import DataPage
from db.db_manager import DBManager 
# Importar configuraciones
from config import (
    DYNAMIC_DATA_BASE_DIR, 
    ASSETS_DIR, 
    DB_PATH_FINAL,
    FISCAL_YEAR, 
    DB_FILE_NAME,
    add_historical_credit, add_multiple_historical_credits
)

def main():
    app = QApplication(sys.argv)

    # 🎯 CARGAR LOGO SVG
    logo_path = os.path.join(ASSETS_DIR, "logo_BGC_grande.svg")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
        print(f"✅ Logo SVG cargado: {logo_path}")
    else:
        print(f"⚠️ Logo no encontrado en: {logo_path}")

    # Cargar fuente Inter Variable
    font_path = os.path.join(ASSETS_DIR, "fonts", "InterVariable.ttf") 
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
        print(f"✅ Fuente '{family}' cargada correctamente.")
    else:
        print("❌ No se pudo cargar la fuente Inter Variable.")


    # Inicializar y conectar la base de datos
    db_path = os.path.join(DYNAMIC_DATA_BASE_DIR, "BGC-software.db")
    db_manager = DBManager(db_path)

    db_needs_migration = False  # Flag para saber si se necesita migración anual
    db_created_now = False      # Flag para saber si la creamos en este instante
    
    # Verificar si la base de datos del año fiscal actual ya existe
    if not os.path.exists(DB_PATH_FINAL):
        print(f"⚠️ Base de datos no encontrada para el año fiscal {FISCAL_YEAR}. Creando nueva DB.")
        db_created_now = True

        # Determinar si existe un año anterior para migrardb_created_now = False # Nuevo flag para saber si la creamos en este instante
        prev_fiscal_year = str(int(FISCAL_YEAR) - 1)
        prev_year_db_folder = os.path.join(os.path.dirname(os.path.dirname(DB_PATH_FINAL)), prev_fiscal_year)
        
        # Si la carpeta del año anterior existe, entonces SÍ es un RESET de año.
        if os.path.exists(prev_year_db_folder):
            db_needs_migration = True
            print(f"✅ Se detectó la carpeta del año anterior ({prev_fiscal_year}). Se necesita migración de saldos.")
            

    # Inicializar y conectar la base de datos
    db_manager = DBManager(DB_PATH_FINAL)

    # El db_manager.connect() creará el archivo DB_PATH_FINAL si no existía.
    if not db_manager.connect():
        print("❌ No se pudo conectar a la base de datos.")
        sys.exit(1)
        
    # 5. Crear la estructura de tablas. Es crucial si el archivo se acaba de crear.
    db_manager.create_tables()  # No sujeta a condicion IF porque dentro de ella ya tiene "if not exists"
    
    
    # 6. Ejecutar Migración SI y SOLO SI es un reset de año
    # También añadimos una condición para que solo migre si la DB fue creada ahora.
    if db_needs_migration and db_created_now:
        # Construir la ruta al archivo DB del año anterior
        print("Se necesita migracion")
        """ prev_db_path = os.path.join(
            os.path.dirname(os.path.dirname(DB_PATH_FINAL)), prev_fiscal_year, DB_FILE_NAME
        )
        db_manager.run_annual_migration(prev_db_path) """

    # 7. Reseteo de secuencias
    # Esto solo debe correr en la DB nueva. Lo envolvemos en la lógica de creación.
    if db_created_now and not db_needs_migration:
        db_manager.set_sequence_start_value("recibos", 0) 
        
        db_manager.set_sequence_start_value("creditos", 445)

    credits_list = [
        {
            'letra': 369,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 36,
            'fecha_inicio': '2023-11-08',
            'socios_ids': [3],  # Agregar IDs de Nathalia Burbano P. / David Montilla
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-12-08', 'valor_cuota': 280000, 'interes_mes': 100000, 'cuota_mensual': 380000, 'saldo_capital': 9720000, 'fecha_pago': '2023-12-10'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-01-08', 'valor_cuota': 280000, 'interes_mes': 97200, 'cuota_mensual': 377200, 'saldo_capital': 9440000, 'fecha_pago': '2024-01-07'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-02-08', 'valor_cuota': 280000, 'interes_mes': 94400, 'cuota_mensual': 374400, 'saldo_capital': 9160000, 'fecha_pago': '2024-02-05'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-03-08', 'valor_cuota': 280000, 'interes_mes': 91600, 'cuota_mensual': 371600, 'saldo_capital': 8880000, 'fecha_pago': '2024-03-06'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-04-08', 'valor_cuota': 280000, 'interes_mes': 88800, 'cuota_mensual': 368800, 'saldo_capital': 8600000, 'fecha_pago': '2024-04-02'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-05-08', 'valor_cuota': 280000, 'interes_mes': 86000, 'cuota_mensual': 366000, 'saldo_capital': 8320000, 'fecha_pago': '2024-05-06'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-06-08', 'valor_cuota': 280000, 'interes_mes': 83200, 'cuota_mensual': 363200, 'saldo_capital': 8040000, 'fecha_pago': '2024-06-09'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-07-08', 'valor_cuota': 280000, 'interes_mes': 80400, 'cuota_mensual': 360400, 'saldo_capital': 7760000, 'fecha_pago': '2024-07-10'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-08-08', 'valor_cuota': 280000, 'interes_mes': 77600, 'cuota_mensual': 357600, 'saldo_capital': 7480000, 'fecha_pago': '2024-08-08'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-09-08', 'valor_cuota': 280000, 'interes_mes': 74800, 'cuota_mensual': 354800, 'saldo_capital': 7200000, 'fecha_pago': '2024-09-03'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-10-08', 'valor_cuota': 280000, 'interes_mes': 72000, 'cuota_mensual': 352000, 'saldo_capital': 6920000, 'fecha_pago': '2024-10-07'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-11-08', 'valor_cuota': 280000, 'interes_mes': 69200, 'cuota_mensual': 349200, 'saldo_capital': 6640000, 'fecha_pago': '2024-11-02'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-12-08', 'valor_cuota': 280000, 'interes_mes': 66400, 'cuota_mensual': 346400, 'saldo_capital': 6360000, 'fecha_pago': '2024-12-05'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-01-08', 'valor_cuota': 280000, 'interes_mes': 63600, 'cuota_mensual': 343600, 'saldo_capital': 6080000, 'fecha_pago': '2025-01-03'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-02-08', 'valor_cuota': 280000, 'interes_mes': 60800, 'cuota_mensual': 340800, 'saldo_capital': 5800000, 'fecha_pago': '2025-02-01'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-03-08', 'valor_cuota': 280000, 'interes_mes': 58000, 'cuota_mensual': 338000, 'saldo_capital': 5520000, 'fecha_pago': '2025-03-11'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-04-08', 'valor_cuota': 280000, 'interes_mes': 55200, 'cuota_mensual': 335200, 'saldo_capital': 5240000, 'fecha_pago': '2025-04-13'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-05-08', 'valor_cuota': 280000, 'interes_mes': 52400, 'cuota_mensual': 332400, 'saldo_capital': 4960000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-06-08', 'valor_cuota': 280000, 'interes_mes': 49600, 'cuota_mensual': 329600, 'saldo_capital': 4680000, 'fecha_pago': '2025-06-09'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-07-08', 'valor_cuota': 280000, 'interes_mes': 46800, 'cuota_mensual': 326800, 'saldo_capital': 4400000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-08-08', 'valor_cuota': 280000, 'interes_mes': 44000, 'cuota_mensual': 324000, 'saldo_capital': 4120000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-09-08', 'valor_cuota': 280000, 'interes_mes': 41200, 'cuota_mensual': 321200, 'saldo_capital': 3840000, 'fecha_pago': '2025-09-04'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-10-08', 'valor_cuota': 280000, 'interes_mes': 38400, 'cuota_mensual': 318400, 'saldo_capital': 3560000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-11-08', 'valor_cuota': 280000, 'interes_mes': 35600, 'cuota_mensual': 315600, 'saldo_capital': 3280000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-12-08', 'valor_cuota': 280000, 'interes_mes': 32800, 'cuota_mensual': 312800, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-01-08', 'valor_cuota': 280000, 'interes_mes': 30000, 'cuota_mensual': 310000, 'saldo_capital': 2720000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-02-08', 'valor_cuota': 280000, 'interes_mes': 27200, 'cuota_mensual': 307200, 'saldo_capital': 2440000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-03-08', 'valor_cuota': 280000, 'interes_mes': 24400, 'cuota_mensual': 304400, 'saldo_capital': 2160000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2026-04-08', 'valor_cuota': 280000, 'interes_mes': 21600, 'cuota_mensual': 301600, 'saldo_capital': 1880000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-05-08', 'valor_cuota': 280000, 'interes_mes': 18800, 'cuota_mensual': 298800, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-06-08', 'valor_cuota': 280000, 'interes_mes': 16000, 'cuota_mensual': 296000, 'saldo_capital': 1320000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-07-08', 'valor_cuota': 280000, 'interes_mes': 13200, 'cuota_mensual': 293200, 'saldo_capital': 1040000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-08-08', 'valor_cuota': 280000, 'interes_mes': 10400, 'cuota_mensual': 290400, 'saldo_capital': 760000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2026-09-08', 'valor_cuota': 280000, 'interes_mes': 7600, 'cuota_mensual': 287600, 'saldo_capital': 480000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2026-10-08', 'valor_cuota': 280000, 'interes_mes': 4800, 'cuota_mensual': 284800, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-11-08', 'valor_cuota': 200000, 'interes_mes': 2000, 'cuota_mensual': 202000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },
    ]
    #db_manager.add_multiple_historical_credits(credits_list)
    

    """ # Datos de créditos históricos a agregar
    credits_list = [
        {
            'letra': 425,
            'capital': 20000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 36,
            'fecha_inicio': '2025-04-17',
            'socios_ids': [32,31],  # Agregar IDs de Jesus Rodrigo Garcia D. / Rodrigo Garcia Castro
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-07', 'valor_cuota': 560000, 'interes_mes': 200000, 'cuota_mensual': 760000, 'saldo_capital': 19440000, 'fecha_pago': '2025-05-19'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-17', 'valor_cuota': 560000, 'interes_mes': 194400, 'cuota_mensual': 754400, 'saldo_capital': 18880000, 'fecha_pago': '2025-06-17'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-17', 'valor_cuota': 560000, 'interes_mes': 188800, 'cuota_mensual': 748800, 'saldo_capital': 18320000, 'fecha_pago': '2025-07-17'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-17', 'valor_cuota': 560000, 'interes_mes': 183200, 'cuota_mensual': 743200, 'saldo_capital': 17760000, 'fecha_pago': '2025-08-21'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-17', 'valor_cuota': 560000, 'interes_mes': 177600, 'cuota_mensual': 737600, 'saldo_capital': 17200000, 'fecha_pago': '2025-09-24'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-17', 'valor_cuota': 560000, 'interes_mes': 172000, 'cuota_mensual': 732000, 'saldo_capital': 16640000, 'fecha_pago': '2025-10-16'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-17', 'valor_cuota': 560000, 'interes_mes': 166400, 'cuota_mensual': 726400, 'saldo_capital': 16080000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-17', 'valor_cuota': 560000, 'interes_mes': 160800, 'cuota_mensual': 720800, 'saldo_capital': 15520000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-17', 'valor_cuota': 560000, 'interes_mes': 155200, 'cuota_mensual': 715200, 'saldo_capital': 14960000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-17', 'valor_cuota': 560000, 'interes_mes': 149600, 'cuota_mensual': 709600, 'saldo_capital': 14400000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-17', 'valor_cuota': 560000, 'interes_mes': 144000, 'cuota_mensual': 704000, 'saldo_capital': 13840000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-17', 'valor_cuota': 560000, 'interes_mes': 138400, 'cuota_mensual': 698400, 'saldo_capital': 13280000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-17', 'valor_cuota': 560000, 'interes_mes': 132800, 'cuota_mensual': 692800, 'saldo_capital': 12720000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-06-17', 'valor_cuota': 560000, 'interes_mes': 127200, 'cuota_mensual': 687200, 'saldo_capital': 12160000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-07-17', 'valor_cuota': 560000, 'interes_mes': 121600, 'cuota_mensual': 681600, 'saldo_capital': 11600000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-08-17', 'valor_cuota': 560000, 'interes_mes': 116000, 'cuota_mensual': 676000, 'saldo_capital': 11040000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-09-17', 'valor_cuota': 560000, 'interes_mes': 110400, 'cuota_mensual': 670400, 'saldo_capital': 10480000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-10-17', 'valor_cuota': 560000, 'interes_mes': 104800, 'cuota_mensual': 664800, 'saldo_capital': 9920000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-11-17', 'valor_cuota': 560000, 'interes_mes': 99200, 'cuota_mensual': 659200, 'saldo_capital': 9360000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-12-17', 'valor_cuota': 560000, 'interes_mes': 93600, 'cuota_mensual': 653600, 'saldo_capital': 8800000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-01-17', 'valor_cuota': 560000, 'interes_mes': 88000, 'cuota_mensual': 648000, 'saldo_capital': 8240000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-02-17', 'valor_cuota': 560000, 'interes_mes': 82400, 'cuota_mensual': 642400, 'saldo_capital': 7680000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-03-17', 'valor_cuota': 560000, 'interes_mes': 76800, 'cuota_mensual': 636800, 'saldo_capital': 7120000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-04-17', 'valor_cuota': 560000, 'interes_mes': 71200, 'cuota_mensual': 631200, 'saldo_capital': 6560000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-05-17', 'valor_cuota': 560000, 'interes_mes': 65600, 'cuota_mensual': 625600, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-06-17', 'valor_cuota': 560000, 'interes_mes': 60000, 'cuota_mensual': 620000, 'saldo_capital': 5440000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-07-17', 'valor_cuota': 560000, 'interes_mes': 54400, 'cuota_mensual': 614400, 'saldo_capital': 4880000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-08-17', 'valor_cuota': 560000, 'interes_mes': 48800, 'cuota_mensual': 608800, 'saldo_capital': 4320000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-09-17', 'valor_cuota': 560000, 'interes_mes': 43200, 'cuota_mensual': 603200, 'saldo_capital': 3760000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-10-17', 'valor_cuota': 560000, 'interes_mes': 37600, 'cuota_mensual': 597600, 'saldo_capital': 3200000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-11-17', 'valor_cuota': 560000, 'interes_mes': 32000, 'cuota_mensual': 592000, 'saldo_capital': 2640000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-12-17', 'valor_cuota': 560000, 'interes_mes': 26400, 'cuota_mensual': 586400, 'saldo_capital': 2080000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-01-17', 'valor_cuota': 560000, 'interes_mes': 20800, 'cuota_mensual': 580800, 'saldo_capital': 1520000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-02-17', 'valor_cuota': 560000, 'interes_mes': 15200, 'cuota_mensual': 575200, 'saldo_capital': 960000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-03-17', 'valor_cuota': 560000, 'interes_mes': 9600, 'cuota_mensual': 569600, 'saldo_capital': 400000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-04-17', 'valor_cuota': 400000, 'interes_mes': 4000, 'cuota_mensual': 404000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 411,
            'capital': 12325000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 15,
            'fecha_inicio': '2024-12-14',
            'socios_ids': [21],  # Agregar IDs de Efrain Burbano Garcia / Pilar Del Gastillo
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-01-14', 'valor_cuota': 825000, 'interes_mes': 123250, 'cuota_mensual': 948250, 'saldo_capital': 11500000, 'fecha_pago': '2025-01-07'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-02-14', 'valor_cuota': 825000, 'interes_mes': 115000, 'cuota_mensual': 940000, 'saldo_capital': 10675000, 'fecha_pago': '2025-02-09'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-03-16', 'valor_cuota': 825000, 'interes_mes': 106750, 'cuota_mensual': 931750, 'saldo_capital': 9850000, 'fecha_pago': '2025-04-18'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-04-14', 'valor_cuota': 825000, 'interes_mes': 98500, 'cuota_mensual': 923500, 'saldo_capital': 9025000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-05-14', 'valor_cuota': 825000, 'interes_mes': 90250, 'cuota_mensual': 915250, 'saldo_capital': 8200000, 'fecha_pago': '2025-06-18'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-06-14', 'valor_cuota': 825000, 'interes_mes': 82000, 'cuota_mensual': 907000, 'saldo_capital': 7375000, 'fecha_pago': '2025-07-18'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-07-14', 'valor_cuota': 825000, 'interes_mes': 73750, 'cuota_mensual': 898750, 'saldo_capital': 6550000, 'fecha_pago': '2025-08-28'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-08-14', 'valor_cuota': 825000, 'interes_mes': 65500, 'cuota_mensual': 890500, 'saldo_capital': 5725000, 'fecha_pago': '2025-10-13'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-09-14', 'valor_cuota': 825000, 'interes_mes': 57250, 'cuota_mensual': 882250, 'saldo_capital': 4900000, 'fecha_pago': '2025-11-10'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-10-14', 'valor_cuota': 825000, 'interes_mes': 49000, 'cuota_mensual': 874000, 'saldo_capital': 4075000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-11-14', 'valor_cuota': 825000, 'interes_mes': 40750, 'cuota_mensual': 865750, 'saldo_capital': 3250000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-12-14', 'valor_cuota': 825000, 'interes_mes': 32500, 'cuota_mensual': 857500, 'saldo_capital': 2425000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-01-14', 'valor_cuota': 825000, 'interes_mes': 24250, 'cuota_mensual': 849250, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-02-14', 'valor_cuota': 825000, 'interes_mes': 16000, 'cuota_mensual': 841000, 'saldo_capital': 775000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-03-16', 'valor_cuota': 775000, 'interes_mes': 7750, 'cuota_mensual': 782750, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 369,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 36,
            'fecha_inicio': '2023-11-08',
            'socios_ids': [3],  # Agregar IDs de Nathalia Burbano P. / David Montilla
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-12-08', 'valor_cuota': 280000, 'interes_mes': 100000, 'cuota_mensual': 380000, 'saldo_capital': 9720000, 'fecha_pago': '2023-12-10'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-01-08', 'valor_cuota': 280000, 'interes_mes': 97200, 'cuota_mensual': 377200, 'saldo_capital': 9440000, 'fecha_pago': '2024-01-07'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-02-08', 'valor_cuota': 280000, 'interes_mes': 94400, 'cuota_mensual': 374400, 'saldo_capital': 9160000, 'fecha_pago': '2024-02-05'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-03-08', 'valor_cuota': 280000, 'interes_mes': 91600, 'cuota_mensual': 371600, 'saldo_capital': 8880000, 'fecha_pago': '2024-03-06'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-04-08', 'valor_cuota': 280000, 'interes_mes': 88800, 'cuota_mensual': 368800, 'saldo_capital': 8600000, 'fecha_pago': '2024-04-02'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-05-08', 'valor_cuota': 280000, 'interes_mes': 86000, 'cuota_mensual': 366000, 'saldo_capital': 8320000, 'fecha_pago': '2024-05-06'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-06-08', 'valor_cuota': 280000, 'interes_mes': 83200, 'cuota_mensual': 363200, 'saldo_capital': 8040000, 'fecha_pago': '2024-06-09'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-07-08', 'valor_cuota': 280000, 'interes_mes': 80400, 'cuota_mensual': 360400, 'saldo_capital': 7760000, 'fecha_pago': '2024-07-10'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-08-08', 'valor_cuota': 280000, 'interes_mes': 77600, 'cuota_mensual': 357600, 'saldo_capital': 7480000, 'fecha_pago': '2024-08-08'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-09-08', 'valor_cuota': 280000, 'interes_mes': 74800, 'cuota_mensual': 354800, 'saldo_capital': 7200000, 'fecha_pago': '2024-09-03'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-10-08', 'valor_cuota': 280000, 'interes_mes': 72000, 'cuota_mensual': 352000, 'saldo_capital': 6920000, 'fecha_pago': '2024-10-07'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-11-08', 'valor_cuota': 280000, 'interes_mes': 69200, 'cuota_mensual': 349200, 'saldo_capital': 6640000, 'fecha_pago': '2024-11-02'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-12-08', 'valor_cuota': 280000, 'interes_mes': 66400, 'cuota_mensual': 346400, 'saldo_capital': 6360000, 'fecha_pago': '2024-12-05'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-01-08', 'valor_cuota': 280000, 'interes_mes': 63600, 'cuota_mensual': 343600, 'saldo_capital': 6080000, 'fecha_pago': '2025-01-03'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-02-08', 'valor_cuota': 280000, 'interes_mes': 60800, 'cuota_mensual': 340800, 'saldo_capital': 5800000, 'fecha_pago': '2025-02-01'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-03-08', 'valor_cuota': 280000, 'interes_mes': 58000, 'cuota_mensual': 338000, 'saldo_capital': 5520000, 'fecha_pago': '2025-03-11'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-04-08', 'valor_cuota': 280000, 'interes_mes': 55200, 'cuota_mensual': 335200, 'saldo_capital': 5240000, 'fecha_pago': '2025-04-13'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-05-08', 'valor_cuota': 280000, 'interes_mes': 52400, 'cuota_mensual': 332400, 'saldo_capital': 4960000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-06-08', 'valor_cuota': 280000, 'interes_mes': 49600, 'cuota_mensual': 329600, 'saldo_capital': 4680000, 'fecha_pago': '2025-06-09'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-07-08', 'valor_cuota': 280000, 'interes_mes': 46800, 'cuota_mensual': 326800, 'saldo_capital': 4400000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-08-08', 'valor_cuota': 280000, 'interes_mes': 44000, 'cuota_mensual': 324000, 'saldo_capital': 4120000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-09-08', 'valor_cuota': 280000, 'interes_mes': 41200, 'cuota_mensual': 321200, 'saldo_capital': 3840000, 'fecha_pago': '2025-09-04'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-10-08', 'valor_cuota': 280000, 'interes_mes': 38400, 'cuota_mensual': 318400, 'saldo_capital': 3560000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-11-08', 'valor_cuota': 280000, 'interes_mes': 35600, 'cuota_mensual': 315600, 'saldo_capital': 3280000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-12-08', 'valor_cuota': 280000, 'interes_mes': 32800, 'cuota_mensual': 312800, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-01-08', 'valor_cuota': 280000, 'interes_mes': 30000, 'cuota_mensual': 310000, 'saldo_capital': 2720000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-02-08', 'valor_cuota': 280000, 'interes_mes': 27200, 'cuota_mensual': 307200, 'saldo_capital': 2440000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-03-08', 'valor_cuota': 280000, 'interes_mes': 24400, 'cuota_mensual': 304400, 'saldo_capital': 2160000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2026-04-08', 'valor_cuota': 280000, 'interes_mes': 21600, 'cuota_mensual': 301600, 'saldo_capital': 1880000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-05-08', 'valor_cuota': 280000, 'interes_mes': 18800, 'cuota_mensual': 298800, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-06-08', 'valor_cuota': 280000, 'interes_mes': 16000, 'cuota_mensual': 296000, 'saldo_capital': 1320000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-07-08', 'valor_cuota': 280000, 'interes_mes': 13200, 'cuota_mensual': 293200, 'saldo_capital': 1040000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-08-08', 'valor_cuota': 280000, 'interes_mes': 10400, 'cuota_mensual': 290400, 'saldo_capital': 760000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2026-09-08', 'valor_cuota': 280000, 'interes_mes': 7600, 'cuota_mensual': 287600, 'saldo_capital': 480000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2026-10-08', 'valor_cuota': 280000, 'interes_mes': 4800, 'cuota_mensual': 284800, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-11-08', 'valor_cuota': 200000, 'interes_mes': 2000, 'cuota_mensual': 202000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 426,
            'capital': 2000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 12,
            'fecha_inicio': '2025-04-27',
            'socios_ids': [3],  # Agregar IDs de Nathalia Burbano Padilla / David Montilla
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-27', 'valor_cuota': 170000, 'interes_mes': 20000, 'cuota_mensual': 190000, 'saldo_capital': 1830000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-27', 'valor_cuota': 170000, 'interes_mes': 18300, 'cuota_mensual': 188300, 'saldo_capital': 1660000, 'fecha_pago': '2025-06-09'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-27', 'valor_cuota': 170000, 'interes_mes': 16600, 'cuota_mensual': 186600, 'saldo_capital': 1490000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-27', 'valor_cuota': 170000, 'interes_mes': 14900, 'cuota_mensual': 184900, 'saldo_capital': 1320000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-27', 'valor_cuota': 170000, 'interes_mes': 13200, 'cuota_mensual': 183200, 'saldo_capital': 1150000, 'fecha_pago': '2025-09-04'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-27', 'valor_cuota': 170000, 'interes_mes': 11500, 'cuota_mensual': 181500, 'saldo_capital': 980000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-27', 'valor_cuota': 170000, 'interes_mes': 9800, 'cuota_mensual': 179800, 'saldo_capital': 810000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-27', 'valor_cuota': 170000, 'interes_mes': 8100, 'cuota_mensual': 178100, 'saldo_capital': 640000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-27', 'valor_cuota': 170000, 'interes_mes': 6400, 'cuota_mensual': 176400, 'saldo_capital': 470000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-27', 'valor_cuota': 170000, 'interes_mes': 4700, 'cuota_mensual': 174700, 'saldo_capital': 300000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-27', 'valor_cuota': 170000, 'interes_mes': 3000, 'cuota_mensual': 173000, 'saldo_capital': 130000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-27', 'valor_cuota': 130000, 'interes_mes': 1300, 'cuota_mensual': 131300, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 342,
            'capital': 20000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 36,
            'fecha_inicio': '2023-01-28',
            'socios_ids': [23],  # Agregar IDs de Ana Nereyda Burbano / Javier M. Castro Burbano
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-02-28', 'valor_cuota': 560000, 'interes_mes': 200000, 'cuota_mensual': 760000, 'saldo_capital': 19440000, 'fecha_pago': '2023-03-16'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2023-03-28', 'valor_cuota': 560000, 'interes_mes': 194400, 'cuota_mensual': 754400, 'saldo_capital': 18880000, 'fecha_pago': '2023-04-1'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2023-04-28', 'valor_cuota': 560000, 'interes_mes': 188800, 'cuota_mensual': 748800, 'saldo_capital': 18320000, 'fecha_pago': '2023-05-03'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2023-05-28', 'valor_cuota': 560000, 'interes_mes': 183200, 'cuota_mensual': 743200, 'saldo_capital': 17760000, 'fecha_pago': '2023-06-14'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2023-06-28', 'valor_cuota': 560000, 'interes_mes': 177600, 'cuota_mensual': 737600, 'saldo_capital': 17200000, 'fecha_pago': '2023-07-11'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2023-07-28', 'valor_cuota': 560000, 'interes_mes': 172000, 'cuota_mensual': 732000, 'saldo_capital': 16640000, 'fecha_pago': '2023-08-25'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2023-08-28', 'valor_cuota': 560000, 'interes_mes': 166400, 'cuota_mensual': 726400, 'saldo_capital': 16080000, 'fecha_pago': '2023-09-10'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2023-09-28', 'valor_cuota': 560000, 'interes_mes': 160800, 'cuota_mensual': 720800, 'saldo_capital': 15520000, 'fecha_pago': '2023-10-25'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2023-10-28', 'valor_cuota': 560000, 'interes_mes': 155200, 'cuota_mensual': 715200, 'saldo_capital': 14960000, 'fecha_pago': '2023-11-29'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2023-11-28', 'valor_cuota': 560000, 'interes_mes': 149600, 'cuota_mensual': 709600, 'saldo_capital': 14400000, 'fecha_pago': '2023-12-06'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2023-12-28', 'valor_cuota': 560000, 'interes_mes': 144000, 'cuota_mensual': 704000, 'saldo_capital': 13840000, 'fecha_pago': '2024-01-11'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-01-28', 'valor_cuota': 560000, 'interes_mes': 138400, 'cuota_mensual': 698400, 'saldo_capital': 13280000, 'fecha_pago': '2024-02-27'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-02-28', 'valor_cuota': 560000, 'interes_mes': 132800, 'cuota_mensual': 692800, 'saldo_capital': 12720000, 'fecha_pago': '2024-03-26'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2024-03-28', 'valor_cuota': 560000, 'interes_mes': 127200, 'cuota_mensual': 687200, 'saldo_capital': 12160000, 'fecha_pago': '2024-04-11'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2024-04-28', 'valor_cuota': 560000, 'interes_mes': 121600, 'cuota_mensual': 681600, 'saldo_capital': 11600000, 'fecha_pago': '2024-05-22'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2024-05-28', 'valor_cuota': 560000, 'interes_mes': 116000, 'cuota_mensual': 676000, 'saldo_capital': 11040000, 'fecha_pago': '2024-06-9'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2024-06-28', 'valor_cuota': 560000, 'interes_mes': 110400, 'cuota_mensual': 670400, 'saldo_capital': 10480000, 'fecha_pago': '2024-07-15'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2024-07-28', 'valor_cuota': 560000, 'interes_mes': 104800, 'cuota_mensual': 664800, 'saldo_capital': 9920000, 'fecha_pago': '2024-08-27'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2024-08-28', 'valor_cuota': 560000, 'interes_mes': 99200, 'cuota_mensual': 659200, 'saldo_capital': 9360000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2024-09-28', 'valor_cuota': 560000, 'interes_mes': 93600, 'cuota_mensual': 653600, 'saldo_capital': 8800000, 'fecha_pago': '2024-10-26'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2024-10-28', 'valor_cuota': 560000, 'interes_mes': 88000, 'cuota_mensual': 648000, 'saldo_capital': 8240000, 'fecha_pago': '2024-11-29'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2024-11-28', 'valor_cuota': 560000, 'interes_mes': 82400, 'cuota_mensual': 642400, 'saldo_capital': 7680000, 'fecha_pago': '2025-01-03'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2024-12-28', 'valor_cuota': 560000, 'interes_mes': 76800, 'cuota_mensual': 636800, 'saldo_capital': 7120000, 'fecha_pago': '2025-01-09'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-01-28', 'valor_cuota': 560000, 'interes_mes': 71200, 'cuota_mensual': 631200, 'saldo_capital': 6560000, 'fecha_pago': '2025-02-25'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-02-28', 'valor_cuota': 560000, 'interes_mes': 65600, 'cuota_mensual': 625600, 'saldo_capital': 6000000, 'fecha_pago': '2025-03-11'},
                {'nro_cuota': 26, 'fecha_vencimiento': '2025-03-28', 'valor_cuota': 560000, 'interes_mes': 60000, 'cuota_mensual': 620000, 'saldo_capital': 5440000, 'fecha_pago': '2025-04-18'},
                {'nro_cuota': 27, 'fecha_vencimiento': '2025-04-28', 'valor_cuota': 560000, 'interes_mes': 54400, 'cuota_mensual': 614400, 'saldo_capital': 4880000, 'fecha_pago': '2025-05-16'},
                {'nro_cuota': 28, 'fecha_vencimiento': '2025-05-28', 'valor_cuota': 560000, 'interes_mes': 48800, 'cuota_mensual': 608800, 'saldo_capital': 4320000, 'fecha_pago': '2025-06-28'},
                {'nro_cuota': 29, 'fecha_vencimiento': '2025-06-28', 'valor_cuota': 560000, 'interes_mes': 43200, 'cuota_mensual': 603200, 'saldo_capital': 3760000, 'fecha_pago': '2025-07-02'},
                {'nro_cuota': 30, 'fecha_vencimiento': '2025-07-28', 'valor_cuota': 560000, 'interes_mes': 37600, 'cuota_mensual': 597600, 'saldo_capital': 3200000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 31, 'fecha_vencimiento': '2025-08-28', 'valor_cuota': 560000, 'interes_mes': 32000, 'cuota_mensual': 592000, 'saldo_capital': 2640000, 'fecha_pago': '2025-09-07'},
                {'nro_cuota': 32, 'fecha_vencimiento': '2025-09-28', 'valor_cuota': 560000, 'interes_mes': 26400, 'cuota_mensual': 586400, 'saldo_capital': 2080000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 33, 'fecha_vencimiento': '2025-10-28', 'valor_cuota': 560000, 'interes_mes': 20800, 'cuota_mensual': 580800, 'saldo_capital': 1520000, 'fecha_pago': '2025-11-13'},
                {'nro_cuota': 34, 'fecha_vencimiento': '2025-11-28', 'valor_cuota': 560000, 'interes_mes': 15200, 'cuota_mensual': 575200, 'saldo_capital': 960000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2025-12-28', 'valor_cuota': 560000, 'interes_mes': 9600, 'cuota_mensual': 569600, 'saldo_capital': 400000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-01-28', 'valor_cuota': 400000, 'interes_mes': 4000, 'cuota_mensual': 404000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 423,
            'capital': 3000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 24,
            'fecha_inicio': '2025-04-03',
            'socios_ids': [24],  # Agregar IDs de Javier Mauricio Castro Burbano / Ana Nereyda Burbano Garcia
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-03', 'valor_cuota': 125000, 'interes_mes': 30000, 'cuota_mensual': 155000, 'saldo_capital': 2875000, 'fecha_pago': '2025-05-16'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-03', 'valor_cuota': 125000, 'interes_mes': 28750, 'cuota_mensual': 153750, 'saldo_capital': 2750000, 'fecha_pago': '2025-06-29'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-03', 'valor_cuota': 125000, 'interes_mes': 27500, 'cuota_mensual': 152500, 'saldo_capital': 2625000, 'fecha_pago': '2025-07-28'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-03', 'valor_cuota': 125000, 'interes_mes': 26250, 'cuota_mensual': 151250, 'saldo_capital': 2500000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-03', 'valor_cuota': 125000, 'interes_mes': 25000, 'cuota_mensual': 150000, 'saldo_capital': 2375000, 'fecha_pago': '2025-09-30'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-03', 'valor_cuota': 125000, 'interes_mes': 23750, 'cuota_mensual': 148750, 'saldo_capital': 2250000, 'fecha_pago': '2025-09-30'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-03', 'valor_cuota': 125000, 'interes_mes': 22500, 'cuota_mensual': 147500, 'saldo_capital': 2125000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-03', 'valor_cuota': 125000, 'interes_mes': 21250, 'cuota_mensual': 146250, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-03', 'valor_cuota': 125000, 'interes_mes': 20000, 'cuota_mensual': 145000, 'saldo_capital': 1875000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-03', 'valor_cuota': 125000, 'interes_mes': 18750, 'cuota_mensual': 143750, 'saldo_capital': 1750000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-03', 'valor_cuota': 125000, 'interes_mes': 17500, 'cuota_mensual': 142500, 'saldo_capital': 1625000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-03', 'valor_cuota': 125000, 'interes_mes': 16250, 'cuota_mensual': 141250, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-03', 'valor_cuota': 125000, 'interes_mes': 15000, 'cuota_mensual': 140000, 'saldo_capital': 1375000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-06-03', 'valor_cuota': 125000, 'interes_mes': 13750, 'cuota_mensual': 138750, 'saldo_capital': 1250000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-07-03', 'valor_cuota': 125000, 'interes_mes': 12500, 'cuota_mensual': 137500, 'saldo_capital': 1125000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-08-03', 'valor_cuota': 125000, 'interes_mes': 11250, 'cuota_mensual': 136250, 'saldo_capital': 1000000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-09-03', 'valor_cuota': 125000, 'interes_mes': 10000, 'cuota_mensual': 135000, 'saldo_capital': 875000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-10-03', 'valor_cuota': 125000, 'interes_mes': 8750, 'cuota_mensual': 133750, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-11-03', 'valor_cuota': 125000, 'interes_mes': 7500, 'cuota_mensual': 132500, 'saldo_capital': 625000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-12-03', 'valor_cuota': 125000, 'interes_mes': 6250, 'cuota_mensual': 131250, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-01-03', 'valor_cuota': 125000, 'interes_mes': 5000, 'cuota_mensual': 130000, 'saldo_capital': 375000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-02-03', 'valor_cuota': 125000, 'interes_mes': 3750, 'cuota_mensual': 128750, 'saldo_capital': 250000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-03-03', 'valor_cuota': 125000, 'interes_mes': 2500, 'cuota_mensual': 127500, 'saldo_capital': 125000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-04-03', 'valor_cuota': 125000, 'interes_mes': 1250, 'cuota_mensual': 126250, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 376,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% según el documento
            'no_cuotas': 36,
            'fecha_inicio': '2023-11-08',
            'socios_ids': [25],  # Agregar IDs de Ayda B. Burbano G. / Juan Carlos Moreno
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-04-09', 'valor_cuota': 280000, 'interes_mes': 100000, 'cuota_mensual': 380000, 'saldo_capital': 9720000, 'fecha_pago': '2024-04-11'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-05-09', 'valor_cuota': 280000, 'interes_mes': 97200, 'cuota_mensual': 377200, 'saldo_capital': 9440000, 'fecha_pago': '2024-05-22'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-06-09', 'valor_cuota': 280000, 'interes_mes': 94400, 'cuota_mensual': 374400, 'saldo_capital': 9160000, 'fecha_pago': '2024-06-09'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-07-09', 'valor_cuota': 280000, 'interes_mes': 91600, 'cuota_mensual': 371600, 'saldo_capital': 8880000, 'fecha_pago': '2024-07-15'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-08-09', 'valor_cuota': 280000, 'interes_mes': 88800, 'cuota_mensual': 368800, 'saldo_capital': 8600000, 'fecha_pago': '2024-08-27'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-09-09', 'valor_cuota': 280000, 'interes_mes': 86000, 'cuota_mensual': 366000, 'saldo_capital': 8320000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-10-09', 'valor_cuota': 280000, 'interes_mes': 83200, 'cuota_mensual': 363200, 'saldo_capital': 8040000, 'fecha_pago': '2024-10-26'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-11-09', 'valor_cuota': 280000, 'interes_mes': 80400, 'cuota_mensual': 360400, 'saldo_capital': 7760000, 'fecha_pago': '2024-11-29'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-12-09', 'valor_cuota': 280000, 'interes_mes': 77600, 'cuota_mensual': 357600, 'saldo_capital': 7480000, 'fecha_pago': '2025-01-03'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-01-09', 'valor_cuota': 280000, 'interes_mes': 74800, 'cuota_mensual': 354800, 'saldo_capital': 7200000, 'fecha_pago': '2025-01-09'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-02-09', 'valor_cuota': 280000, 'interes_mes': 72000, 'cuota_mensual': 352000, 'saldo_capital': 6920000, 'fecha_pago': '2025-02-25'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-03-09', 'valor_cuota': 280000, 'interes_mes': 69200, 'cuota_mensual': 349200, 'saldo_capital': 6640000, 'fecha_pago': '2025-03-11'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-04-09', 'valor_cuota': 280000, 'interes_mes': 66400, 'cuota_mensual': 346400, 'saldo_capital': 6360000, 'fecha_pago': '2025-04-18'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-05-09', 'valor_cuota': 280000, 'interes_mes': 63600, 'cuota_mensual': 343600, 'saldo_capital': 6080000, 'fecha_pago': '2025-05-16'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-06-09', 'valor_cuota': 280000, 'interes_mes': 60800, 'cuota_mensual': 340800, 'saldo_capital': 5800000, 'fecha_pago': '2025-06-29'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-07-09', 'valor_cuota': 280000, 'interes_mes': 58000, 'cuota_mensual': 338000, 'saldo_capital': 5520000, 'fecha_pago': '2025-07-27'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-08-09', 'valor_cuota': 280000, 'interes_mes': 55200, 'cuota_mensual': 335200, 'saldo_capital': 5240000, 'fecha_pago': '2025-08-07'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-09-09', 'valor_cuota': 280000, 'interes_mes': 52400, 'cuota_mensual': 332400, 'saldo_capital': 4960000, 'fecha_pago': '2025-09-30'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-10-09', 'valor_cuota': 280000, 'interes_mes': 49600, 'cuota_mensual': 329600, 'saldo_capital': 4680000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-11-09', 'valor_cuota': 280000, 'interes_mes': 46800, 'cuota_mensual': 326800, 'saldo_capital': 4400000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-12-09', 'valor_cuota': 280000, 'interes_mes': 44000, 'cuota_mensual': 324000, 'saldo_capital': 4120000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-01-09', 'valor_cuota': 280000, 'interes_mes': 41200, 'cuota_mensual': 321200, 'saldo_capital': 3840000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-02-09', 'valor_cuota': 280000, 'interes_mes': 38400, 'cuota_mensual': 318400, 'saldo_capital': 3560000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-03-09', 'valor_cuota': 280000, 'interes_mes': 35600, 'cuota_mensual': 315600, 'saldo_capital': 3280000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2026-04-09', 'valor_cuota': 280000, 'interes_mes': 32800, 'cuota_mensual': 312800, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-05-09', 'valor_cuota': 280000, 'interes_mes': 30000, 'cuota_mensual': 310000, 'saldo_capital': 2720000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-06-09', 'valor_cuota': 280000, 'interes_mes': 27200, 'cuota_mensual': 307200, 'saldo_capital': 2440000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-07-09', 'valor_cuota': 280000, 'interes_mes': 24400, 'cuota_mensual': 304400, 'saldo_capital': 2160000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2026-08-09', 'valor_cuota': 280000, 'interes_mes': 21600, 'cuota_mensual': 301600, 'saldo_capital': 1880000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-09-09', 'valor_cuota': 280000, 'interes_mes': 18800, 'cuota_mensual': 298800, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-10-09', 'valor_cuota': 280000, 'interes_mes': 16000, 'cuota_mensual': 296000, 'saldo_capital': 1320000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-11-09', 'valor_cuota': 280000, 'interes_mes': 13200, 'cuota_mensual': 293200, 'saldo_capital': 1040000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-12-09', 'valor_cuota': 280000, 'interes_mes': 10400, 'cuota_mensual': 290400, 'saldo_capital': 760000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-01-09', 'valor_cuota': 280000, 'interes_mes': 7600, 'cuota_mensual': 287600, 'saldo_capital': 480000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-02-09', 'valor_cuota': 280000, 'interes_mes': 4800, 'cuota_mensual': 284800, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-03-09', 'valor_cuota': 200000, 'interes_mes': 2000, 'cuota_mensual': 202000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 443,
            'capital': 25000000,
            'interes': 0.01,  # 1,00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-10-03',
            'socios': [25],
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2026-11-03', 'valor_cuota': 695000, 'interes_mes': 250000, 'cuota_mensual': 945000, 'saldo_capital': 24305000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2026-12-03', 'valor_cuota': 695000, 'interes_mes': 243050, 'cuota_mensual': 938050, 'saldo_capital': 23610000, 'fecha_pago': None},
                {'nro_cuota': 3, 'fecha_vencimiento': '2027-01-03', 'valor_cuota': 695000, 'interes_mes': 236100, 'cuota_mensual': 931100, 'saldo_capital': 22915000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2027-02-03', 'valor_cuota': 695000, 'interes_mes': 229150, 'cuota_mensual': 924150, 'saldo_capital': 22220000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2027-03-03', 'valor_cuota': 695000, 'interes_mes': 222200, 'cuota_mensual': 917200, 'saldo_capital': 21525000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2027-04-03', 'valor_cuota': 695000, 'interes_mes': 215250, 'cuota_mensual': 910250, 'saldo_capital': 20830000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2027-05-03', 'valor_cuota': 695000, 'interes_mes': 208300, 'cuota_mensual': 903300, 'saldo_capital': 20135000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2027-06-03', 'valor_cuota': 695000, 'interes_mes': 201350, 'cuota_mensual': 896350, 'saldo_capital': 19440000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2027-07-03', 'valor_cuota': 695000, 'interes_mes': 194400, 'cuota_mensual': 889400, 'saldo_capital': 18745000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2027-08-03', 'valor_cuota': 695000, 'interes_mes': 187450, 'cuota_mensual': 882450, 'saldo_capital': 18050000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2027-09-03', 'valor_cuota': 695000, 'interes_mes': 180500, 'cuota_mensual': 875500, 'saldo_capital': 17355000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2027-10-03', 'valor_cuota': 695000, 'interes_mes': 173550, 'cuota_mensual': 868550, 'saldo_capital': 16660000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2027-11-03', 'valor_cuota': 695000, 'interes_mes': 166600, 'cuota_mensual': 861600, 'saldo_capital': 15965000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2027-12-03', 'valor_cuota': 695000, 'interes_mes': 159650, 'cuota_mensual': 854650, 'saldo_capital': 15270000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2028-01-03', 'valor_cuota': 695000, 'interes_mes': 152700, 'cuota_mensual': 847700, 'saldo_capital': 14575000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2028-02-03', 'valor_cuota': 695000, 'interes_mes': 145750, 'cuota_mensual': 840750, 'saldo_capital': 13880000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2028-03-03', 'valor_cuota': 695000, 'interes_mes': 138800, 'cuota_mensual': 833800, 'saldo_capital': 13185000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2028-04-03', 'valor_cuota': 695000, 'interes_mes': 131850, 'cuota_mensual': 826850, 'saldo_capital': 12490000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2028-11-03', 'valor_cuota': 695000, 'interes_mes': 124900, 'cuota_mensual': 819900, 'saldo_capital': 11795000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2028-12-03', 'valor_cuota': 695000, 'interes_mes': 117950, 'cuota_mensual': 812950, 'saldo_capital': 11100000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2029-01-03', 'valor_cuota': 695000, 'interes_mes': 111000, 'cuota_mensual': 806000, 'saldo_capital': 10405000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2029-02-03', 'valor_cuota': 695000, 'interes_mes': 104050, 'cuota_mensual': 799050, 'saldo_capital': 9710000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2029-03-03', 'valor_cuota': 695000, 'interes_mes': 97100, 'cuota_mensual': 792100, 'saldo_capital': 9015000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2029-04-03', 'valor_cuota': 695000, 'interes_mes': 90150, 'cuota_mensual': 785150, 'saldo_capital': 8320000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2029-05-03', 'valor_cuota': 695000, 'interes_mes': 83200, 'cuota_mensual': 778200, 'saldo_capital': 7625000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2029-06-03', 'valor_cuota': 695000, 'interes_mes': 76250, 'cuota_mensual': 771250, 'saldo_capital': 6930000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2029-07-03', 'valor_cuota': 695000, 'interes_mes': 69300, 'cuota_mensual': 764300, 'saldo_capital': 6235000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2029-08-03', 'valor_cuota': 695000, 'interes_mes': 62350, 'cuota_mensual': 757350, 'saldo_capital': 5540000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2029-09-03', 'valor_cuota': 695000, 'interes_mes': 55400, 'cuota_mensual': 750400, 'saldo_capital': 4845000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2029-10-03', 'valor_cuota': 695000, 'interes_mes': 48450, 'cuota_mensual': 743450, 'saldo_capital': 4150000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2029-11-03', 'valor_cuota': 695000, 'interes_mes': 41500, 'cuota_mensual': 736500, 'saldo_capital': 3455000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2029-12-03', 'valor_cuota': 695000, 'interes_mes': 34550, 'cuota_mensual': 729550, 'saldo_capital': 2760000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2030-01-03', 'valor_cuota': 695000, 'interes_mes': 27600, 'cuota_mensual': 722600, 'saldo_capital': 2065000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2030-02-03', 'valor_cuota': 695000, 'interes_mes': 20650, 'cuota_mensual': 715650, 'saldo_capital': 1370000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2030-03-03', 'valor_cuota': 695000, 'interes_mes': 13700, 'cuota_mensual': 708700, 'saldo_capital': 675000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2030-04-03', 'valor_cuota': 675000, 'interes_mes': 6750, 'cuota_mensual': 681750, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 424,
            'capital': 11000000,
            'interes': 0.01,
            'no_cuotas': 13,
            'fecha_inicio': '2025-04-07',
            'socios_ids': [28],
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-07', 'valor_cuota': 850000, 'interes_mes': 110000, 'cuota_mensual': 960000, 'saldo_capital': 10150000, 'fecha_pago': '2025-05-26'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-07', 'valor_cuota': 850000, 'interes_mes': 101500, 'cuota_mensual': 951500, 'saldo_capital': 9300000, 'fecha_pago': '2025-08-15'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-07', 'valor_cuota': 850000, 'interes_mes': 93000, 'cuota_mensual': 943000, 'saldo_capital': 8450000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-07', 'valor_cuota': 850000, 'interes_mes': 84500, 'cuota_mensual': 934500, 'saldo_capital': 7600000, 'fecha_pago': '2025-11-11'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-07', 'valor_cuota': 850000, 'interes_mes': 76000, 'cuota_mensual': 926000, 'saldo_capital': 6750000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-07', 'valor_cuota': 850000, 'interes_mes': 67500, 'cuota_mensual': 917500, 'saldo_capital': 5900000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-07', 'valor_cuota': 850000, 'interes_mes': 59000, 'cuota_mensual': 909000, 'saldo_capital': 5050000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-07', 'valor_cuota': 850000, 'interes_mes': 50500, 'cuota_mensual': 900500, 'saldo_capital': 4200000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-07', 'valor_cuota': 850000, 'interes_mes': 42000, 'cuota_mensual': 892000, 'saldo_capital': 3350000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-07', 'valor_cuota': 850000, 'interes_mes': 33500, 'cuota_mensual': 883500, 'saldo_capital': 2500000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-07', 'valor_cuota': 850000, 'interes_mes': 25000, 'cuota_mensual': 875000, 'saldo_capital': 1650000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-07', 'valor_cuota': 850000, 'interes_mes': 16500, 'cuota_mensual': 866500, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-07', 'valor_cuota': 800000, 'interes_mes': 8000, 'cuota_mensual': 808000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        

        











        
    ]


    db_manager.add_multiple_historical_credits(credits_list) """

    # Create main window
    window = MainWindow()
    assistant_page = AssistantPage(db_manager)
    home_page = HomePage(db_manager, assistant_page, window)

    # Create and add new views to the main window
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
