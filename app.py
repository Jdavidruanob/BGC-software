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

    db_manager.populate_initial_members()
    

    # Datos de créditos históricos a agregar
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
            'socios_ids': [25],
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

        {
            'letra': 409,
            'capital': 8000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2024-11-30',
            'socios_ids': [7],  # WILLIAM DAVID JIMENEZ P.
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-12-30', 'valor_cuota': 340000, 'interes_mes': 80000, 'cuota_mensual': 420000, 'saldo_capital': 7660000, 'fecha_pago': '2024-12-29'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-01-30', 'valor_cuota': 340000, 'interes_mes': 76600, 'cuota_mensual': 416600, 'saldo_capital': 7320000, 'fecha_pago': '2025-02-01'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-02-28', 'valor_cuota': 340000, 'interes_mes': 73200, 'cuota_mensual': 413200, 'saldo_capital': 6980000, 'fecha_pago': '2025-03-10'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-03-30', 'valor_cuota': 340000, 'interes_mes': 69800, 'cuota_mensual': 409800, 'saldo_capital': 6640000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-04-30', 'valor_cuota': 340000, 'interes_mes': 66400, 'cuota_mensual': 406400, 'saldo_capital': 6300000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-05-30', 'valor_cuota': 340000, 'interes_mes': 63000, 'cuota_mensual': 403000, 'saldo_capital': 5960000, 'fecha_pago': '2025-06-18'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-06-30', 'valor_cuota': 340000, 'interes_mes': 59600, 'cuota_mensual': 399600, 'saldo_capital': 5620000, 'fecha_pago': '2025-07-27'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-07-30', 'valor_cuota': 340000, 'interes_mes': 56200, 'cuota_mensual': 396200, 'saldo_capital': 5280000, 'fecha_pago': '2025-08-18'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-08-30', 'valor_cuota': 340000, 'interes_mes': 52800, 'cuota_mensual': 392800, 'saldo_capital': 4940000, 'fecha_pago': '2025-09-22'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-09-30', 'valor_cuota': 340000, 'interes_mes': 49400, 'cuota_mensual': 389400, 'saldo_capital': 4600000, 'fecha_pago': '2025-10-13'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-10-30', 'valor_cuota': 340000, 'interes_mes': 46000, 'cuota_mensual': 386000, 'saldo_capital': 4260000, 'fecha_pago': '2025-11-21'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-11-30', 'valor_cuota': 340000, 'interes_mes': 42600, 'cuota_mensual': 382600, 'saldo_capital': 3920000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-12-30', 'valor_cuota': 340000, 'interes_mes': 39200, 'cuota_mensual': 379200, 'saldo_capital': 3580000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-01-30', 'valor_cuota': 340000, 'interes_mes': 35800, 'cuota_mensual': 375800, 'saldo_capital': 3240000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-02-28', 'valor_cuota': 340000, 'interes_mes': 32400, 'cuota_mensual': 372400, 'saldo_capital': 2900000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-03-30', 'valor_cuota': 340000, 'interes_mes': 29000, 'cuota_mensual': 369000, 'saldo_capital': 2560000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-04-30', 'valor_cuota': 340000, 'interes_mes': 25600, 'cuota_mensual': 365600, 'saldo_capital': 2220000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-05-30', 'valor_cuota': 340000, 'interes_mes': 22200, 'cuota_mensual': 362200, 'saldo_capital': 1880000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-06-30', 'valor_cuota': 340000, 'interes_mes': 18800, 'cuota_mensual': 358800, 'saldo_capital': 1540000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-07-30', 'valor_cuota': 340000, 'interes_mes': 15400, 'cuota_mensual': 355400, 'saldo_capital': 1200000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-08-30', 'valor_cuota': 340000, 'interes_mes': 12000, 'cuota_mensual': 352000, 'saldo_capital': 860000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-09-30', 'valor_cuota': 340000, 'interes_mes': 8600, 'cuota_mensual': 348600, 'saldo_capital': 520000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-10-30', 'valor_cuota': 340000, 'interes_mes': 5200, 'cuota_mensual': 345200, 'saldo_capital': 180000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-11-30', 'valor_cuota': 180000, 'interes_mes': 1800, 'cuota_mensual': 181800, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 422,
            'capital': 8000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-04-01',
            'socios_ids': [17],  # MAGALLY BURBANO GARCIA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-01', 'valor_cuota': 335000, 'interes_mes': 80000, 'cuota_mensual': 415000, 'saldo_capital': 7665000, 'fecha_pago': '2025-05-09'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-01', 'valor_cuota': 335000, 'interes_mes': 76650, 'cuota_mensual': 411650, 'saldo_capital': 7330000, 'fecha_pago': '2025-07-18'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-01', 'valor_cuota': 335000, 'interes_mes': 73300, 'cuota_mensual': 408300, 'saldo_capital': 6995000, 'fecha_pago': '2025-07-25'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-01', 'valor_cuota': 335000, 'interes_mes': 69950, 'cuota_mensual': 404950, 'saldo_capital': 6660000, 'fecha_pago': '2025-11-10'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-01', 'valor_cuota': 335000, 'interes_mes': 66600, 'cuota_mensual': 401600, 'saldo_capital': 6325000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-01', 'valor_cuota': 335000, 'interes_mes': 63250, 'cuota_mensual': 398250, 'saldo_capital': 5990000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-01', 'valor_cuota': 335000, 'interes_mes': 59900, 'cuota_mensual': 394900, 'saldo_capital': 5655000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-01', 'valor_cuota': 335000, 'interes_mes': 56550, 'cuota_mensual': 391550, 'saldo_capital': 5320000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-01', 'valor_cuota': 335000, 'interes_mes': 53200, 'cuota_mensual': 388200, 'saldo_capital': 4985000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-01', 'valor_cuota': 335000, 'interes_mes': 49850, 'cuota_mensual': 384850, 'saldo_capital': 4650000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-01', 'valor_cuota': 335000, 'interes_mes': 46500, 'cuota_mensual': 381500, 'saldo_capital': 4315000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-01', 'valor_cuota': 335000, 'interes_mes': 43150, 'cuota_mensual': 378150, 'saldo_capital': 3980000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-01', 'valor_cuota': 335000, 'interes_mes': 39800, 'cuota_mensual': 374800, 'saldo_capital': 3645000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-06-01', 'valor_cuota': 335000, 'interes_mes': 36450, 'cuota_mensual': 371450, 'saldo_capital': 3310000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-07-01', 'valor_cuota': 335000, 'interes_mes': 33100, 'cuota_mensual': 368100, 'saldo_capital': 2975000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-08-01', 'valor_cuota': 335000, 'interes_mes': 29750, 'cuota_mensual': 364750, 'saldo_capital': 2640000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-09-01', 'valor_cuota': 335000, 'interes_mes': 26400, 'cuota_mensual': 361400, 'saldo_capital': 2305000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-10-01', 'valor_cuota': 335000, 'interes_mes': 23050, 'cuota_mensual': 358050, 'saldo_capital': 1970000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-11-01', 'valor_cuota': 335000, 'interes_mes': 19700, 'cuota_mensual': 354700, 'saldo_capital': 1635000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-12-01', 'valor_cuota': 335000, 'interes_mes': 16350, 'cuota_mensual': 351350, 'saldo_capital': 1300000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-01-01', 'valor_cuota': 335000, 'interes_mes': 13000, 'cuota_mensual': 348000, 'saldo_capital': 965000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-02-01', 'valor_cuota': 335000, 'interes_mes': 9650, 'cuota_mensual': 344650, 'saldo_capital': 630000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-03-01', 'valor_cuota': 335000, 'interes_mes': 6300, 'cuota_mensual': 341300, 'saldo_capital': 295000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-04-01', 'valor_cuota': 295000, 'interes_mes': 2950, 'cuota_mensual': 297950, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 433,
            'capital': 5080000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 12,
            'fecha_inicio': '2025-07-02',
            'socios_ids': [17],  # MAGALLY BURBANO GARCIA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-08-02', 'valor_cuota': 425000, 'interes_mes': 50800, 'cuota_mensual': 475800, 'saldo_capital': 4655000, 'fecha_pago': '2025-08-06'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-09-02', 'valor_cuota': 425000, 'interes_mes': 46550, 'cuota_mensual': 471550, 'saldo_capital': 4230000, 'fecha_pago': '2025-09-07'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-10-02', 'valor_cuota': 425000, 'interes_mes': 42300, 'cuota_mensual': 467300, 'saldo_capital': 3805000, 'fecha_pago': '2025-11-06'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-11-02', 'valor_cuota': 425000, 'interes_mes': 38050, 'cuota_mensual': 463050, 'saldo_capital': 3380000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-12-02', 'valor_cuota': 425000, 'interes_mes': 33800, 'cuota_mensual': 458800, 'saldo_capital': 2955000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-01-02', 'valor_cuota': 425000, 'interes_mes': 29550, 'cuota_mensual': 454550, 'saldo_capital': 2530000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-02-02', 'valor_cuota': 425000, 'interes_mes': 25300, 'cuota_mensual': 450300, 'saldo_capital': 2105000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-03-02', 'valor_cuota': 425000, 'interes_mes': 21050, 'cuota_mensual': 446050, 'saldo_capital': 1680000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-04-02', 'valor_cuota': 425000, 'interes_mes': 16800, 'cuota_mensual': 441800, 'saldo_capital': 1255000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-05-02', 'valor_cuota': 425000, 'interes_mes': 12550, 'cuota_mensual': 437550, 'saldo_capital': 830000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-06-02', 'valor_cuota': 425000, 'interes_mes': 8300, 'cuota_mensual': 433300, 'saldo_capital': 405000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-07-02', 'valor_cuota': 405000, 'interes_mes': 4050, 'cuota_mensual': 409050, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 372,
            'capital': 4000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2024-01-23',
            'socios_ids': [50],  # AMPARO FLOREZ Y/O LUIS F. VALLEJO F.
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-02-23', 'valor_cuota': 167000, 'interes_mes': 40000, 'cuota_mensual': 207000, 'saldo_capital': 3833000, 'fecha_pago': '2024-02-24'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-03-23', 'valor_cuota': 167000, 'interes_mes': 38330, 'cuota_mensual': 205330, 'saldo_capital': 3666000, 'fecha_pago': '2024-03-27'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-04-23', 'valor_cuota': 167000, 'interes_mes': 36660, 'cuota_mensual': 203660, 'saldo_capital': 3499000, 'fecha_pago': '2024-04-22'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-05-23', 'valor_cuota': 167000, 'interes_mes': 34990, 'cuota_mensual': 201990, 'saldo_capital': 3332000, 'fecha_pago': '2024-05-28'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-06-23', 'valor_cuota': 167000, 'interes_mes': 33320, 'cuota_mensual': 200320, 'saldo_capital': 3165000, 'fecha_pago': '2024-06-25'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-07-23', 'valor_cuota': 167000, 'interes_mes': 31650, 'cuota_mensual': 198650, 'saldo_capital': 2998000, 'fecha_pago': '2024-07-29'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-08-23', 'valor_cuota': 167000, 'interes_mes': 29980, 'cuota_mensual': 196980, 'saldo_capital': 2831000, 'fecha_pago': '2024-08-26'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-09-23', 'valor_cuota': 167000, 'interes_mes': 28310, 'cuota_mensual': 195310, 'saldo_capital': 2664000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-10-23', 'valor_cuota': 167000, 'interes_mes': 26640, 'cuota_mensual': 193640, 'saldo_capital': 2497000, 'fecha_pago': '2024-10-29'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-11-23', 'valor_cuota': 167000, 'interes_mes': 24970, 'cuota_mensual': 191970, 'saldo_capital': 2330000, 'fecha_pago': '2024-11-24'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-12-23', 'valor_cuota': 167000, 'interes_mes': 23300, 'cuota_mensual': 190300, 'saldo_capital': 2163000, 'fecha_pago': '2024-12-27'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-01-23', 'valor_cuota': 167000, 'interes_mes': 21630, 'cuota_mensual': 188630, 'saldo_capital': 1996000, 'fecha_pago': '2025-01-24'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-02-23', 'valor_cuota': 167000, 'interes_mes': 19960, 'cuota_mensual': 186960, 'saldo_capital': 1829000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-03-23', 'valor_cuota': 167000, 'interes_mes': 18290, 'cuota_mensual': 185290, 'saldo_capital': 1662000, 'fecha_pago': '2025-03-31'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-04-23', 'valor_cuota': 167000, 'interes_mes': 16620, 'cuota_mensual': 183620, 'saldo_capital': 1495000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-05-23', 'valor_cuota': 167000, 'interes_mes': 14950, 'cuota_mensual': 181950, 'saldo_capital': 1328000, 'fecha_pago': '2025-06-02'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-06-23', 'valor_cuota': 167000, 'interes_mes': 13280, 'cuota_mensual': 180280, 'saldo_capital': 1161000, 'fecha_pago': '2025-06-27'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-07-23', 'valor_cuota': 167000, 'interes_mes': 11610, 'cuota_mensual': 178610, 'saldo_capital': 994000, 'fecha_pago': '2025-07-29'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-08-23', 'valor_cuota': 167000, 'interes_mes': 9940, 'cuota_mensual': 176940, 'saldo_capital': 827000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-09-23', 'valor_cuota': 167000, 'interes_mes': 8270, 'cuota_mensual': 175270, 'saldo_capital': 660000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-10-23', 'valor_cuota': 167000, 'interes_mes': 6600, 'cuota_mensual': 173600, 'saldo_capital': 493000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-11-23', 'valor_cuota': 167000, 'interes_mes': 4930, 'cuota_mensual': 171930, 'saldo_capital': 326000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-12-23', 'valor_cuota': 167000, 'interes_mes': 3260, 'cuota_mensual': 170260, 'saldo_capital': 159000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-01-23', 'valor_cuota': 159000, 'interes_mes': 1590, 'cuota_mensual': 160590, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 375,
            'capital': 15000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 40,
            'fecha_inicio': '2024-03-01',
            'socios_ids': [50],  # AMPARO FLOREZ Y/O LUIS VALLEJO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-04-01', 'valor_cuota': 375000, 'interes_mes': 150000, 'cuota_mensual': 525000, 'saldo_capital': 14625000, 'fecha_pago': '2024-04-22'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-05-01', 'valor_cuota': 375000, 'interes_mes': 146250, 'cuota_mensual': 521250, 'saldo_capital': 14250000, 'fecha_pago': '2024-05-28'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-06-01', 'valor_cuota': 375000, 'interes_mes': 142500, 'cuota_mensual': 517500, 'saldo_capital': 13875000, 'fecha_pago': '2024-06-25'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-07-11', 'valor_cuota': 375000, 'interes_mes': 138750, 'cuota_mensual': 513750, 'saldo_capital': 13500000, 'fecha_pago': '2024-07-29'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-08-01', 'valor_cuota': 375000, 'interes_mes': 135000, 'cuota_mensual': 510000, 'saldo_capital': 13125000, 'fecha_pago': '2024-08-26'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-09-01', 'valor_cuota': 375000, 'interes_mes': 131250, 'cuota_mensual': 506250, 'saldo_capital': 12750000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-10-01', 'valor_cuota': 375000, 'interes_mes': 127500, 'cuota_mensual': 502500, 'saldo_capital': 12375000, 'fecha_pago': '2024-10-29'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-11-01', 'valor_cuota': 375000, 'interes_mes': 123750, 'cuota_mensual': 498750, 'saldo_capital': 12000000, 'fecha_pago': '2024-11-29'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-12-01', 'valor_cuota': 375000, 'interes_mes': 120000, 'cuota_mensual': 495000, 'saldo_capital': 11625000, 'fecha_pago': '2024-12-27'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-01-01', 'valor_cuota': 375000, 'interes_mes': 116250, 'cuota_mensual': 491250, 'saldo_capital': 11250000, 'fecha_pago': '2025-01-24'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-02-01', 'valor_cuota': 375000, 'interes_mes': 112500, 'cuota_mensual': 487500, 'saldo_capital': 10875000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-03-01', 'valor_cuota': 375000, 'interes_mes': 108750, 'cuota_mensual': 483750, 'saldo_capital': 10500000, 'fecha_pago': '2025-03-31'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-04-01', 'valor_cuota': 375000, 'interes_mes': 105000, 'cuota_mensual': 480000, 'saldo_capital': 10125000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-05-01', 'valor_cuota': 375000, 'interes_mes': 101250, 'cuota_mensual': 476250, 'saldo_capital': 9750000, 'fecha_pago': '2025-06-02'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-06-01', 'valor_cuota': 375000, 'interes_mes': 97500, 'cuota_mensual': 472500, 'saldo_capital': 9375000, 'fecha_pago': '2025-06-27'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-07-11', 'valor_cuota': 375000, 'interes_mes': 93750, 'cuota_mensual': 468750, 'saldo_capital': 9000000, 'fecha_pago': '2025-07-29'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-08-01', 'valor_cuota': 375000, 'interes_mes': 90000, 'cuota_mensual': 465000, 'saldo_capital': 8625000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-09-01', 'valor_cuota': 375000, 'interes_mes': 86250, 'cuota_mensual': 461250, 'saldo_capital': 8250000, 'fecha_pago': '2025-09-29'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-10-01', 'valor_cuota': 375000, 'interes_mes': 82500, 'cuota_mensual': 457500, 'saldo_capital': 7875000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-11-01', 'valor_cuota': 375000, 'interes_mes': 78750, 'cuota_mensual': 453750, 'saldo_capital': 7500000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-12-01', 'valor_cuota': 375000, 'interes_mes': 75000, 'cuota_mensual': 450000, 'saldo_capital': 7125000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-01-01', 'valor_cuota': 375000, 'interes_mes': 71250, 'cuota_mensual': 446250, 'saldo_capital': 6750000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-02-01', 'valor_cuota': 375000, 'interes_mes': 67500, 'cuota_mensual': 442500, 'saldo_capital': 6375000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-03-01', 'valor_cuota': 375000, 'interes_mes': 63750, 'cuota_mensual': 438750, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2026-04-01', 'valor_cuota': 375000, 'interes_mes': 60000, 'cuota_mensual': 435000, 'saldo_capital': 5625000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-05-01', 'valor_cuota': 375000, 'interes_mes': 56250, 'cuota_mensual': 431250, 'saldo_capital': 5250000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-06-01', 'valor_cuota': 375000, 'interes_mes': 52500, 'cuota_mensual': 427500, 'saldo_capital': 4875000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-07-01', 'valor_cuota': 375000, 'interes_mes': 48750, 'cuota_mensual': 423750, 'saldo_capital': 4500000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2026-08-01', 'valor_cuota': 375000, 'interes_mes': 45000, 'cuota_mensual': 420000, 'saldo_capital': 4125000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-09-01', 'valor_cuota': 375000, 'interes_mes': 41250, 'cuota_mensual': 416250, 'saldo_capital': 3750000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-10-01', 'valor_cuota': 375000, 'interes_mes': 37500, 'cuota_mensual': 412500, 'saldo_capital': 3375000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-11-01', 'valor_cuota': 375000, 'interes_mes': 33750, 'cuota_mensual': 408750, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-12-01', 'valor_cuota': 375000, 'interes_mes': 30000, 'cuota_mensual': 405000, 'saldo_capital': 2625000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-01-01', 'valor_cuota': 375000, 'interes_mes': 26250, 'cuota_mensual': 401250, 'saldo_capital': 2250000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-02-01', 'valor_cuota': 375000, 'interes_mes': 22500, 'cuota_mensual': 397500, 'saldo_capital': 1875000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-03-01', 'valor_cuota': 375000, 'interes_mes': 18750, 'cuota_mensual': 393750, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 37, 'fecha_vencimiento': '2027-04-01', 'valor_cuota': 375000, 'interes_mes': 15000, 'cuota_mensual': 390000, 'saldo_capital': 1125000, 'fecha_pago': None},
                {'nro_cuota': 38, 'fecha_vencimiento': '2027-05-01', 'valor_cuota': 375000, 'interes_mes': 11250, 'cuota_mensual': 386250, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 39, 'fecha_vencimiento': '2027-06-01', 'valor_cuota': 375000, 'interes_mes': 7500, 'cuota_mensual': 382500, 'saldo_capital': 375000, 'fecha_pago': None},
                {'nro_cuota': 40, 'fecha_vencimiento': '2027-07-06', 'valor_cuota': 375000, 'interes_mes': 3750, 'cuota_mensual': 378750, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 415,
            'capital': 20000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-01-11',
            'socios_ids': [33],  # ANA MILENA GARCIA D. Y/O WILMER CERON MARTINEZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-02-11', 'valor_cuota': 560000, 'interes_mes': 200000, 'cuota_mensual': 760000, 'saldo_capital': 19440000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-03-11', 'valor_cuota': 560000, 'interes_mes': 194400, 'cuota_mensual': 754400, 'saldo_capital': 18880000, 'fecha_pago': '2025-03-23'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-04-11', 'valor_cuota': 560000, 'interes_mes': 188800, 'cuota_mensual': 748800, 'saldo_capital': 18320000, 'fecha_pago': '2025-04-26'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-05-11', 'valor_cuota': 560000, 'interes_mes': 183200, 'cuota_mensual': 743200, 'saldo_capital': 17760000, 'fecha_pago': '2025-06-01'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-06-11', 'valor_cuota': 560000, 'interes_mes': 177600, 'cuota_mensual': 737600, 'saldo_capital': 17200000, 'fecha_pago': '2025-06-22'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-07-11', 'valor_cuota': 560000, 'interes_mes': 172000, 'cuota_mensual': 732000, 'saldo_capital': 16640000, 'fecha_pago': '2025-07-30'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-08-11', 'valor_cuota': 560000, 'interes_mes': 166400, 'cuota_mensual': 726400, 'saldo_capital': 16080000, 'fecha_pago': '2025-08-26'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-09-11', 'valor_cuota': 560000, 'interes_mes': 160800, 'cuota_mensual': 720800, 'saldo_capital': 15520000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-10-11', 'valor_cuota': 560000, 'interes_mes': 155200, 'cuota_mensual': 715200, 'saldo_capital': 14960000, 'fecha_pago': '2025-10-19'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-11-11', 'valor_cuota': 560000, 'interes_mes': 149600, 'cuota_mensual': 709600, 'saldo_capital': 14400000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-12-11', 'valor_cuota': 560000, 'interes_mes': 144000, 'cuota_mensual': 704000, 'saldo_capital': 13840000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-01-11', 'valor_cuota': 560000, 'interes_mes': 138400, 'cuota_mensual': 698400, 'saldo_capital': 13280000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-02-11', 'valor_cuota': 560000, 'interes_mes': 132800, 'cuota_mensual': 692800, 'saldo_capital': 12720000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-03-11', 'valor_cuota': 560000, 'interes_mes': 127200, 'cuota_mensual': 687200, 'saldo_capital': 12160000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-04-11', 'valor_cuota': 560000, 'interes_mes': 121600, 'cuota_mensual': 681600, 'saldo_capital': 11600000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-05-11', 'valor_cuota': 560000, 'interes_mes': 116000, 'cuota_mensual': 676000, 'saldo_capital': 11040000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-06-11', 'valor_cuota': 560000, 'interes_mes': 110400, 'cuota_mensual': 670400, 'saldo_capital': 10480000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-07-11', 'valor_cuota': 560000, 'interes_mes': 104800, 'cuota_mensual': 664800, 'saldo_capital': 9920000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-08-11', 'valor_cuota': 560000, 'interes_mes': 99200, 'cuota_mensual': 659200, 'saldo_capital': 9360000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-09-11', 'valor_cuota': 560000, 'interes_mes': 93600, 'cuota_mensual': 653600, 'saldo_capital': 8800000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-10-11', 'valor_cuota': 560000, 'interes_mes': 88000, 'cuota_mensual': 648000, 'saldo_capital': 8240000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-11-11', 'valor_cuota': 560000, 'interes_mes': 82400, 'cuota_mensual': 642400, 'saldo_capital': 7680000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-12-11', 'valor_cuota': 560000, 'interes_mes': 76800, 'cuota_mensual': 636800, 'saldo_capital': 7120000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-01-11', 'valor_cuota': 560000, 'interes_mes': 71200, 'cuota_mensual': 631200, 'saldo_capital': 6560000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-02-11', 'valor_cuota': 560000, 'interes_mes': 65600, 'cuota_mensual': 625600, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-03-11', 'valor_cuota': 560000, 'interes_mes': 60000, 'cuota_mensual': 620000, 'saldo_capital': 5440000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-04-11', 'valor_cuota': 560000, 'interes_mes': 54400, 'cuota_mensual': 614400, 'saldo_capital': 4880000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-05-11', 'valor_cuota': 560000, 'interes_mes': 48800, 'cuota_mensual': 608800, 'saldo_capital': 4320000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-06-11', 'valor_cuota': 560000, 'interes_mes': 43200, 'cuota_mensual': 603200, 'saldo_capital': 3760000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-07-11', 'valor_cuota': 560000, 'interes_mes': 37600, 'cuota_mensual': 597600, 'saldo_capital': 3200000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-08-11', 'valor_cuota': 560000, 'interes_mes': 32000, 'cuota_mensual': 592000, 'saldo_capital': 2640000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-09-11', 'valor_cuota': 560000, 'interes_mes': 26400, 'cuota_mensual': 586400, 'saldo_capital': 2080000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-10-11', 'valor_cuota': 560000, 'interes_mes': 20800, 'cuota_mensual': 580800, 'saldo_capital': 1520000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-11-11', 'valor_cuota': 560000, 'interes_mes': 15200, 'cuota_mensual': 575200, 'saldo_capital': 960000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-12-11', 'valor_cuota': 560000, 'interes_mes': 9600, 'cuota_mensual': 569600, 'saldo_capital': 400000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-01-11', 'valor_cuota': 400000, 'interes_mes': 4000, 'cuota_mensual': 404000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 437,
            'capital': 40000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-07-04',
            'socios_ids': [33],  # ANA MILENA GARCIA D. Y/O WILMER CERON MARTINEZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-08-04', 'valor_cuota': 1115000, 'interes_mes': 400000, 'cuota_mensual': 1515000, 'saldo_capital': 38885000, 'fecha_pago': '2025-08-26'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-09-04', 'valor_cuota': 1115000, 'interes_mes': 388850, 'cuota_mensual': 1503850, 'saldo_capital': 37770000, 'fecha_pago': '2025-09-27'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-10-04', 'valor_cuota': 1115000, 'interes_mes': 377700, 'cuota_mensual': 1492700, 'saldo_capital': 36655000, 'fecha_pago': '2025-10-19'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-11-04', 'valor_cuota': 1115000, 'interes_mes': 366550, 'cuota_mensual': 1481550, 'saldo_capital': 35540000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-12-04', 'valor_cuota': 1115000, 'interes_mes': 355400, 'cuota_mensual': 1470400, 'saldo_capital': 34425000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-01-04', 'valor_cuota': 1115000, 'interes_mes': 344250, 'cuota_mensual': 1459250, 'saldo_capital': 33310000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-02-04', 'valor_cuota': 1115000, 'interes_mes': 333100, 'cuota_mensual': 1448100, 'saldo_capital': 32195000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-03-04', 'valor_cuota': 1115000, 'interes_mes': 321950, 'cuota_mensual': 1436950, 'saldo_capital': 31080000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-04-04', 'valor_cuota': 1115000, 'interes_mes': 310800, 'cuota_mensual': 1425800, 'saldo_capital': 29965000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-05-04', 'valor_cuota': 1115000, 'interes_mes': 299650, 'cuota_mensual': 1414650, 'saldo_capital': 28850000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-06-04', 'valor_cuota': 1115000, 'interes_mes': 288500, 'cuota_mensual': 1403500, 'saldo_capital': 27735000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-07-04', 'valor_cuota': 1115000, 'interes_mes': 277350, 'cuota_mensual': 1392350, 'saldo_capital': 26620000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-08-04', 'valor_cuota': 1115000, 'interes_mes': 266200, 'cuota_mensual': 1381200, 'saldo_capital': 25505000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-09-04', 'valor_cuota': 1115000, 'interes_mes': 255050, 'cuota_mensual': 1370050, 'saldo_capital': 24390000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-10-04', 'valor_cuota': 1115000, 'interes_mes': 243900, 'cuota_mensual': 1358900, 'saldo_capital': 23275000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-11-04', 'valor_cuota': 1115000, 'interes_mes': 232750, 'cuota_mensual': 1347750, 'saldo_capital': 22160000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-12-04', 'valor_cuota': 1115000, 'interes_mes': 221600, 'cuota_mensual': 1336600, 'saldo_capital': 21045000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-01-04', 'valor_cuota': 1115000, 'interes_mes': 210450, 'cuota_mensual': 1325450, 'saldo_capital': 19930000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-02-04', 'valor_cuota': 1115000, 'interes_mes': 199300, 'cuota_mensual': 1314300, 'saldo_capital': 18815000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-03-04', 'valor_cuota': 1115000, 'interes_mes': 188150, 'cuota_mensual': 1303150, 'saldo_capital': 17700000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-04-04', 'valor_cuota': 1115000, 'interes_mes': 177000, 'cuota_mensual': 1292000, 'saldo_capital': 16585000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-05-04', 'valor_cuota': 1115000, 'interes_mes': 165850, 'cuota_mensual': 1280850, 'saldo_capital': 15470000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-06-04', 'valor_cuota': 1115000, 'interes_mes': 154700, 'cuota_mensual': 1269700, 'saldo_capital': 14355000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-07-04', 'valor_cuota': 1115000, 'interes_mes': 143550, 'cuota_mensual': 1258550, 'saldo_capital': 13240000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-08-04', 'valor_cuota': 1115000, 'interes_mes': 132400, 'cuota_mensual': 1247400, 'saldo_capital': 12125000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-09-04', 'valor_cuota': 1115000, 'interes_mes': 121250, 'cuota_mensual': 1236250, 'saldo_capital': 11010000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-10-04', 'valor_cuota': 1115000, 'interes_mes': 110100, 'cuota_mensual': 1225100, 'saldo_capital': 9895000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-11-04', 'valor_cuota': 1115000, 'interes_mes': 98950, 'cuota_mensual': 1213950, 'saldo_capital': 8780000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-12-04', 'valor_cuota': 1115000, 'interes_mes': 87800, 'cuota_mensual': 1202800, 'saldo_capital': 7665000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2028-01-04', 'valor_cuota': 1115000, 'interes_mes': 76650, 'cuota_mensual': 1191650, 'saldo_capital': 6550000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2028-02-04', 'valor_cuota': 1115000, 'interes_mes': 65500, 'cuota_mensual': 1180500, 'saldo_capital': 5435000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2028-03-04', 'valor_cuota': 1115000, 'interes_mes': 54350, 'cuota_mensual': 1169350, 'saldo_capital': 4320000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-04-04', 'valor_cuota': 1115000, 'interes_mes': 43200, 'cuota_mensual': 1158200, 'saldo_capital': 3205000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-05-04', 'valor_cuota': 1115000, 'interes_mes': 32050, 'cuota_mensual': 1147050, 'saldo_capital': 2090000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-06-04', 'valor_cuota': 1115000, 'interes_mes': 20900, 'cuota_mensual': 1135900, 'saldo_capital': 975000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-07-04', 'valor_cuota': 975000, 'interes_mes': 9750, 'cuota_mensual': 984750, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 403,
            'capital': 15000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2024-08-28',
            'socios_ids': [32,31],  # JESUS R. GARCIA D. Y/O RODRIGO GARCIA CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-09-28', 'valor_cuota': 420000, 'interes_mes': 150000, 'cuota_mensual': 570000, 'saldo_capital': 14580000, 'fecha_pago': '2024-10-08'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-10-28', 'valor_cuota': 420000, 'interes_mes': 145800, 'cuota_mensual': 565800, 'saldo_capital': 14160000, 'fecha_pago': '2024-10-27'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-11-28', 'valor_cuota': 420000, 'interes_mes': 141600, 'cuota_mensual': 561600, 'saldo_capital': 13740000, 'fecha_pago': '2024-11-18'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-12-28', 'valor_cuota': 420000, 'interes_mes': 137400, 'cuota_mensual': 557400, 'saldo_capital': 13320000, 'fecha_pago': '2024-12-23'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-01-28', 'valor_cuota': 420000, 'interes_mes': 133200, 'cuota_mensual': 553200, 'saldo_capital': 12900000, 'fecha_pago': '2025-02-08'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-02-28', 'valor_cuota': 420000, 'interes_mes': 129000, 'cuota_mensual': 549000, 'saldo_capital': 12480000, 'fecha_pago': '2025-03-09'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-03-28', 'valor_cuota': 420000, 'interes_mes': 124800, 'cuota_mensual': 544800, 'saldo_capital': 12060000, 'fecha_pago': '2025-03-26'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-04-28', 'valor_cuota': 420000, 'interes_mes': 120600, 'cuota_mensual': 540600, 'saldo_capital': 11640000, 'fecha_pago': '2025-04-17'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-05-28', 'valor_cuota': 420000, 'interes_mes': 116400, 'cuota_mensual': 536400, 'saldo_capital': 11220000, 'fecha_pago': '2025-05-19'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-06-28', 'valor_cuota': 420000, 'interes_mes': 112200, 'cuota_mensual': 532200, 'saldo_capital': 10800000, 'fecha_pago': '2025-06-19'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-07-28', 'valor_cuota': 420000, 'interes_mes': 108000, 'cuota_mensual': 528000, 'saldo_capital': 10380000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-08-28', 'valor_cuota': 420000, 'interes_mes': 103800, 'cuota_mensual': 523800, 'saldo_capital': 9960000, 'fecha_pago': '2025-08-21'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-09-28', 'valor_cuota': 420000, 'interes_mes': 99600, 'cuota_mensual': 519600, 'saldo_capital': 9540000, 'fecha_pago': '2025-09-24'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-10-28', 'valor_cuota': 420000, 'interes_mes': 95400, 'cuota_mensual': 515400, 'saldo_capital': 9120000, 'fecha_pago': '2025-10-16'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-11-28', 'valor_cuota': 420000, 'interes_mes': 91200, 'cuota_mensual': 511200, 'saldo_capital': 8700000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-12-28', 'valor_cuota': 420000, 'interes_mes': 87000, 'cuota_mensual': 507000, 'saldo_capital': 8280000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-01-28', 'valor_cuota': 420000, 'interes_mes': 82800, 'cuota_mensual': 502800, 'saldo_capital': 7860000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-02-28', 'valor_cuota': 420000, 'interes_mes': 78600, 'cuota_mensual': 498600, 'saldo_capital': 7440000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-03-28', 'valor_cuota': 420000, 'interes_mes': 74400, 'cuota_mensual': 494400, 'saldo_capital': 7020000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-04-28', 'valor_cuota': 420000, 'interes_mes': 70200, 'cuota_mensual': 490200, 'saldo_capital': 6600000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-05-28', 'valor_cuota': 420000, 'interes_mes': 66000, 'cuota_mensual': 486000, 'saldo_capital': 6180000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-06-28', 'valor_cuota': 420000, 'interes_mes': 61800, 'cuota_mensual': 481800, 'saldo_capital': 5760000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-07-28', 'valor_cuota': 420000, 'interes_mes': 57600, 'cuota_mensual': 477600, 'saldo_capital': 5340000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-08-28', 'valor_cuota': 420000, 'interes_mes': 53400, 'cuota_mensual': 473400, 'saldo_capital': 4920000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2026-09-28', 'valor_cuota': 420000, 'interes_mes': 49200, 'cuota_mensual': 469200, 'saldo_capital': 4500000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-10-28', 'valor_cuota': 420000, 'interes_mes': 45000, 'cuota_mensual': 465000, 'saldo_capital': 4080000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-11-28', 'valor_cuota': 420000, 'interes_mes': 40800, 'cuota_mensual': 460800, 'saldo_capital': 3660000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-12-28', 'valor_cuota': 420000, 'interes_mes': 36600, 'cuota_mensual': 456600, 'saldo_capital': 3240000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-01-28', 'valor_cuota': 420000, 'interes_mes': 32400, 'cuota_mensual': 452400, 'saldo_capital': 2820000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-02-28', 'valor_cuota': 420000, 'interes_mes': 28200, 'cuota_mensual': 448200, 'saldo_capital': 2400000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-03-28', 'valor_cuota': 420000, 'interes_mes': 24000, 'cuota_mensual': 444000, 'saldo_capital': 1980000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-04-28', 'valor_cuota': 420000, 'interes_mes': 19800, 'cuota_mensual': 439800, 'saldo_capital': 1560000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-05-28', 'valor_cuota': 420000, 'interes_mes': 15600, 'cuota_mensual': 435600, 'saldo_capital': 1140000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-06-28', 'valor_cuota': 420000, 'interes_mes': 11400, 'cuota_mensual': 431400, 'saldo_capital': 720000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-07-28', 'valor_cuota': 420000, 'interes_mes': 7200, 'cuota_mensual': 427200, 'saldo_capital': 300000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-08-28', 'valor_cuota': 300000, 'interes_mes': 3000, 'cuota_mensual': 303000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 412,
            'capital': 15000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2024-12-27',
            'socios_ids': [32,31],  # JESUS RODRIGO GARCIA DELGADO / RODRIGO GARCIA CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-01-27', 'valor_cuota': 417000, 'interes_mes': 150000, 'cuota_mensual': 567000, 'saldo_capital': 14583000, 'fecha_pago': '2025-02-08'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-02-27', 'valor_cuota': 417000, 'interes_mes': 145830, 'cuota_mensual': 562830, 'saldo_capital': 14166000, 'fecha_pago': '2025-03-09'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-03-27', 'valor_cuota': 417000, 'interes_mes': 141660, 'cuota_mensual': 558660, 'saldo_capital': 13749000, 'fecha_pago': '2025-03-26'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-04-27', 'valor_cuota': 417000, 'interes_mes': 137490, 'cuota_mensual': 554490, 'saldo_capital': 13332000, 'fecha_pago': '2025-04-17'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-05-27', 'valor_cuota': 417000, 'interes_mes': 133320, 'cuota_mensual': 550320, 'saldo_capital': 12915000, 'fecha_pago': '2025-05-19'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-06-27', 'valor_cuota': 417000, 'interes_mes': 129150, 'cuota_mensual': 546150, 'saldo_capital': 12498000, 'fecha_pago': '2025-06-19'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-07-27', 'valor_cuota': 417000, 'interes_mes': 124980, 'cuota_mensual': 541980, 'saldo_capital': 12081000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-08-27', 'valor_cuota': 417000, 'interes_mes': 120810, 'cuota_mensual': 537810, 'saldo_capital': 11664000, 'fecha_pago': '2025-08-21'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-09-27', 'valor_cuota': 417000, 'interes_mes': 116640, 'cuota_mensual': 533640, 'saldo_capital': 11247000, 'fecha_pago': '2025-09-24'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-10-27', 'valor_cuota': 417000, 'interes_mes': 112470, 'cuota_mensual': 529470, 'saldo_capital': 10830000, 'fecha_pago': '2025-10-16'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-11-27', 'valor_cuota': 417000, 'interes_mes': 108300, 'cuota_mensual': 525300, 'saldo_capital': 10413000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-12-27', 'valor_cuota': 417000, 'interes_mes': 104130, 'cuota_mensual': 521130, 'saldo_capital': 9996000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-01-27', 'valor_cuota': 417000, 'interes_mes': 99960, 'cuota_mensual': 516960, 'saldo_capital': 9579000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-02-27', 'valor_cuota': 417000, 'interes_mes': 95790, 'cuota_mensual': 512790, 'saldo_capital': 9162000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-03-27', 'valor_cuota': 417000, 'interes_mes': 91620, 'cuota_mensual': 508620, 'saldo_capital': 8745000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-04-27', 'valor_cuota': 417000, 'interes_mes': 87450, 'cuota_mensual': 504450, 'saldo_capital': 8328000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-05-27', 'valor_cuota': 417000, 'interes_mes': 83280, 'cuota_mensual': 500280, 'saldo_capital': 7911000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-06-27', 'valor_cuota': 417000, 'interes_mes': 79110, 'cuota_mensual': 496110, 'saldo_capital': 7494000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-07-27', 'valor_cuota': 417000, 'interes_mes': 74940, 'cuota_mensual': 491940, 'saldo_capital': 7077000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-08-27', 'valor_cuota': 417000, 'interes_mes': 70770, 'cuota_mensual': 487770, 'saldo_capital': 6660000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-09-27', 'valor_cuota': 417000, 'interes_mes': 66600, 'cuota_mensual': 483600, 'saldo_capital': 6243000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-10-27', 'valor_cuota': 417000, 'interes_mes': 62430, 'cuota_mensual': 479430, 'saldo_capital': 5826000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-11-27', 'valor_cuota': 417000, 'interes_mes': 58260, 'cuota_mensual': 475260, 'saldo_capital': 5409000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-12-27', 'valor_cuota': 417000, 'interes_mes': 54090, 'cuota_mensual': 471090, 'saldo_capital': 4992000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-01-27', 'valor_cuota': 417000, 'interes_mes': 49920, 'cuota_mensual': 466920, 'saldo_capital': 4575000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-02-27', 'valor_cuota': 417000, 'interes_mes': 45750, 'cuota_mensual': 462750, 'saldo_capital': 4158000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-03-27', 'valor_cuota': 417000, 'interes_mes': 41580, 'cuota_mensual': 458580, 'saldo_capital': 3741000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-04-27', 'valor_cuota': 417000, 'interes_mes': 37410, 'cuota_mensual': 454410, 'saldo_capital': 3324000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-05-27', 'valor_cuota': 417000, 'interes_mes': 33240, 'cuota_mensual': 450240, 'saldo_capital': 2907000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-06-27', 'valor_cuota': 417000, 'interes_mes': 29070, 'cuota_mensual': 446070, 'saldo_capital': 2490000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-07-27', 'valor_cuota': 417000, 'interes_mes': 24900, 'cuota_mensual': 441900, 'saldo_capital': 2073000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-08-27', 'valor_cuota': 417000, 'interes_mes': 20730, 'cuota_mensual': 437730, 'saldo_capital': 1656000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-09-27', 'valor_cuota': 417000, 'interes_mes': 16560, 'cuota_mensual': 433560, 'saldo_capital': 1239000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-10-27', 'valor_cuota': 417000, 'interes_mes': 12390, 'cuota_mensual': 429390, 'saldo_capital': 822000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-11-27', 'valor_cuota': 417000, 'interes_mes': 8220, 'cuota_mensual': 425220, 'saldo_capital': 405000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-12-27', 'valor_cuota': 405000, 'interes_mes': 4050, 'cuota_mensual': 409050, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 408,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 15,
            'fecha_inicio': '2024-10-28',
            'socios_ids': [32,31],  # RODRIGO GARCIA CASTRO / JESUS R. GARCIA D.
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-11-28', 'valor_cuota': 670000, 'interes_mes': 100000, 'cuota_mensual': 770000, 'saldo_capital': 9330000, 'fecha_pago': '2024-12-23'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-12-28', 'valor_cuota': 670000, 'interes_mes': 93300, 'cuota_mensual': 763300, 'saldo_capital': 8660000, 'fecha_pago': '2025-01-24'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-01-28', 'valor_cuota': 670000, 'interes_mes': 86600, 'cuota_mensual': 756600, 'saldo_capital': 7990000, 'fecha_pago': '2025-01-24'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-02-28', 'valor_cuota': 670000, 'interes_mes': 79900, 'cuota_mensual': 749900, 'saldo_capital': 7320000, 'fecha_pago': '2025-02-19'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-03-28', 'valor_cuota': 670000, 'interes_mes': 73200, 'cuota_mensual': 743200, 'saldo_capital': 6650000, 'fecha_pago': '2025-04-17'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-04-28', 'valor_cuota': 670000, 'interes_mes': 66500, 'cuota_mensual': 736500, 'saldo_capital': 5980000, 'fecha_pago': '2025-05-18'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-05-28', 'valor_cuota': 670000, 'interes_mes': 59800, 'cuota_mensual': 729800, 'saldo_capital': 5310000, 'fecha_pago': '2025-06-19'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-06-28', 'valor_cuota': 670000, 'interes_mes': 53100, 'cuota_mensual': 723100, 'saldo_capital': 4640000, 'fecha_pago': '2025-07-13'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-07-28', 'valor_cuota': 670000, 'interes_mes': 46400, 'cuota_mensual': 716400, 'saldo_capital': 3970000, 'fecha_pago': '2025-08-09'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-08-28', 'valor_cuota': 670000, 'interes_mes': 39700, 'cuota_mensual': 709700, 'saldo_capital': 3300000, 'fecha_pago': '2025-09-13'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-09-28', 'valor_cuota': 670000, 'interes_mes': 33000, 'cuota_mensual': 703000, 'saldo_capital': 2630000, 'fecha_pago': '2025-10-16'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-10-28', 'valor_cuota': 670000, 'interes_mes': 26300, 'cuota_mensual': 696300, 'saldo_capital': 1960000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-11-28', 'valor_cuota': 670000, 'interes_mes': 19600, 'cuota_mensual': 689600, 'saldo_capital': 1290000, 'fecha_pago': '2025-11-28'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-12-28', 'valor_cuota': 670000, 'interes_mes': 12900, 'cuota_mensual': 682900, 'saldo_capital': 620000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-01-28', 'valor_cuota': 620000, 'interes_mes': 6200, 'cuota_mensual': 626200, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 441,
            'capital': 5000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 12,
            'fecha_inicio': '2025-10-01',
            'socios_ids': [31],  # RODRIGO GARCIA CASTRO / ANGELA MARIA GARCIA DELGADO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-11-01', 'valor_cuota': 420000, 'interes_mes': 50000, 'cuota_mensual': 470000, 'saldo_capital': 4580000, 'fecha_pago': '2025-11-02'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-12-01', 'valor_cuota': 420000, 'interes_mes': 45800, 'cuota_mensual': 465800, 'saldo_capital': 4160000, 'fecha_pago': None},
                {'nro_cuota': 3, 'fecha_vencimiento': '2026-01-01', 'valor_cuota': 420000, 'interes_mes': 41600, 'cuota_mensual': 461600, 'saldo_capital': 3740000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2026-02-01', 'valor_cuota': 420000, 'interes_mes': 37400, 'cuota_mensual': 457400, 'saldo_capital': 3320000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2026-03-01', 'valor_cuota': 420000, 'interes_mes': 33200, 'cuota_mensual': 453200, 'saldo_capital': 2900000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-04-01', 'valor_cuota': 420000, 'interes_mes': 29000, 'cuota_mensual': 449000, 'saldo_capital': 2480000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-05-01', 'valor_cuota': 420000, 'interes_mes': 24800, 'cuota_mensual': 444800, 'saldo_capital': 2060000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-06-01', 'valor_cuota': 420000, 'interes_mes': 20600, 'cuota_mensual': 440600, 'saldo_capital': 1640000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-07-01', 'valor_cuota': 420000, 'interes_mes': 16400, 'cuota_mensual': 436400, 'saldo_capital': 1220000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-08-01', 'valor_cuota': 420000, 'interes_mes': 12200, 'cuota_mensual': 432200, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-09-01', 'valor_cuota': 420000, 'interes_mes': 8000, 'cuota_mensual': 428000, 'saldo_capital': 380000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-10-01', 'valor_cuota': 380000, 'interes_mes': 3800, 'cuota_mensual': 383800, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 413,
            'capital': 40843000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 12,  # Ajustado a la tabla real (el encabezado decía 15 por error)
            'fecha_inicio': '2025-01-09',
            'socios_ids': [35,36],  # HARVEY GARCIA LUNA Y/O MARCELA SALAZAR FLOREZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-02-09', 'valor_cuota': 3404000, 'interes_mes': 408430, 'cuota_mensual': 3812430, 'saldo_capital': 37439000, 'fecha_pago': '2025-02-10'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-03-09', 'valor_cuota': 3404000, 'interes_mes': 374390, 'cuota_mensual': 3778390, 'saldo_capital': 34035000, 'fecha_pago': '2025-03-05'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-04-09', 'valor_cuota': 3404000, 'interes_mes': 340350, 'cuota_mensual': 3744350, 'saldo_capital': 30631000, 'fecha_pago': '2025-04-03'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-05-09', 'valor_cuota': 3404000, 'interes_mes': 306310, 'cuota_mensual': 3710310, 'saldo_capital': 27227000, 'fecha_pago': '2025-04-26'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-06-09', 'valor_cuota': 3404000, 'interes_mes': 272270, 'cuota_mensual': 3676270, 'saldo_capital': 23823000, 'fecha_pago': '2025-05-23'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-07-09', 'valor_cuota': 3404000, 'interes_mes': 238230, 'cuota_mensual': 3642230, 'saldo_capital': 20419000, 'fecha_pago': '2025-07-08'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-08-09', 'valor_cuota': 3404000, 'interes_mes': 204190, 'cuota_mensual': 3608190, 'saldo_capital': 17015000, 'fecha_pago': '2025-07-28'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-09-09', 'valor_cuota': 3404000, 'interes_mes': 170150, 'cuota_mensual': 3574150, 'saldo_capital': 13611000, 'fecha_pago': '2025-08-22'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-10-09', 'valor_cuota': 3404000, 'interes_mes': 136110, 'cuota_mensual': 3540110, 'saldo_capital': 10207000, 'fecha_pago': '2025-09-15'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-11-09', 'valor_cuota': 3404000, 'interes_mes': 102070, 'cuota_mensual': 3506070, 'saldo_capital': 6803000, 'fecha_pago': '2025-10-16'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-12-09', 'valor_cuota': 3404000, 'interes_mes': 68030, 'cuota_mensual': 3472030, 'saldo_capital': 3399000, 'fecha_pago': '2025-11-07'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-01-09', 'valor_cuota': 3399000, 'interes_mes': 33990, 'cuota_mensual': 3432990, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 444,
            'capital': 20000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-11-06',
            'socios_ids': [35,36],  # HARVEY GARCIA LUNA Y/O MARCELA SALAZAR FLOREZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-12-06', 'valor_cuota': 835000, 'interes_mes': 200000, 'cuota_mensual': 1035000, 'saldo_capital': 19165000, 'fecha_pago': None},
                {'nro_cuota': 2, 'fecha_vencimiento': '2026-01-06', 'valor_cuota': 835000, 'interes_mes': 191650, 'cuota_mensual': 1026650, 'saldo_capital': 18330000, 'fecha_pago': None},
                {'nro_cuota': 3, 'fecha_vencimiento': '2026-02-06', 'valor_cuota': 835000, 'interes_mes': 183300, 'cuota_mensual': 1018300, 'saldo_capital': 17495000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2026-03-06', 'valor_cuota': 835000, 'interes_mes': 174950, 'cuota_mensual': 1009950, 'saldo_capital': 16660000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2026-04-06', 'valor_cuota': 835000, 'interes_mes': 166600, 'cuota_mensual': 1001600, 'saldo_capital': 15825000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-05-06', 'valor_cuota': 835000, 'interes_mes': 158250, 'cuota_mensual': 993250, 'saldo_capital': 14990000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-06-06', 'valor_cuota': 835000, 'interes_mes': 149900, 'cuota_mensual': 984900, 'saldo_capital': 14155000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-07-06', 'valor_cuota': 835000, 'interes_mes': 141550, 'cuota_mensual': 976550, 'saldo_capital': 13320000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-08-06', 'valor_cuota': 835000, 'interes_mes': 133200, 'cuota_mensual': 968200, 'saldo_capital': 12485000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-09-06', 'valor_cuota': 835000, 'interes_mes': 124850, 'cuota_mensual': 959850, 'saldo_capital': 11650000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-10-06', 'valor_cuota': 835000, 'interes_mes': 116500, 'cuota_mensual': 951500, 'saldo_capital': 10815000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-11-06', 'valor_cuota': 835000, 'interes_mes': 108150, 'cuota_mensual': 943150, 'saldo_capital': 9980000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-12-06', 'valor_cuota': 835000, 'interes_mes': 99800, 'cuota_mensual': 934800, 'saldo_capital': 9145000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2027-01-06', 'valor_cuota': 835000, 'interes_mes': 91450, 'cuota_mensual': 926450, 'saldo_capital': 8310000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2027-02-06', 'valor_cuota': 835000, 'interes_mes': 83100, 'cuota_mensual': 918100, 'saldo_capital': 7475000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2027-03-06', 'valor_cuota': 835000, 'interes_mes': 74750, 'cuota_mensual': 909750, 'saldo_capital': 6640000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2027-04-06', 'valor_cuota': 835000, 'interes_mes': 66400, 'cuota_mensual': 901400, 'saldo_capital': 5805000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-05-06', 'valor_cuota': 835000, 'interes_mes': 58050, 'cuota_mensual': 893050, 'saldo_capital': 4970000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-06-06', 'valor_cuota': 835000, 'interes_mes': 49700, 'cuota_mensual': 884700, 'saldo_capital': 4135000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-07-06', 'valor_cuota': 835000, 'interes_mes': 41350, 'cuota_mensual': 876350, 'saldo_capital': 3300000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-08-06', 'valor_cuota': 835000, 'interes_mes': 33000, 'cuota_mensual': 868000, 'saldo_capital': 2465000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-09-06', 'valor_cuota': 835000, 'interes_mes': 24650, 'cuota_mensual': 859650, 'saldo_capital': 1630000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-10-06', 'valor_cuota': 835000, 'interes_mes': 16300, 'cuota_mensual': 851300, 'saldo_capital': 795000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-11-06', 'valor_cuota': 795000, 'interes_mes': 7950, 'cuota_mensual': 802950, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 445,
            'capital': 12000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 6,
            'fecha_inicio': '2025-11-26',
            'socios_ids': [35,36],  # HARVEY GARCÍA LUNA / MARCELA SALAZAR FLOREZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-12-26', 'valor_cuota': 2000000, 'interes_mes': 120000, 'cuota_mensual': 2120000, 'saldo_capital': 10000000, 'fecha_pago': None},
                {'nro_cuota': 2, 'fecha_vencimiento': '2026-01-26', 'valor_cuota': 2000000, 'interes_mes': 100000, 'cuota_mensual': 2100000, 'saldo_capital': 8000000, 'fecha_pago': None},
                {'nro_cuota': 3, 'fecha_vencimiento': '2026-02-26', 'valor_cuota': 2000000, 'interes_mes': 80000, 'cuota_mensual': 2080000, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2026-03-26', 'valor_cuota': 2000000, 'interes_mes': 60000, 'cuota_mensual': 2060000, 'saldo_capital': 4000000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2026-04-26', 'valor_cuota': 2000000, 'interes_mes': 40000, 'cuota_mensual': 2040000, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-05-26', 'valor_cuota': 2000000, 'interes_mes': 20000, 'cuota_mensual': 2020000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 430,
            'capital': 6000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-04-30',
            'socios_ids': [40],  # SIOMARA ALEJANDRA GARCIA / JOHAN NARVAEZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-30', 'valor_cuota': 170000, 'interes_mes': 60000, 'cuota_mensual': 230000, 'saldo_capital': 5830000, 'fecha_pago': '2025-06-04'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-30', 'valor_cuota': 170000, 'interes_mes': 58300, 'cuota_mensual': 228300, 'saldo_capital': 5660000, 'fecha_pago': '2025-07-10'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-30', 'valor_cuota': 170000, 'interes_mes': 56600, 'cuota_mensual': 226600, 'saldo_capital': 5490000, 'fecha_pago': '2025-08-08'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-30', 'valor_cuota': 170000, 'interes_mes': 54900, 'cuota_mensual': 224900, 'saldo_capital': 5320000, 'fecha_pago': '2025-09-18'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-30', 'valor_cuota': 170000, 'interes_mes': 53200, 'cuota_mensual': 223200, 'saldo_capital': 5150000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-30', 'valor_cuota': 170000, 'interes_mes': 51500, 'cuota_mensual': 221500, 'saldo_capital': 4980000, 'fecha_pago': '2025-11-10'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-30', 'valor_cuota': 170000, 'interes_mes': 49800, 'cuota_mensual': 219800, 'saldo_capital': 4810000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-30', 'valor_cuota': 170000, 'interes_mes': 48100, 'cuota_mensual': 218100, 'saldo_capital': 4640000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-30', 'valor_cuota': 170000, 'interes_mes': 46400, 'cuota_mensual': 216400, 'saldo_capital': 4470000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-28', 'valor_cuota': 170000, 'interes_mes': 44700, 'cuota_mensual': 214700, 'saldo_capital': 4300000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-30', 'valor_cuota': 170000, 'interes_mes': 43000, 'cuota_mensual': 213000, 'saldo_capital': 4130000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-30', 'valor_cuota': 170000, 'interes_mes': 41300, 'cuota_mensual': 211300, 'saldo_capital': 3960000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-30', 'valor_cuota': 170000, 'interes_mes': 39600, 'cuota_mensual': 209600, 'saldo_capital': 3790000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-06-30', 'valor_cuota': 170000, 'interes_mes': 37900, 'cuota_mensual': 207900, 'saldo_capital': 3620000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-07-30', 'valor_cuota': 170000, 'interes_mes': 36200, 'cuota_mensual': 206200, 'saldo_capital': 3450000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-08-30', 'valor_cuota': 170000, 'interes_mes': 34500, 'cuota_mensual': 204500, 'saldo_capital': 3280000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-09-30', 'valor_cuota': 170000, 'interes_mes': 32800, 'cuota_mensual': 202800, 'saldo_capital': 3110000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-10-30', 'valor_cuota': 170000, 'interes_mes': 31100, 'cuota_mensual': 201100, 'saldo_capital': 2940000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-11-30', 'valor_cuota': 170000, 'interes_mes': 29400, 'cuota_mensual': 199400, 'saldo_capital': 2770000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-12-30', 'valor_cuota': 170000, 'interes_mes': 27700, 'cuota_mensual': 197700, 'saldo_capital': 2600000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-01-30', 'valor_cuota': 170000, 'interes_mes': 26000, 'cuota_mensual': 196000, 'saldo_capital': 2430000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-02-28', 'valor_cuota': 170000, 'interes_mes': 24300, 'cuota_mensual': 194300, 'saldo_capital': 2260000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-03-30', 'valor_cuota': 170000, 'interes_mes': 22600, 'cuota_mensual': 192600, 'saldo_capital': 2090000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-04-30', 'valor_cuota': 170000, 'interes_mes': 20900, 'cuota_mensual': 190900, 'saldo_capital': 1920000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-05-30', 'valor_cuota': 170000, 'interes_mes': 19200, 'cuota_mensual': 189200, 'saldo_capital': 1750000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-06-30', 'valor_cuota': 170000, 'interes_mes': 17500, 'cuota_mensual': 187500, 'saldo_capital': 1580000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-07-30', 'valor_cuota': 170000, 'interes_mes': 15800, 'cuota_mensual': 185800, 'saldo_capital': 1410000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-08-30', 'valor_cuota': 170000, 'interes_mes': 14100, 'cuota_mensual': 184100, 'saldo_capital': 1240000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-09-30', 'valor_cuota': 170000, 'interes_mes': 12400, 'cuota_mensual': 182400, 'saldo_capital': 1070000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-10-30', 'valor_cuota': 170000, 'interes_mes': 10700, 'cuota_mensual': 180700, 'saldo_capital': 900000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-11-30', 'valor_cuota': 170000, 'interes_mes': 9000, 'cuota_mensual': 179000, 'saldo_capital': 730000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-12-30', 'valor_cuota': 170000, 'interes_mes': 7300, 'cuota_mensual': 177300, 'saldo_capital': 560000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-01-30', 'valor_cuota': 170000, 'interes_mes': 5600, 'cuota_mensual': 175600, 'saldo_capital': 390000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-02-28', 'valor_cuota': 170000, 'interes_mes': 3900, 'cuota_mensual': 173900, 'saldo_capital': 220000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-03-30', 'valor_cuota': 170000, 'interes_mes': 2200, 'cuota_mensual': 172200, 'saldo_capital': 50000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-04-30', 'valor_cuota': 50000, 'interes_mes': 500, 'cuota_mensual': 50500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 358,
            'capital': 15000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2023-07-26',
            'socios_ids': [46,47],  # MAGCEIDER GARCIA LUNA Y/O PILAR HERRERA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-08-26', 'valor_cuota': 420000, 'interes_mes': 150000, 'cuota_mensual': 570000, 'saldo_capital': 14580000, 'fecha_pago': '2023-08-28'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2023-09-26', 'valor_cuota': 420000, 'interes_mes': 145800, 'cuota_mensual': 565800, 'saldo_capital': 14160000, 'fecha_pago': '2023-10-08'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2023-10-26', 'valor_cuota': 420000, 'interes_mes': 141600, 'cuota_mensual': 561600, 'saldo_capital': 13740000, 'fecha_pago': '2023-11-06'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2023-11-26', 'valor_cuota': 420000, 'interes_mes': 137400, 'cuota_mensual': 557400, 'saldo_capital': 13320000, 'fecha_pago': '2023-12-05'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2023-12-26', 'valor_cuota': 420000, 'interes_mes': 133200, 'cuota_mensual': 553200, 'saldo_capital': 12900000, 'fecha_pago': '2024-01-10'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-01-26', 'valor_cuota': 420000, 'interes_mes': 129000, 'cuota_mensual': 549000, 'saldo_capital': 12480000, 'fecha_pago': '2024-02-10'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-02-26', 'valor_cuota': 420000, 'interes_mes': 124800, 'cuota_mensual': 544800, 'saldo_capital': 12060000, 'fecha_pago': '2024-03-17'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-03-26', 'valor_cuota': 420000, 'interes_mes': 120600, 'cuota_mensual': 540600, 'saldo_capital': 11640000, 'fecha_pago': '2024-04-18'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-04-26', 'valor_cuota': 420000, 'interes_mes': 116400, 'cuota_mensual': 536400, 'saldo_capital': 11220000, 'fecha_pago': '2024-05-19'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-05-26', 'valor_cuota': 420000, 'interes_mes': 112200, 'cuota_mensual': 532200, 'saldo_capital': 10800000, 'fecha_pago': '2024-06-23'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-06-26', 'valor_cuota': 420000, 'interes_mes': 108000, 'cuota_mensual': 528000, 'saldo_capital': 10380000, 'fecha_pago': '2024-07-24'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-07-26', 'valor_cuota': 420000, 'interes_mes': 103800, 'cuota_mensual': 523800, 'saldo_capital': 9960000, 'fecha_pago': '2024-08-24'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-08-26', 'valor_cuota': 420000, 'interes_mes': 99600, 'cuota_mensual': 519600, 'saldo_capital': 9540000, 'fecha_pago': '2024-10-07'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2024-09-26', 'valor_cuota': 420000, 'interes_mes': 95400, 'cuota_mensual': 515400, 'saldo_capital': 9120000, 'fecha_pago': '2024-11-12'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2024-10-26', 'valor_cuota': 420000, 'interes_mes': 91200, 'cuota_mensual': 511200, 'saldo_capital': 8700000, 'fecha_pago': '2024-11-18'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2024-11-26', 'valor_cuota': 420000, 'interes_mes': 87000, 'cuota_mensual': 507000, 'saldo_capital': 8280000, 'fecha_pago': '2024-12-10'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2024-12-26', 'valor_cuota': 420000, 'interes_mes': 82800, 'cuota_mensual': 502800, 'saldo_capital': 7860000, 'fecha_pago': '2025-01-15'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-01-26', 'valor_cuota': 420000, 'interes_mes': 78600, 'cuota_mensual': 498600, 'saldo_capital': 7440000, 'fecha_pago': '2025-03-09'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-02-26', 'valor_cuota': 420000, 'interes_mes': 74400, 'cuota_mensual': 494400, 'saldo_capital': 7020000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-03-26', 'valor_cuota': 420000, 'interes_mes': 70200, 'cuota_mensual': 490200, 'saldo_capital': 6600000, 'fecha_pago': '2025-06-09'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-04-26', 'valor_cuota': 420000, 'interes_mes': 66000, 'cuota_mensual': 486000, 'saldo_capital': 6180000, 'fecha_pago': '2025-07-08'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-05-26', 'valor_cuota': 420000, 'interes_mes': 61800, 'cuota_mensual': 481800, 'saldo_capital': 5760000, 'fecha_pago': '2025-09-09'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-06-26', 'valor_cuota': 420000, 'interes_mes': 57600, 'cuota_mensual': 477600, 'saldo_capital': 5340000, 'fecha_pago': '2025-11-04'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-07-26', 'valor_cuota': 420000, 'interes_mes': 53400, 'cuota_mensual': 473400, 'saldo_capital': 4920000, 'fecha_pago': '2025-11-04'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-08-26', 'valor_cuota': 420000, 'interes_mes': 49200, 'cuota_mensual': 469200, 'saldo_capital': 4500000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2025-09-26', 'valor_cuota': 420000, 'interes_mes': 45000, 'cuota_mensual': 465000, 'saldo_capital': 4080000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2025-10-26', 'valor_cuota': 420000, 'interes_mes': 40800, 'cuota_mensual': 460800, 'saldo_capital': 3660000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2025-11-26', 'valor_cuota': 420000, 'interes_mes': 36600, 'cuota_mensual': 456600, 'saldo_capital': 3240000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2025-12-26', 'valor_cuota': 420000, 'interes_mes': 32400, 'cuota_mensual': 452400, 'saldo_capital': 2820000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-01-26', 'valor_cuota': 420000, 'interes_mes': 28200, 'cuota_mensual': 448200, 'saldo_capital': 2400000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-02-26', 'valor_cuota': 420000, 'interes_mes': 24000, 'cuota_mensual': 444000, 'saldo_capital': 1980000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-03-26', 'valor_cuota': 420000, 'interes_mes': 19800, 'cuota_mensual': 439800, 'saldo_capital': 1560000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-04-26', 'valor_cuota': 420000, 'interes_mes': 15600, 'cuota_mensual': 435600, 'saldo_capital': 1140000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2026-05-26', 'valor_cuota': 420000, 'interes_mes': 11400, 'cuota_mensual': 431400, 'saldo_capital': 720000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2026-06-26', 'valor_cuota': 420000, 'interes_mes': 7200, 'cuota_mensual': 427200, 'saldo_capital': 300000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-07-26', 'valor_cuota': 300000, 'interes_mes': 3000, 'cuota_mensual': 303000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },


        {
            'letra': 440,
            'capital': 1000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 4,
            'fecha_inicio': '2025-09-08',
            'socios_ids': [52,54],  # NOE ANGEL GUACHAVEZ / LUIS FERNANDO VALLEJOS FLOREZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-10-08', 'valor_cuota': 250000, 'interes_mes': 10000, 'cuota_mensual': 260000, 'saldo_capital': 750000, 'fecha_pago': '2025-09-26'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-11-08', 'valor_cuota': 250000, 'interes_mes': 7500, 'cuota_mensual': 257500, 'saldo_capital': 500000, 'fecha_pago': '2025-10-24'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-12-08', 'valor_cuota': 250000, 'interes_mes': 5000, 'cuota_mensual': 255000, 'saldo_capital': 250000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2026-01-08', 'valor_cuota': 250000, 'interes_mes': 2500, 'cuota_mensual': 252500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 410,
            'capital': 20000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2024-12-10',
            'socios_ids': [46,47],  # MAGCEIDER GARCIA L. Y/O PILAR HERRERA E.
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-01-10', 'valor_cuota': 560000, 'interes_mes': 200000, 'cuota_mensual': 760000, 'saldo_capital': 19440000, 'fecha_pago': '2025-01-15'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-02-10', 'valor_cuota': 560000, 'interes_mes': 194400, 'cuota_mensual': 754400, 'saldo_capital': 18880000, 'fecha_pago': '2025-03-09'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-03-10', 'valor_cuota': 560000, 'interes_mes': 188800, 'cuota_mensual': 748800, 'saldo_capital': 18320000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-04-10', 'valor_cuota': 560000, 'interes_mes': 183200, 'cuota_mensual': 743200, 'saldo_capital': 17760000, 'fecha_pago': '2025-06-09'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-05-10', 'valor_cuota': 560000, 'interes_mes': 177600, 'cuota_mensual': 737600, 'saldo_capital': 17200000, 'fecha_pago': '2025-07-08'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-06-10', 'valor_cuota': 560000, 'interes_mes': 172000, 'cuota_mensual': 732000, 'saldo_capital': 16640000, 'fecha_pago': '2025-09-09'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-07-10', 'valor_cuota': 560000, 'interes_mes': 166400, 'cuota_mensual': 726400, 'saldo_capital': 16080000, 'fecha_pago': '2025-11-04'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-08-10', 'valor_cuota': 560000, 'interes_mes': 160800, 'cuota_mensual': 720800, 'saldo_capital': 15520000, 'fecha_pago': '2025-11-04'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-09-10', 'valor_cuota': 560000, 'interes_mes': 155200, 'cuota_mensual': 715200, 'saldo_capital': 14960000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-10-10', 'valor_cuota': 560000, 'interes_mes': 149600, 'cuota_mensual': 709600, 'saldo_capital': 14400000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-11-10', 'valor_cuota': 560000, 'interes_mes': 144000, 'cuota_mensual': 704000, 'saldo_capital': 13840000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-12-10', 'valor_cuota': 560000, 'interes_mes': 138400, 'cuota_mensual': 698400, 'saldo_capital': 13280000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-01-10', 'valor_cuota': 560000, 'interes_mes': 132800, 'cuota_mensual': 692800, 'saldo_capital': 12720000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-02-10', 'valor_cuota': 560000, 'interes_mes': 127200, 'cuota_mensual': 687200, 'saldo_capital': 12160000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-03-10', 'valor_cuota': 560000, 'interes_mes': 121600, 'cuota_mensual': 681600, 'saldo_capital': 11600000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-04-10', 'valor_cuota': 560000, 'interes_mes': 116000, 'cuota_mensual': 676000, 'saldo_capital': 11040000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-05-10', 'valor_cuota': 560000, 'interes_mes': 110400, 'cuota_mensual': 670400, 'saldo_capital': 10480000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-06-10', 'valor_cuota': 560000, 'interes_mes': 104800, 'cuota_mensual': 664800, 'saldo_capital': 9920000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-07-10', 'valor_cuota': 560000, 'interes_mes': 99200, 'cuota_mensual': 659200, 'saldo_capital': 9360000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-08-10', 'valor_cuota': 560000, 'interes_mes': 93600, 'cuota_mensual': 653600, 'saldo_capital': 8800000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-09-10', 'valor_cuota': 560000, 'interes_mes': 88000, 'cuota_mensual': 648000, 'saldo_capital': 8240000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-10-10', 'valor_cuota': 560000, 'interes_mes': 82400, 'cuota_mensual': 642400, 'saldo_capital': 7680000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-11-10', 'valor_cuota': 560000, 'interes_mes': 76800, 'cuota_mensual': 636800, 'saldo_capital': 7120000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-12-10', 'valor_cuota': 560000, 'interes_mes': 71200, 'cuota_mensual': 631200, 'saldo_capital': 6560000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-01-10', 'valor_cuota': 560000, 'interes_mes': 65600, 'cuota_mensual': 625600, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-02-10', 'valor_cuota': 560000, 'interes_mes': 60000, 'cuota_mensual': 620000, 'saldo_capital': 5440000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-03-10', 'valor_cuota': 560000, 'interes_mes': 54400, 'cuota_mensual': 614400, 'saldo_capital': 4880000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-04-10', 'valor_cuota': 560000, 'interes_mes': 48800, 'cuota_mensual': 608800, 'saldo_capital': 4320000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-05-10', 'valor_cuota': 560000, 'interes_mes': 43200, 'cuota_mensual': 603200, 'saldo_capital': 3760000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-06-10', 'valor_cuota': 560000, 'interes_mes': 37600, 'cuota_mensual': 597600, 'saldo_capital': 3200000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-07-10', 'valor_cuota': 560000, 'interes_mes': 32000, 'cuota_mensual': 592000, 'saldo_capital': 2640000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-08-10', 'valor_cuota': 560000, 'interes_mes': 26400, 'cuota_mensual': 586400, 'saldo_capital': 2080000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-09-10', 'valor_cuota': 560000, 'interes_mes': 20800, 'cuota_mensual': 580800, 'saldo_capital': 1520000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-10-10', 'valor_cuota': 560000, 'interes_mes': 15200, 'cuota_mensual': 575200, 'saldo_capital': 960000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-11-10', 'valor_cuota': 560000, 'interes_mes': 9600, 'cuota_mensual': 569600, 'saldo_capital': 400000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-12-10', 'valor_cuota': 400000, 'interes_mes': 4000, 'cuota_mensual': 404000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 431,
            'capital': 30000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-05-04',
            'socios_ids': [42,43],  # OLGA PATRICIA TORO MELO / HEYMAN LUNA TORO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-06-04', 'valor_cuota': 834000, 'interes_mes': 300000, 'cuota_mensual': 1134000, 'saldo_capital': 29166000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-07-04', 'valor_cuota': 834000, 'interes_mes': 291660, 'cuota_mensual': 1125660, 'saldo_capital': 28332000, 'fecha_pago': '2025-07-14'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-08-04', 'valor_cuota': 834000, 'interes_mes': 283320, 'cuota_mensual': 1117320, 'saldo_capital': 27498000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-09-04', 'valor_cuota': 834000, 'interes_mes': 274980, 'cuota_mensual': 1108980, 'saldo_capital': 26664000, 'fecha_pago': '2025-09-05'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-10-04', 'valor_cuota': 834000, 'interes_mes': 266640, 'cuota_mensual': 1100640, 'saldo_capital': 25830000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-11-04', 'valor_cuota': 834000, 'interes_mes': 258300, 'cuota_mensual': 1092300, 'saldo_capital': 24996000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-12-04', 'valor_cuota': 834000, 'interes_mes': 249960, 'cuota_mensual': 1083960, 'saldo_capital': 24162000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-01-04', 'valor_cuota': 834000, 'interes_mes': 241620, 'cuota_mensual': 1075620, 'saldo_capital': 23328000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-02-04', 'valor_cuota': 834000, 'interes_mes': 233280, 'cuota_mensual': 1067280, 'saldo_capital': 22494000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-03-04', 'valor_cuota': 834000, 'interes_mes': 224940, 'cuota_mensual': 1058940, 'saldo_capital': 21660000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-04-04', 'valor_cuota': 834000, 'interes_mes': 216600, 'cuota_mensual': 1050600, 'saldo_capital': 20826000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-05-04', 'valor_cuota': 834000, 'interes_mes': 208260, 'cuota_mensual': 1042260, 'saldo_capital': 19992000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-06-04', 'valor_cuota': 834000, 'interes_mes': 199920, 'cuota_mensual': 1033920, 'saldo_capital': 19158000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-07-04', 'valor_cuota': 834000, 'interes_mes': 191580, 'cuota_mensual': 1025580, 'saldo_capital': 18324000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-08-04', 'valor_cuota': 834000, 'interes_mes': 183240, 'cuota_mensual': 1017240, 'saldo_capital': 17490000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-09-04', 'valor_cuota': 834000, 'interes_mes': 174900, 'cuota_mensual': 1008900, 'saldo_capital': 16656000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-10-04', 'valor_cuota': 834000, 'interes_mes': 166560, 'cuota_mensual': 1000560, 'saldo_capital': 15822000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-11-04', 'valor_cuota': 834000, 'interes_mes': 158220, 'cuota_mensual': 992220, 'saldo_capital': 14988000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-12-04', 'valor_cuota': 834000, 'interes_mes': 149880, 'cuota_mensual': 983880, 'saldo_capital': 14154000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-01-04', 'valor_cuota': 834000, 'interes_mes': 141540, 'cuota_mensual': 975540, 'saldo_capital': 13320000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-02-04', 'valor_cuota': 834000, 'interes_mes': 133200, 'cuota_mensual': 967200, 'saldo_capital': 12486000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-03-04', 'valor_cuota': 834000, 'interes_mes': 124860, 'cuota_mensual': 958860, 'saldo_capital': 11652000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-04-04', 'valor_cuota': 834000, 'interes_mes': 116520, 'cuota_mensual': 950520, 'saldo_capital': 10818000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-05-04', 'valor_cuota': 834000, 'interes_mes': 108180, 'cuota_mensual': 942180, 'saldo_capital': 9984000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-06-04', 'valor_cuota': 834000, 'interes_mes': 99840, 'cuota_mensual': 933840, 'saldo_capital': 9150000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-07-04', 'valor_cuota': 834000, 'interes_mes': 91500, 'cuota_mensual': 925500, 'saldo_capital': 8316000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-08-04', 'valor_cuota': 834000, 'interes_mes': 83160, 'cuota_mensual': 917160, 'saldo_capital': 7482000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-09-04', 'valor_cuota': 834000, 'interes_mes': 74820, 'cuota_mensual': 908820, 'saldo_capital': 6648000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-10-04', 'valor_cuota': 834000, 'interes_mes': 66480, 'cuota_mensual': 900480, 'saldo_capital': 5814000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-11-04', 'valor_cuota': 834000, 'interes_mes': 58140, 'cuota_mensual': 892140, 'saldo_capital': 4980000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-12-04', 'valor_cuota': 834000, 'interes_mes': 49800, 'cuota_mensual': 883800, 'saldo_capital': 4146000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2028-01-04', 'valor_cuota': 834000, 'interes_mes': 41460, 'cuota_mensual': 875460, 'saldo_capital': 3312000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-02-04', 'valor_cuota': 834000, 'interes_mes': 33120, 'cuota_mensual': 867120, 'saldo_capital': 2478000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-03-04', 'valor_cuota': 834000, 'interes_mes': 24780, 'cuota_mensual': 858780, 'saldo_capital': 1644000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-04-04', 'valor_cuota': 834000, 'interes_mes': 16440, 'cuota_mensual': 850440, 'saldo_capital': 810000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-05-04', 'valor_cuota': 810000, 'interes_mes': 8100, 'cuota_mensual': 818100, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 435,
            'capital': 5000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 18,
            'fecha_inicio': '2025-06-23',
            'socios_ids': [43,42],  # HEYMAN G. LUNA TORO Y/O OLGA PATRICIA TORO MELO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-07-23', 'valor_cuota': 280000, 'interes_mes': 50000, 'cuota_mensual': 330000, 'saldo_capital': 4720000, 'fecha_pago': '2025-09-05'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-08-23', 'valor_cuota': 280000, 'interes_mes': 47200, 'cuota_mensual': 327200, 'saldo_capital': 4440000, 'fecha_pago': '2025-09-05'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-09-23', 'valor_cuota': 280000, 'interes_mes': 44400, 'cuota_mensual': 324400, 'saldo_capital': 4160000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-10-23', 'valor_cuota': 280000, 'interes_mes': 41600, 'cuota_mensual': 321600, 'saldo_capital': 3880000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-11-23', 'valor_cuota': 280000, 'interes_mes': 38800, 'cuota_mensual': 318800, 'saldo_capital': 3600000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-12-23', 'valor_cuota': 280000, 'interes_mes': 36000, 'cuota_mensual': 316000, 'saldo_capital': 3320000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-01-23', 'valor_cuota': 280000, 'interes_mes': 33200, 'cuota_mensual': 313200, 'saldo_capital': 3040000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-02-23', 'valor_cuota': 280000, 'interes_mes': 30400, 'cuota_mensual': 310400, 'saldo_capital': 2760000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-03-23', 'valor_cuota': 280000, 'interes_mes': 27600, 'cuota_mensual': 307600, 'saldo_capital': 2480000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-04-23', 'valor_cuota': 280000, 'interes_mes': 24800, 'cuota_mensual': 304800, 'saldo_capital': 2200000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-05-23', 'valor_cuota': 280000, 'interes_mes': 22000, 'cuota_mensual': 302000, 'saldo_capital': 1920000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-06-23', 'valor_cuota': 280000, 'interes_mes': 19200, 'cuota_mensual': 299200, 'saldo_capital': 1640000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-07-23', 'valor_cuota': 280000, 'interes_mes': 16400, 'cuota_mensual': 296400, 'saldo_capital': 1360000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-08-23', 'valor_cuota': 280000, 'interes_mes': 13600, 'cuota_mensual': 293600, 'saldo_capital': 1080000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-09-23', 'valor_cuota': 280000, 'interes_mes': 10800, 'cuota_mensual': 290800, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-10-23', 'valor_cuota': 280000, 'interes_mes': 8000, 'cuota_mensual': 288000, 'saldo_capital': 520000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-11-23', 'valor_cuota': 280000, 'interes_mes': 5200, 'cuota_mensual': 285200, 'saldo_capital': 240000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-12-23', 'valor_cuota': 240000, 'interes_mes': 2400, 'cuota_mensual': 242400, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 439,
            'capital': 3500000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-07-14',
            'socios_ids': [44,42],  # ANGIE DANIELA LUNA TORO / OLGA PATRICIA TORO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-09-06', 'valor_cuota': 150000, 'interes_mes': 35000, 'cuota_mensual': 185000, 'saldo_capital': 3350000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-10-06', 'valor_cuota': 150000, 'interes_mes': 33500, 'cuota_mensual': 183500, 'saldo_capital': 3200000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-11-06', 'valor_cuota': 150000, 'interes_mes': 32000, 'cuota_mensual': 182000, 'saldo_capital': 3050000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-12-06', 'valor_cuota': 150000, 'interes_mes': 30500, 'cuota_mensual': 180500, 'saldo_capital': 2900000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2026-01-06', 'valor_cuota': 150000, 'interes_mes': 29000, 'cuota_mensual': 179000, 'saldo_capital': 2750000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-02-06', 'valor_cuota': 150000, 'interes_mes': 27500, 'cuota_mensual': 177500, 'saldo_capital': 2600000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-03-06', 'valor_cuota': 150000, 'interes_mes': 26000, 'cuota_mensual': 176000, 'saldo_capital': 2450000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-04-06', 'valor_cuota': 150000, 'interes_mes': 24500, 'cuota_mensual': 174500, 'saldo_capital': 2300000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-05-06', 'valor_cuota': 150000, 'interes_mes': 23000, 'cuota_mensual': 173000, 'saldo_capital': 2150000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-06-06', 'valor_cuota': 150000, 'interes_mes': 21500, 'cuota_mensual': 171500, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-07-06', 'valor_cuota': 150000, 'interes_mes': 20000, 'cuota_mensual': 170000, 'saldo_capital': 1850000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-08-06', 'valor_cuota': 150000, 'interes_mes': 18500, 'cuota_mensual': 168500, 'saldo_capital': 1700000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-09-06', 'valor_cuota': 150000, 'interes_mes': 17000, 'cuota_mensual': 167000, 'saldo_capital': 1550000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-10-06', 'valor_cuota': 150000, 'interes_mes': 15500, 'cuota_mensual': 165500, 'saldo_capital': 1400000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-11-06', 'valor_cuota': 150000, 'interes_mes': 14000, 'cuota_mensual': 164000, 'saldo_capital': 1250000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-12-06', 'valor_cuota': 150000, 'interes_mes': 12500, 'cuota_mensual': 162500, 'saldo_capital': 1100000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2027-01-06', 'valor_cuota': 150000, 'interes_mes': 11000, 'cuota_mensual': 161000, 'saldo_capital': 950000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-02-06', 'valor_cuota': 150000, 'interes_mes': 9500, 'cuota_mensual': 159500, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-03-06', 'valor_cuota': 150000, 'interes_mes': 8000, 'cuota_mensual': 158000, 'saldo_capital': 650000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-04-06', 'valor_cuota': 150000, 'interes_mes': 6500, 'cuota_mensual': 156500, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-05-06', 'valor_cuota': 150000, 'interes_mes': 5000, 'cuota_mensual': 155000, 'saldo_capital': 350000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-06-06', 'valor_cuota': 150000, 'interes_mes': 3500, 'cuota_mensual': 153500, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-07-06', 'valor_cuota': 150000, 'interes_mes': 2000, 'cuota_mensual': 152000, 'saldo_capital': 50000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-08-06', 'valor_cuota': 50000, 'interes_mes': 500, 'cuota_mensual': 50500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 368,
            'capital': 5000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2023-10-25',
            'socios_ids': [54,50],  # AMPARO FLOREZ CASTRO Y/O LUIS F. VALLEJOS F.
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-11-25', 'valor_cuota': 140000, 'interes_mes': 50000, 'cuota_mensual': 190000, 'saldo_capital': 4860000, 'fecha_pago': '2023-11-14'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2023-12-25', 'valor_cuota': 140000, 'interes_mes': 48600, 'cuota_mensual': 188600, 'saldo_capital': 4720000, 'fecha_pago': '2023-12-21'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-01-25', 'valor_cuota': 140000, 'interes_mes': 47200, 'cuota_mensual': 187200, 'saldo_capital': 4580000, 'fecha_pago': '2024-01-14'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-02-25', 'valor_cuota': 140000, 'interes_mes': 45800, 'cuota_mensual': 185800, 'saldo_capital': 4440000, 'fecha_pago': '2024-02-24'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-03-25', 'valor_cuota': 140000, 'interes_mes': 44400, 'cuota_mensual': 184400, 'saldo_capital': 4300000, 'fecha_pago': '2024-03-27'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-04-25', 'valor_cuota': 140000, 'interes_mes': 43000, 'cuota_mensual': 183000, 'saldo_capital': 4160000, 'fecha_pago': '2024-04-22'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-05-25', 'valor_cuota': 140000, 'interes_mes': 41600, 'cuota_mensual': 181600, 'saldo_capital': 4020000, 'fecha_pago': '2024-05-18'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-06-25', 'valor_cuota': 140000, 'interes_mes': 40200, 'cuota_mensual': 180200, 'saldo_capital': 3880000, 'fecha_pago': '2024-06-25'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-07-25', 'valor_cuota': 140000, 'interes_mes': 38800, 'cuota_mensual': 178800, 'saldo_capital': 3740000, 'fecha_pago': '2024-07-29'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-08-25', 'valor_cuota': 140000, 'interes_mes': 37400, 'cuota_mensual': 177400, 'saldo_capital': 3600000, 'fecha_pago': '2024-08-26'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-09-25', 'valor_cuota': 140000, 'interes_mes': 36000, 'cuota_mensual': 176000, 'saldo_capital': 3460000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-10-25', 'valor_cuota': 140000, 'interes_mes': 34600, 'cuota_mensual': 174600, 'saldo_capital': 3320000, 'fecha_pago': '2024-10-27'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-11-25', 'valor_cuota': 140000, 'interes_mes': 33200, 'cuota_mensual': 173200, 'saldo_capital': 3180000, 'fecha_pago': '2024-11-24'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2024-12-25', 'valor_cuota': 140000, 'interes_mes': 31800, 'cuota_mensual': 171800, 'saldo_capital': 3040000, 'fecha_pago': '2024-12-27'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-01-25', 'valor_cuota': 140000, 'interes_mes': 30400, 'cuota_mensual': 170400, 'saldo_capital': 2900000, 'fecha_pago': '2025-01-24'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-02-25', 'valor_cuota': 140000, 'interes_mes': 29000, 'cuota_mensual': 169000, 'saldo_capital': 2760000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-03-25', 'valor_cuota': 140000, 'interes_mes': 27600, 'cuota_mensual': 167600, 'saldo_capital': 2620000, 'fecha_pago': '2025-03-29'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-04-25', 'valor_cuota': 140000, 'interes_mes': 26200, 'cuota_mensual': 166200, 'saldo_capital': 2480000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-05-25', 'valor_cuota': 140000, 'interes_mes': 24800, 'cuota_mensual': 164800, 'saldo_capital': 2340000, 'fecha_pago': '2025-05-30'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-06-25', 'valor_cuota': 140000, 'interes_mes': 23400, 'cuota_mensual': 163400, 'saldo_capital': 2200000, 'fecha_pago': '2025-07-29'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-07-25', 'valor_cuota': 140000, 'interes_mes': 22000, 'cuota_mensual': 162000, 'saldo_capital': 2060000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-08-25', 'valor_cuota': 140000, 'interes_mes': 20600, 'cuota_mensual': 160600, 'saldo_capital': 1920000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-09-25', 'valor_cuota': 140000, 'interes_mes': 19200, 'cuota_mensual': 159200, 'saldo_capital': 1780000, 'fecha_pago': '2025-10-27'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-10-25', 'valor_cuota': 140000, 'interes_mes': 17800, 'cuota_mensual': 157800, 'saldo_capital': 1640000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-11-25', 'valor_cuota': 140000, 'interes_mes': 16400, 'cuota_mensual': 156400, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2025-12-25', 'valor_cuota': 140000, 'interes_mes': 15000, 'cuota_mensual': 155000, 'saldo_capital': 1360000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-01-25', 'valor_cuota': 140000, 'interes_mes': 13600, 'cuota_mensual': 153600, 'saldo_capital': 1220000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2026-02-25', 'valor_cuota': 140000, 'interes_mes': 12200, 'cuota_mensual': 152200, 'saldo_capital': 1080000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2026-03-25', 'valor_cuota': 140000, 'interes_mes': 10800, 'cuota_mensual': 150800, 'saldo_capital': 940000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2026-04-25', 'valor_cuota': 140000, 'interes_mes': 9400, 'cuota_mensual': 149400, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2026-05-25', 'valor_cuota': 140000, 'interes_mes': 8000, 'cuota_mensual': 148000, 'saldo_capital': 660000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-06-25', 'valor_cuota': 140000, 'interes_mes': 6600, 'cuota_mensual': 146600, 'saldo_capital': 520000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-07-25', 'valor_cuota': 140000, 'interes_mes': 5200, 'cuota_mensual': 145200, 'saldo_capital': 380000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2026-08-25', 'valor_cuota': 140000, 'interes_mes': 3800, 'cuota_mensual': 143800, 'saldo_capital': 240000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2026-09-25', 'valor_cuota': 140000, 'interes_mes': 2400, 'cuota_mensual': 142400, 'saldo_capital': 100000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-10-25', 'valor_cuota': 100000, 'interes_mes': 1000, 'cuota_mensual': 101000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 419,
            'capital': 6000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-02-12',
            'socios_ids': [54,50],  # LUIS FERNANDO VALLEJOS / AMPARO FLORES CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-03-12', 'valor_cuota': 250000, 'interes_mes': 60000, 'cuota_mensual': 310000, 'saldo_capital': 5750000, 'fecha_pago': '2025-03-29'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-04-12', 'valor_cuota': 250000, 'interes_mes': 57500, 'cuota_mensual': 307500, 'saldo_capital': 5500000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-05-12', 'valor_cuota': 250000, 'interes_mes': 55000, 'cuota_mensual': 305000, 'saldo_capital': 5250000, 'fecha_pago': '2025-05-30'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-06-12', 'valor_cuota': 250000, 'interes_mes': 52500, 'cuota_mensual': 302500, 'saldo_capital': 5000000, 'fecha_pago': '2025-06-27'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-07-12', 'valor_cuota': 250000, 'interes_mes': 50000, 'cuota_mensual': 300000, 'saldo_capital': 4750000, 'fecha_pago': '2025-07-27'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-08-12', 'valor_cuota': 250000, 'interes_mes': 47500, 'cuota_mensual': 297500, 'saldo_capital': 4500000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-09-12', 'valor_cuota': 250000, 'interes_mes': 45000, 'cuota_mensual': 295000, 'saldo_capital': 4250000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-10-12', 'valor_cuota': 250000, 'interes_mes': 42500, 'cuota_mensual': 292500, 'saldo_capital': 4000000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-11-12', 'valor_cuota': 250000, 'interes_mes': 40000, 'cuota_mensual': 290000, 'saldo_capital': 3750000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-12-12', 'valor_cuota': 250000, 'interes_mes': 37500, 'cuota_mensual': 287500, 'saldo_capital': 3500000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-01-12', 'valor_cuota': 250000, 'interes_mes': 35000, 'cuota_mensual': 285000, 'saldo_capital': 3250000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-02-12', 'valor_cuota': 250000, 'interes_mes': 32500, 'cuota_mensual': 282500, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-03-12', 'valor_cuota': 250000, 'interes_mes': 30000, 'cuota_mensual': 280000, 'saldo_capital': 2750000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-04-12', 'valor_cuota': 250000, 'interes_mes': 27500, 'cuota_mensual': 277500, 'saldo_capital': 2500000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-05-12', 'valor_cuota': 250000, 'interes_mes': 25000, 'cuota_mensual': 275000, 'saldo_capital': 2250000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-06-12', 'valor_cuota': 250000, 'interes_mes': 22500, 'cuota_mensual': 272500, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-07-12', 'valor_cuota': 250000, 'interes_mes': 20000, 'cuota_mensual': 270000, 'saldo_capital': 1750000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-08-12', 'valor_cuota': 250000, 'interes_mes': 17500, 'cuota_mensual': 267500, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-09-12', 'valor_cuota': 250000, 'interes_mes': 15000, 'cuota_mensual': 265000, 'saldo_capital': 1250000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-10-12', 'valor_cuota': 250000, 'interes_mes': 12500, 'cuota_mensual': 262500, 'saldo_capital': 1000000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-11-12', 'valor_cuota': 250000, 'interes_mes': 10000, 'cuota_mensual': 260000, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-12-12', 'valor_cuota': 250000, 'interes_mes': 7500, 'cuota_mensual': 257500, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-01-12', 'valor_cuota': 250000, 'interes_mes': 5000, 'cuota_mensual': 255000, 'saldo_capital': 250000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-02-12', 'valor_cuota': 250000, 'interes_mes': 2500, 'cuota_mensual': 252500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 350,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2023-05-20',
            'socios_ids': [51,50],  # MIGUEL A. VALLEJO FLOREZ / AMPARO FLOREZ CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2023-06-20', 'valor_cuota': 278000, 'interes_mes': 100000, 'cuota_mensual': 378000, 'saldo_capital': 9722000, 'fecha_pago': '2023-06-14'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2023-07-20', 'valor_cuota': 278000, 'interes_mes': 97220, 'cuota_mensual': 375220, 'saldo_capital': 9444000, 'fecha_pago': '2023-07-10'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2023-08-20', 'valor_cuota': 278000, 'interes_mes': 94440, 'cuota_mensual': 372440, 'saldo_capital': 9166000, 'fecha_pago': '2023-08-14'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2023-09-20', 'valor_cuota': 278000, 'interes_mes': 91660, 'cuota_mensual': 369660, 'saldo_capital': 8888000, 'fecha_pago': '2023-09-21'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2023-10-20', 'valor_cuota': 278000, 'interes_mes': 88880, 'cuota_mensual': 366880, 'saldo_capital': 8610000, 'fecha_pago': '2023-10-17'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2023-11-20', 'valor_cuota': 278000, 'interes_mes': 86100, 'cuota_mensual': 364100, 'saldo_capital': 8332000, 'fecha_pago': '2023-11-16'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2023-12-20', 'valor_cuota': 278000, 'interes_mes': 83320, 'cuota_mensual': 361320, 'saldo_capital': 8054000, 'fecha_pago': '2023-12-21'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-01-20', 'valor_cuota': 278000, 'interes_mes': 80540, 'cuota_mensual': 358540, 'saldo_capital': 7776000, 'fecha_pago': '2024-02-07'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-02-20', 'valor_cuota': 278000, 'interes_mes': 77760, 'cuota_mensual': 355760, 'saldo_capital': 7498000, 'fecha_pago': '2024-02-29'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-03-20', 'valor_cuota': 278000, 'interes_mes': 74980, 'cuota_mensual': 352980, 'saldo_capital': 7220000, 'fecha_pago': '2024-04-06'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-04-20', 'valor_cuota': 278000, 'interes_mes': 72200, 'cuota_mensual': 350200, 'saldo_capital': 6942000, 'fecha_pago': '2024-05-18'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2024-05-20', 'valor_cuota': 278000, 'interes_mes': 69420, 'cuota_mensual': 347420, 'saldo_capital': 6664000, 'fecha_pago': '2024-06-25'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2024-06-20', 'valor_cuota': 278000, 'interes_mes': 66640, 'cuota_mensual': 344640, 'saldo_capital': 6386000, 'fecha_pago': '2024-07-29'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2024-07-20', 'valor_cuota': 278000, 'interes_mes': 63860, 'cuota_mensual': 341860, 'saldo_capital': 6108000, 'fecha_pago': '2024-08-26'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2024-08-20', 'valor_cuota': 278000, 'interes_mes': 61080, 'cuota_mensual': 339080, 'saldo_capital': 5830000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2024-09-20', 'valor_cuota': 278000, 'interes_mes': 58300, 'cuota_mensual': 336300, 'saldo_capital': 5552000, 'fecha_pago': '2024-10-29'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2024-10-20', 'valor_cuota': 278000, 'interes_mes': 55520, 'cuota_mensual': 333520, 'saldo_capital': 5274000, 'fecha_pago': '2024-11-27'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2024-11-20', 'valor_cuota': 278000, 'interes_mes': 52740, 'cuota_mensual': 330740, 'saldo_capital': 4996000, 'fecha_pago': '2024-12-27'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2024-12-20', 'valor_cuota': 278000, 'interes_mes': 49960, 'cuota_mensual': 327960, 'saldo_capital': 4718000, 'fecha_pago': '2025-01-27'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-01-20', 'valor_cuota': 278000, 'interes_mes': 47180, 'cuota_mensual': 325180, 'saldo_capital': 4440000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-02-20', 'valor_cuota': 278000, 'interes_mes': 44400, 'cuota_mensual': 322400, 'saldo_capital': 4162000, 'fecha_pago': '2025-03-29'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-03-20', 'valor_cuota': 278000, 'interes_mes': 41620, 'cuota_mensual': 319620, 'saldo_capital': 3884000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-04-20', 'valor_cuota': 278000, 'interes_mes': 38840, 'cuota_mensual': 316840, 'saldo_capital': 3606000, 'fecha_pago': '2025-05-30'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2025-05-20', 'valor_cuota': 278000, 'interes_mes': 36060, 'cuota_mensual': 314060, 'saldo_capital': 3328000, 'fecha_pago': '2025-06-27'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2025-06-20', 'valor_cuota': 278000, 'interes_mes': 33280, 'cuota_mensual': 311280, 'saldo_capital': 3050000, 'fecha_pago': '2025-07-10'},
                {'nro_cuota': 26, 'fecha_vencimiento': '2025-07-20', 'valor_cuota': 278000, 'interes_mes': 30500, 'cuota_mensual': 308500, 'saldo_capital': 2772000, 'fecha_pago': '2025-07-29'},
                {'nro_cuota': 27, 'fecha_vencimiento': '2025-08-20', 'valor_cuota': 278000, 'interes_mes': 27720, 'cuota_mensual': 305720, 'saldo_capital': 2494000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 28, 'fecha_vencimiento': '2025-09-20', 'valor_cuota': 278000, 'interes_mes': 24940, 'cuota_mensual': 302940, 'saldo_capital': 2216000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 29, 'fecha_vencimiento': '2025-10-20', 'valor_cuota': 278000, 'interes_mes': 22160, 'cuota_mensual': 300160, 'saldo_capital': 1938000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 30, 'fecha_vencimiento': '2025-11-20', 'valor_cuota': 278000, 'interes_mes': 19380, 'cuota_mensual': 297380, 'saldo_capital': 1660000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 31, 'fecha_vencimiento': '2025-12-20', 'valor_cuota': 278000, 'interes_mes': 16600, 'cuota_mensual': 294600, 'saldo_capital': 1382000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2026-01-20', 'valor_cuota': 278000, 'interes_mes': 13820, 'cuota_mensual': 291820, 'saldo_capital': 1104000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2026-02-20', 'valor_cuota': 278000, 'interes_mes': 11040, 'cuota_mensual': 289040, 'saldo_capital': 826000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2026-03-20', 'valor_cuota': 278000, 'interes_mes': 8260, 'cuota_mensual': 286260, 'saldo_capital': 548000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2026-04-20', 'valor_cuota': 278000, 'interes_mes': 5480, 'cuota_mensual': 283480, 'saldo_capital': 270000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2026-05-20', 'valor_cuota': 270000, 'interes_mes': 2700, 'cuota_mensual': 272700, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 304,
            'capital': 15000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 60,
            'fecha_inicio': '2021-02-20',
            'socios_ids': [51,50],  # MIGUEL A. VALLEJO Y/O AMPARO FLOREZ CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2021-03-20', 'valor_cuota': 250000, 'interes_mes': 150000, 'cuota_mensual': 400000, 'saldo_capital': 14750000, 'fecha_pago': '2021-04-09'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2021-04-20', 'valor_cuota': 250000, 'interes_mes': 147500, 'cuota_mensual': 397500, 'saldo_capital': 14500000, 'fecha_pago': '2021-05-06'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2021-05-20', 'valor_cuota': 250000, 'interes_mes': 145000, 'cuota_mensual': 395000, 'saldo_capital': 14250000, 'fecha_pago': '2021-06-15'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2021-06-20', 'valor_cuota': 250000, 'interes_mes': 142500, 'cuota_mensual': 392500, 'saldo_capital': 14000000, 'fecha_pago': '2021-07-13'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2021-07-20', 'valor_cuota': 250000, 'interes_mes': 140000, 'cuota_mensual': 390000, 'saldo_capital': 13750000, 'fecha_pago': '2021-08-09'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2021-08-20', 'valor_cuota': 250000, 'interes_mes': 137500, 'cuota_mensual': 387500, 'saldo_capital': 13500000, 'fecha_pago': '2021-09-12'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2021-09-20', 'valor_cuota': 250000, 'interes_mes': 135000, 'cuota_mensual': 385000, 'saldo_capital': 13250000, 'fecha_pago': '2021-10-07'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2021-10-20', 'valor_cuota': 250000, 'interes_mes': 132500, 'cuota_mensual': 382500, 'saldo_capital': 13000000, 'fecha_pago': '2021-11-13'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2021-11-20', 'valor_cuota': 250000, 'interes_mes': 130000, 'cuota_mensual': 380000, 'saldo_capital': 12750000, 'fecha_pago': '2021-12-23'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2021-12-20', 'valor_cuota': 250000, 'interes_mes': 127500, 'cuota_mensual': 377500, 'saldo_capital': 12500000, 'fecha_pago': '2022-01-20'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2022-01-20', 'valor_cuota': 250000, 'interes_mes': 125000, 'cuota_mensual': 375000, 'saldo_capital': 12250000, 'fecha_pago': '2022-02-14'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2022-02-20', 'valor_cuota': 250000, 'interes_mes': 122500, 'cuota_mensual': 372500, 'saldo_capital': 12000000, 'fecha_pago': '2022-03-16'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2022-03-20', 'valor_cuota': 250000, 'interes_mes': 120000, 'cuota_mensual': 370000, 'saldo_capital': 11750000, 'fecha_pago': '2022-04-14'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2022-04-20', 'valor_cuota': 250000, 'interes_mes': 117500, 'cuota_mensual': 367500, 'saldo_capital': 11500000, 'fecha_pago': '2022-05-18'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2022-05-20', 'valor_cuota': 250000, 'interes_mes': 115000, 'cuota_mensual': 365000, 'saldo_capital': 11250000, 'fecha_pago': '2022-06-12'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2022-06-20', 'valor_cuota': 250000, 'interes_mes': 112500, 'cuota_mensual': 362500, 'saldo_capital': 11000000, 'fecha_pago': '2022-07-14'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2022-07-20', 'valor_cuota': 250000, 'interes_mes': 110000, 'cuota_mensual': 360000, 'saldo_capital': 10750000, 'fecha_pago': '2022-08-13'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2022-08-20', 'valor_cuota': 250000, 'interes_mes': 107500, 'cuota_mensual': 357500, 'saldo_capital': 10500000, 'fecha_pago': '2022-10-18'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2022-09-20', 'valor_cuota': 250000, 'interes_mes': 105000, 'cuota_mensual': 355000, 'saldo_capital': 10250000, 'fecha_pago': '2022-11-17'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2022-10-20', 'valor_cuota': 250000, 'interes_mes': 102500, 'cuota_mensual': 352500, 'saldo_capital': 10000000, 'fecha_pago': '2022-12-20'},
                {'nro_cuota': 21, 'fecha_vencimiento': '2022-11-20', 'valor_cuota': 250000, 'interes_mes': 100000, 'cuota_mensual': 350000, 'saldo_capital': 9750000, 'fecha_pago': '2023-01-10'},
                {'nro_cuota': 22, 'fecha_vencimiento': '2022-12-20', 'valor_cuota': 250000, 'interes_mes': 97500, 'cuota_mensual': 347500, 'saldo_capital': 9500000, 'fecha_pago': '2023-02-11'},
                {'nro_cuota': 23, 'fecha_vencimiento': '2023-01-20', 'valor_cuota': 250000, 'interes_mes': 95000, 'cuota_mensual': 345000, 'saldo_capital': 9250000, 'fecha_pago': '2023-03-13'},
                {'nro_cuota': 24, 'fecha_vencimiento': '2023-02-20', 'valor_cuota': 250000, 'interes_mes': 92500, 'cuota_mensual': 342500, 'saldo_capital': 9000000, 'fecha_pago': '2023-04-14'},
                {'nro_cuota': 25, 'fecha_vencimiento': '2023-03-20', 'valor_cuota': 250000, 'interes_mes': 90000, 'cuota_mensual': 340000, 'saldo_capital': 8750000, 'fecha_pago': '2023-05-17'},
                {'nro_cuota': 26, 'fecha_vencimiento': '2023-04-20', 'valor_cuota': 250000, 'interes_mes': 87500, 'cuota_mensual': 337500, 'saldo_capital': 8500000, 'fecha_pago': '2023-06-14'},
                {'nro_cuota': 27, 'fecha_vencimiento': '2023-05-20', 'valor_cuota': 250000, 'interes_mes': 85000, 'cuota_mensual': 335000, 'saldo_capital': 8250000, 'fecha_pago': '2023-07-10'},
                {'nro_cuota': 28, 'fecha_vencimiento': '2023-06-20', 'valor_cuota': 250000, 'interes_mes': 82500, 'cuota_mensual': 332500, 'saldo_capital': 8000000, 'fecha_pago': '2023-08-14'},
                {'nro_cuota': 29, 'fecha_vencimiento': '2023-07-20', 'valor_cuota': 250000, 'interes_mes': 80000, 'cuota_mensual': 330000, 'saldo_capital': 7750000, 'fecha_pago': '2023-09-21'},
                {'nro_cuota': 30, 'fecha_vencimiento': '2023-08-20', 'valor_cuota': 250000, 'interes_mes': 77500, 'cuota_mensual': 327500, 'saldo_capital': 7500000, 'fecha_pago': '2023-10-17'},
                {'nro_cuota': 31, 'fecha_vencimiento': '2023-09-20', 'valor_cuota': 250000, 'interes_mes': 75000, 'cuota_mensual': 325000, 'saldo_capital': 7250000, 'fecha_pago': '2023-11-16'},
                {'nro_cuota': 32, 'fecha_vencimiento': '2023-10-20', 'valor_cuota': 250000, 'interes_mes': 72500, 'cuota_mensual': 322500, 'saldo_capital': 7000000, 'fecha_pago': '2023-12-21'},
                {'nro_cuota': 33, 'fecha_vencimiento': '2023-11-20', 'valor_cuota': 250000, 'interes_mes': 70000, 'cuota_mensual': 320000, 'saldo_capital': 6750000, 'fecha_pago': '2024-02-07'},
                {'nro_cuota': 34, 'fecha_vencimiento': '2023-12-20', 'valor_cuota': 250000, 'interes_mes': 67500, 'cuota_mensual': 317500, 'saldo_capital': 6500000, 'fecha_pago': '2024-02-29'},
                {'nro_cuota': 35, 'fecha_vencimiento': '2024-01-20', 'valor_cuota': 250000, 'interes_mes': 65000, 'cuota_mensual': 315000, 'saldo_capital': 6250000, 'fecha_pago': '2024-04-06'},
                {'nro_cuota': 36, 'fecha_vencimiento': '2024-02-20', 'valor_cuota': 250000, 'interes_mes': 62500, 'cuota_mensual': 312500, 'saldo_capital': 6000000, 'fecha_pago': '2024-05-28'},
                {'nro_cuota': 37, 'fecha_vencimiento': '2024-03-20', 'valor_cuota': 250000, 'interes_mes': 60000, 'cuota_mensual': 310000, 'saldo_capital': 5750000, 'fecha_pago': '2024-06-25'},
                {'nro_cuota': 38, 'fecha_vencimiento': '2024-04-20', 'valor_cuota': 250000, 'interes_mes': 57500, 'cuota_mensual': 307500, 'saldo_capital': 5500000, 'fecha_pago': '2024-07-29'},
                {'nro_cuota': 39, 'fecha_vencimiento': '2024-05-20', 'valor_cuota': 250000, 'interes_mes': 55000, 'cuota_mensual': 305000, 'saldo_capital': 5250000, 'fecha_pago': '2024-08-26'},
                {'nro_cuota': 40, 'fecha_vencimiento': '2024-06-20', 'valor_cuota': 250000, 'interes_mes': 52500, 'cuota_mensual': 302500, 'saldo_capital': 5000000, 'fecha_pago': '2024-09-26'},
                {'nro_cuota': 41, 'fecha_vencimiento': '2024-07-20', 'valor_cuota': 250000, 'interes_mes': 50000, 'cuota_mensual': 300000, 'saldo_capital': 4750000, 'fecha_pago': '2024-10-29'},
                {'nro_cuota': 42, 'fecha_vencimiento': '2024-08-20', 'valor_cuota': 250000, 'interes_mes': 47500, 'cuota_mensual': 297500, 'saldo_capital': 4500000, 'fecha_pago': '2024-11-27'},
                {'nro_cuota': 43, 'fecha_vencimiento': '2024-09-20', 'valor_cuota': 250000, 'interes_mes': 45000, 'cuota_mensual': 295000, 'saldo_capital': 4250000, 'fecha_pago': '2024-12-27'},
                {'nro_cuota': 44, 'fecha_vencimiento': '2024-10-20', 'valor_cuota': 250000, 'interes_mes': 42500, 'cuota_mensual': 292500, 'saldo_capital': 4000000, 'fecha_pago': '2025-01-27'},
                {'nro_cuota': 45, 'fecha_vencimiento': '2024-11-20', 'valor_cuota': 250000, 'interes_mes': 40000, 'cuota_mensual': 290000, 'saldo_capital': 3750000, 'fecha_pago': '2025-02-27'},
                {'nro_cuota': 46, 'fecha_vencimiento': '2024-12-20', 'valor_cuota': 250000, 'interes_mes': 37500, 'cuota_mensual': 287500, 'saldo_capital': 3500000, 'fecha_pago': '2025-03-29'},
                {'nro_cuota': 47, 'fecha_vencimiento': '2025-01-20', 'valor_cuota': 250000, 'interes_mes': 35000, 'cuota_mensual': 285000, 'saldo_capital': 3250000, 'fecha_pago': '2025-04-28'},
                {'nro_cuota': 48, 'fecha_vencimiento': '2025-02-20', 'valor_cuota': 250000, 'interes_mes': 32500, 'cuota_mensual': 282500, 'saldo_capital': 3000000, 'fecha_pago': '2025-05-30'},
                {'nro_cuota': 49, 'fecha_vencimiento': '2025-03-20', 'valor_cuota': 250000, 'interes_mes': 30000, 'cuota_mensual': 280000, 'saldo_capital': 2750000, 'fecha_pago': '2025-06-27'},
                {'nro_cuota': 50, 'fecha_vencimiento': '2025-04-20', 'valor_cuota': 250000, 'interes_mes': 27500, 'cuota_mensual': 277500, 'saldo_capital': 2500000, 'fecha_pago': '2025-07-10'},
                {'nro_cuota': 51, 'fecha_vencimiento': '2025-05-20', 'valor_cuota': 250000, 'interes_mes': 25000, 'cuota_mensual': 275000, 'saldo_capital': 2250000, 'fecha_pago': '2025-07-29'},
                {'nro_cuota': 52, 'fecha_vencimiento': '2025-06-20', 'valor_cuota': 250000, 'interes_mes': 22500, 'cuota_mensual': 272500, 'saldo_capital': 2000000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 53, 'fecha_vencimiento': '2025-07-20', 'valor_cuota': 250000, 'interes_mes': 20000, 'cuota_mensual': 270000, 'saldo_capital': 1750000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 54, 'fecha_vencimiento': '2025-08-20', 'valor_cuota': 250000, 'interes_mes': 17500, 'cuota_mensual': 267500, 'saldo_capital': 1500000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 55, 'fecha_vencimiento': '2025-09-20', 'valor_cuota': 250000, 'interes_mes': 15000, 'cuota_mensual': 265000, 'saldo_capital': 1250000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 56, 'fecha_vencimiento': '2025-10-20', 'valor_cuota': 250000, 'interes_mes': 12500, 'cuota_mensual': 262500, 'saldo_capital': 1000000, 'fecha_pago': None},
                {'nro_cuota': 57, 'fecha_vencimiento': '2025-11-20', 'valor_cuota': 250000, 'interes_mes': 10000, 'cuota_mensual': 260000, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 58, 'fecha_vencimiento': '2025-12-20', 'valor_cuota': 250000, 'interes_mes': 7500, 'cuota_mensual': 257500, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 59, 'fecha_vencimiento': '2026-01-20', 'valor_cuota': 250000, 'interes_mes': 5000, 'cuota_mensual': 255000, 'saldo_capital': 250000, 'fecha_pago': None},
                {'nro_cuota': 60, 'fecha_vencimiento': '2026-02-20', 'valor_cuota': 250000, 'interes_mes': 2500, 'cuota_mensual': 252500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },


        {
            'letra': 436,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2025-08-02',
            'socios_ids': [51,50],  # MIGUEL ANDRES VALLEJOS FLOREZ / AMPARO FLOREZ CASTRO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-08-02', 'valor_cuota': 280000, 'interes_mes': 100000, 'cuota_mensual': 380000, 'saldo_capital': 9720000, 'fecha_pago': '2025-08-29'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-09-02', 'valor_cuota': 280000, 'interes_mes': 97200, 'cuota_mensual': 377200, 'saldo_capital': 9440000, 'fecha_pago': '2025-09-28'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-10-02', 'valor_cuota': 280000, 'interes_mes': 94400, 'cuota_mensual': 374400, 'saldo_capital': 9160000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-11-02', 'valor_cuota': 280000, 'interes_mes': 91600, 'cuota_mensual': 371600, 'saldo_capital': 8880000, 'fecha_pago': '2025-11-24'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-12-02', 'valor_cuota': 280000, 'interes_mes': 88800, 'cuota_mensual': 368800, 'saldo_capital': 8600000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-01-02', 'valor_cuota': 280000, 'interes_mes': 86000, 'cuota_mensual': 366000, 'saldo_capital': 8320000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-02-02', 'valor_cuota': 280000, 'interes_mes': 83200, 'cuota_mensual': 363200, 'saldo_capital': 8040000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-03-02', 'valor_cuota': 280000, 'interes_mes': 80400, 'cuota_mensual': 360400, 'saldo_capital': 7760000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-04-02', 'valor_cuota': 280000, 'interes_mes': 77600, 'cuota_mensual': 357600, 'saldo_capital': 7480000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-05-02', 'valor_cuota': 280000, 'interes_mes': 74800, 'cuota_mensual': 354800, 'saldo_capital': 7200000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-06-02', 'valor_cuota': 280000, 'interes_mes': 72000, 'cuota_mensual': 352000, 'saldo_capital': 6920000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-07-02', 'valor_cuota': 280000, 'interes_mes': 69200, 'cuota_mensual': 349200, 'saldo_capital': 6640000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-08-02', 'valor_cuota': 280000, 'interes_mes': 66400, 'cuota_mensual': 346400, 'saldo_capital': 6360000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-09-02', 'valor_cuota': 280000, 'interes_mes': 63600, 'cuota_mensual': 343600, 'saldo_capital': 6080000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-10-02', 'valor_cuota': 280000, 'interes_mes': 60800, 'cuota_mensual': 340800, 'saldo_capital': 5800000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-11-02', 'valor_cuota': 280000, 'interes_mes': 58000, 'cuota_mensual': 338000, 'saldo_capital': 5520000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-12-02', 'valor_cuota': 280000, 'interes_mes': 55200, 'cuota_mensual': 335200, 'saldo_capital': 5240000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-01-02', 'valor_cuota': 280000, 'interes_mes': 52400, 'cuota_mensual': 332400, 'saldo_capital': 4960000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-02-02', 'valor_cuota': 280000, 'interes_mes': 49600, 'cuota_mensual': 329600, 'saldo_capital': 4680000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-03-02', 'valor_cuota': 280000, 'interes_mes': 46800, 'cuota_mensual': 326800, 'saldo_capital': 4400000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-04-02', 'valor_cuota': 280000, 'interes_mes': 44000, 'cuota_mensual': 324000, 'saldo_capital': 4120000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-05-02', 'valor_cuota': 280000, 'interes_mes': 41200, 'cuota_mensual': 321200, 'saldo_capital': 3840000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-06-02', 'valor_cuota': 280000, 'interes_mes': 38400, 'cuota_mensual': 318400, 'saldo_capital': 3560000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-07-02', 'valor_cuota': 280000, 'interes_mes': 35600, 'cuota_mensual': 315600, 'saldo_capital': 3280000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-08-02', 'valor_cuota': 280000, 'interes_mes': 32800, 'cuota_mensual': 312800, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-09-02', 'valor_cuota': 280000, 'interes_mes': 30000, 'cuota_mensual': 310000, 'saldo_capital': 2720000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-10-02', 'valor_cuota': 280000, 'interes_mes': 27200, 'cuota_mensual': 307200, 'saldo_capital': 2440000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-11-02', 'valor_cuota': 280000, 'interes_mes': 24400, 'cuota_mensual': 304400, 'saldo_capital': 2160000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-12-02', 'valor_cuota': 280000, 'interes_mes': 21600, 'cuota_mensual': 301600, 'saldo_capital': 1880000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2028-01-02', 'valor_cuota': 280000, 'interes_mes': 18800, 'cuota_mensual': 298800, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2028-02-02', 'valor_cuota': 280000, 'interes_mes': 16000, 'cuota_mensual': 296000, 'saldo_capital': 1320000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2028-03-02', 'valor_cuota': 280000, 'interes_mes': 13200, 'cuota_mensual': 293200, 'saldo_capital': 1040000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-04-02', 'valor_cuota': 280000, 'interes_mes': 10400, 'cuota_mensual': 290400, 'saldo_capital': 760000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-05-02', 'valor_cuota': 280000, 'interes_mes': 7600, 'cuota_mensual': 287600, 'saldo_capital': 480000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-06-02', 'valor_cuota': 280000, 'interes_mes': 4800, 'cuota_mensual': 284800, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-07-02', 'valor_cuota': 200000, 'interes_mes': 2000, 'cuota_mensual': 202000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 401,
            'capital': 5000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2024-08-19',
            'socios_ids': [12,13],  # FANNY PADILLA JOJOA Y/O MABEL PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-09-19', 'valor_cuota': 210000, 'interes_mes': 50000, 'cuota_mensual': 260000, 'saldo_capital': 4790000, 'fecha_pago': '2024-10-07'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-10-19', 'valor_cuota': 210000, 'interes_mes': 47900, 'cuota_mensual': 257900, 'saldo_capital': 4580000, 'fecha_pago': '2024-11-02'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-11-19', 'valor_cuota': 210000, 'interes_mes': 45800, 'cuota_mensual': 255800, 'saldo_capital': 4370000, 'fecha_pago': '2024-11-29'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-12-19', 'valor_cuota': 210000, 'interes_mes': 43700, 'cuota_mensual': 253700, 'saldo_capital': 4160000, 'fecha_pago': '2024-12-26'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-01-10', 'valor_cuota': 210000, 'interes_mes': 41600, 'cuota_mensual': 251600, 'saldo_capital': 3050000, 'fecha_pago': '2025-02-08'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-02-19', 'valor_cuota': 210000, 'interes_mes': 39500, 'cuota_mensual': 249500, 'saldo_capital': 3740000, 'fecha_pago': '2025-03-09'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-03-19', 'valor_cuota': 210000, 'interes_mes': 37400, 'cuota_mensual': 247400, 'saldo_capital': 3530000, 'fecha_pago': '2025-04-13'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-04-19', 'valor_cuota': 210000, 'interes_mes': 35300, 'cuota_mensual': 245300, 'saldo_capital': 3320000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-05-19', 'valor_cuota': 210000, 'interes_mes': 33200, 'cuota_mensual': 243200, 'saldo_capital': 3110000, 'fecha_pago': '2025-06-18'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-06-19', 'valor_cuota': 210000, 'interes_mes': 31100, 'cuota_mensual': 241100, 'saldo_capital': 2900000, 'fecha_pago': '2025-07-27'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-07-19', 'valor_cuota': 210000, 'interes_mes': 29000, 'cuota_mensual': 239000, 'saldo_capital': 2690000, 'fecha_pago': '2025-08-18'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-08-19', 'valor_cuota': 210000, 'interes_mes': 26900, 'cuota_mensual': 236900, 'saldo_capital': 2480000, 'fecha_pago': '2025-09-22'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-09-19', 'valor_cuota': 210000, 'interes_mes': 24800, 'cuota_mensual': 234800, 'saldo_capital': 2270000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-10-19', 'valor_cuota': 210000, 'interes_mes': 22700, 'cuota_mensual': 232700, 'saldo_capital': 2060000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-11-19', 'valor_cuota': 210000, 'interes_mes': 20600, 'cuota_mensual': 230600, 'saldo_capital': 1850000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-12-19', 'valor_cuota': 210000, 'interes_mes': 18500, 'cuota_mensual': 228500, 'saldo_capital': 1640000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-01-19', 'valor_cuota': 210000, 'interes_mes': 16400, 'cuota_mensual': 226400, 'saldo_capital': 1430000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-02-19', 'valor_cuota': 210000, 'interes_mes': 14300, 'cuota_mensual': 224300, 'saldo_capital': 1220000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-03-19', 'valor_cuota': 210000, 'interes_mes': 12200, 'cuota_mensual': 222200, 'saldo_capital': 1010000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-04-19', 'valor_cuota': 210000, 'interes_mes': 10100, 'cuota_mensual': 220100, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-05-19', 'valor_cuota': 210000, 'interes_mes': 8000, 'cuota_mensual': 218000, 'saldo_capital': 590000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-06-19', 'valor_cuota': 210000, 'interes_mes': 5900, 'cuota_mensual': 215900, 'saldo_capital': 380000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-07-19', 'valor_cuota': 210000, 'interes_mes': 3800, 'cuota_mensual': 213800, 'saldo_capital': 170000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-08-19', 'valor_cuota': 170000, 'interes_mes': 1700, 'cuota_mensual': 171700, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 420,
            'capital': 2000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 10,
            'fecha_inicio': '2025-03-09',
            'socios_ids': [12,13],  # FANNY PADILLA JOJOA / MABEL PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-04-09', 'valor_cuota': 200000, 'interes_mes': 20000, 'cuota_mensual': 220000, 'saldo_capital': 1800000, 'fecha_pago': '2025-04-13'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-05-09', 'valor_cuota': 200000, 'interes_mes': 18000, 'cuota_mensual': 218000, 'saldo_capital': 1600000, 'fecha_pago': '2025-05-14'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-06-09', 'valor_cuota': 200000, 'interes_mes': 16000, 'cuota_mensual': 216000, 'saldo_capital': 1400000, 'fecha_pago': '2025-06-18'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-07-09', 'valor_cuota': 200000, 'interes_mes': 14000, 'cuota_mensual': 214000, 'saldo_capital': 1200000, 'fecha_pago': '2025-07-27'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-08-09', 'valor_cuota': 200000, 'interes_mes': 12000, 'cuota_mensual': 212000, 'saldo_capital': 1000000, 'fecha_pago': '2025-08-03'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-09-09', 'valor_cuota': 200000, 'interes_mes': 10000, 'cuota_mensual': 210000, 'saldo_capital': 800000, 'fecha_pago': '2025-09-09'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-10-09', 'valor_cuota': 200000, 'interes_mes': 8000, 'cuota_mensual': 208000, 'saldo_capital': 600000, 'fecha_pago': '2025-10-05'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-11-09', 'valor_cuota': 200000, 'interes_mes': 6000, 'cuota_mensual': 206000, 'saldo_capital': 400000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-12-09', 'valor_cuota': 200000, 'interes_mes': 4000, 'cuota_mensual': 204000, 'saldo_capital': 200000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-01-09', 'valor_cuota': 200000, 'interes_mes': 2000, 'cuota_mensual': 202000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 417,
            'capital': 4000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-07-14',
            'socios_ids': [12,13],  # FANNY PATRICIA PADILLA JOJOA / MABEL PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-03-09', 'valor_cuota': 167000, 'interes_mes': 40000, 'cuota_mensual': 207000, 'saldo_capital': 3833000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-04-09', 'valor_cuota': 167000, 'interes_mes': 38330, 'cuota_mensual': 205330, 'saldo_capital': 3666000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-05-09', 'valor_cuota': 167000, 'interes_mes': 36660, 'cuota_mensual': 203660, 'saldo_capital': 3499000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-06-09', 'valor_cuota': 167000, 'interes_mes': 34990, 'cuota_mensual': 201990, 'saldo_capital': 3332000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-07-09', 'valor_cuota': 167000, 'interes_mes': 33320, 'cuota_mensual': 200320, 'saldo_capital': 3165000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-08-09', 'valor_cuota': 167000, 'interes_mes': 31650, 'cuota_mensual': 198650, 'saldo_capital': 2998000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-09-09', 'valor_cuota': 167000, 'interes_mes': 29980, 'cuota_mensual': 196980, 'saldo_capital': 2831000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-10-09', 'valor_cuota': 167000, 'interes_mes': 28310, 'cuota_mensual': 195310, 'saldo_capital': 2664000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-11-09', 'valor_cuota': 167000, 'interes_mes': 26640, 'cuota_mensual': 193640, 'saldo_capital': 2497000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-12-09', 'valor_cuota': 167000, 'interes_mes': 24970, 'cuota_mensual': 191970, 'saldo_capital': 2330000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-01-09', 'valor_cuota': 167000, 'interes_mes': 21013, 'cuota_mensual': 188013, 'saldo_capital': 1934310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-02-09', 'valor_cuota': 167000, 'interes_mes': 19343, 'cuota_mensual': 186343, 'saldo_capital': 1767310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-03-09', 'valor_cuota': 167000, 'interes_mes': 17673, 'cuota_mensual': 184673, 'saldo_capital': 1600310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-04-09', 'valor_cuota': 167000, 'interes_mes': 16003, 'cuota_mensual': 183003, 'saldo_capital': 1433310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-05-09', 'valor_cuota': 167000, 'interes_mes': 14333, 'cuota_mensual': 181333, 'saldo_capital': 1266310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-06-09', 'valor_cuota': 167000, 'interes_mes': 12663, 'cuota_mensual': 179663, 'saldo_capital': 1099310, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-07-09', 'valor_cuota': 167000, 'interes_mes': 10993, 'cuota_mensual': 177993, 'saldo_capital': 932310, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-08-09', 'valor_cuota': 167000, 'interes_mes': 9323, 'cuota_mensual': 176323, 'saldo_capital': 765310, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-09-09', 'valor_cuota': 167000, 'interes_mes': 7653, 'cuota_mensual': 174653, 'saldo_capital': 598310, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-10-09', 'valor_cuota': 167000, 'interes_mes': 5983, 'cuota_mensual': 172983, 'saldo_capital': 431310, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-11-09', 'valor_cuota': 167000, 'interes_mes': 4313, 'cuota_mensual': 171313, 'saldo_capital': 264310, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-12-09', 'valor_cuota': 167000, 'interes_mes': 2643, 'cuota_mensual': 169643, 'saldo_capital': 97310, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-01-09', 'valor_cuota': 97310, 'interes_mes': 973, 'cuota_mensual': 98283, 'saldo_capital': 0, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-02-09', 'valor_cuota': 0, 'interes_mes': 0, 'cuota_mensual': 0, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 406,
            'capital': 5000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 36,
            'fecha_inicio': '2024-09-26',
            'socios_ids': [11,13],  # WILSON PADILLA JOJOA / MABEL PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-10-26', 'valor_cuota': 140000, 'interes_mes': 50000, 'cuota_mensual': 190000, 'saldo_capital': 4860000, 'fecha_pago': '2024-11-04'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-11-26', 'valor_cuota': 140000, 'interes_mes': 48600, 'cuota_mensual': 188600, 'saldo_capital': 4720000, 'fecha_pago': '2024-12-05'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-12-26', 'valor_cuota': 140000, 'interes_mes': 47200, 'cuota_mensual': 187200, 'saldo_capital': 4580000, 'fecha_pago': '2024-12-20'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-01-26', 'valor_cuota': 140000, 'interes_mes': 45800, 'cuota_mensual': 185800, 'saldo_capital': 4440000, 'fecha_pago': '2025-02-01'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-02-26', 'valor_cuota': 140000, 'interes_mes': 44400, 'cuota_mensual': 184400, 'saldo_capital': 4300000, 'fecha_pago': '2025-03-04'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-03-26', 'valor_cuota': 140000, 'interes_mes': 43000, 'cuota_mensual': 183000, 'saldo_capital': 4160000, 'fecha_pago': '2025-04-13'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-04-26', 'valor_cuota': 140000, 'interes_mes': 41600, 'cuota_mensual': 181600, 'saldo_capital': 4020000, 'fecha_pago': '2025-04-29'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-05-26', 'valor_cuota': 140000, 'interes_mes': 40200, 'cuota_mensual': 180200, 'saldo_capital': 3880000, 'fecha_pago': '2025-06-18'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-06-26', 'valor_cuota': 140000, 'interes_mes': 38800, 'cuota_mensual': 178800, 'saldo_capital': 3740000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-07-26', 'valor_cuota': 140000, 'interes_mes': 37400, 'cuota_mensual': 177400, 'saldo_capital': 3600000, 'fecha_pago': '2025-08-04'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2025-08-26', 'valor_cuota': 140000, 'interes_mes': 36000, 'cuota_mensual': 176000, 'saldo_capital': 3460000, 'fecha_pago': '2025-09-09'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-09-26', 'valor_cuota': 140000, 'interes_mes': 34600, 'cuota_mensual': 174600, 'saldo_capital': 3320000, 'fecha_pago': '2025-10-02'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-10-26', 'valor_cuota': 140000, 'interes_mes': 33200, 'cuota_mensual': 173200, 'saldo_capital': 3180000, 'fecha_pago': '2025-11-01'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-11-26', 'valor_cuota': 140000, 'interes_mes': 31800, 'cuota_mensual': 171800, 'saldo_capital': 3040000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-12-26', 'valor_cuota': 140000, 'interes_mes': 30400, 'cuota_mensual': 170400, 'saldo_capital': 2900000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-01-26', 'valor_cuota': 140000, 'interes_mes': 29000, 'cuota_mensual': 169000, 'saldo_capital': 2760000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-02-26', 'valor_cuota': 140000, 'interes_mes': 27600, 'cuota_mensual': 167600, 'saldo_capital': 2620000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-03-26', 'valor_cuota': 140000, 'interes_mes': 26200, 'cuota_mensual': 166200, 'saldo_capital': 2480000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-04-26', 'valor_cuota': 140000, 'interes_mes': 24800, 'cuota_mensual': 164800, 'saldo_capital': 2340000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-05-26', 'valor_cuota': 140000, 'interes_mes': 23400, 'cuota_mensual': 163400, 'saldo_capital': 2200000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-06-26', 'valor_cuota': 140000, 'interes_mes': 22000, 'cuota_mensual': 162000, 'saldo_capital': 2060000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-07-26', 'valor_cuota': 140000, 'interes_mes': 20600, 'cuota_mensual': 160600, 'saldo_capital': 1920000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2026-08-26', 'valor_cuota': 140000, 'interes_mes': 19200, 'cuota_mensual': 159200, 'saldo_capital': 1780000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-09-26', 'valor_cuota': 140000, 'interes_mes': 17800, 'cuota_mensual': 157800, 'saldo_capital': 1640000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2026-10-26', 'valor_cuota': 140000, 'interes_mes': 16400, 'cuota_mensual': 156400, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2026-11-26', 'valor_cuota': 140000, 'interes_mes': 15000, 'cuota_mensual': 155000, 'saldo_capital': 1360000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2026-12-26', 'valor_cuota': 140000, 'interes_mes': 13600, 'cuota_mensual': 153600, 'saldo_capital': 1220000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-01-26', 'valor_cuota': 140000, 'interes_mes': 12200, 'cuota_mensual': 152200, 'saldo_capital': 1080000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-02-26', 'valor_cuota': 140000, 'interes_mes': 10800, 'cuota_mensual': 150800, 'saldo_capital': 940000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-03-26', 'valor_cuota': 140000, 'interes_mes': 9400, 'cuota_mensual': 149400, 'saldo_capital': 800000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-04-26', 'valor_cuota': 140000, 'interes_mes': 8000, 'cuota_mensual': 148000, 'saldo_capital': 660000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-05-26', 'valor_cuota': 140000, 'interes_mes': 6600, 'cuota_mensual': 146600, 'saldo_capital': 520000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-06-26', 'valor_cuota': 140000, 'interes_mes': 5200, 'cuota_mensual': 145200, 'saldo_capital': 380000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-07-26', 'valor_cuota': 140000, 'interes_mes': 3800, 'cuota_mensual': 143800, 'saldo_capital': 240000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2027-08-26', 'valor_cuota': 140000, 'interes_mes': 2400, 'cuota_mensual': 142400, 'saldo_capital': 100000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2027-09-26', 'valor_cuota': 100000, 'interes_mes': 1000, 'cuota_mensual': 101000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 427,
            'capital': 2625000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 14,
            'fecha_inicio': '2025-04-30',
            'socios_ids': [11,13],  # WILSON PADILLA JOJOA / MABEL PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-05-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 2437500, 'fecha_pago': '2025-06-02'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-06-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 2250000, 'fecha_pago': '2025-07-09'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-07-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 2062500, 'fecha_pago': '2025-08-06'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-08-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 1875000, 'fecha_pago': '2025-09-09'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-09-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 1687500, 'fecha_pago': '2025-10-05'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-10-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 1500000, 'fecha_pago': '2025-11-10'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-11-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 1312500, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-12-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 1125000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-01-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 937500, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-02-28', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-03-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 562500, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-04-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 375000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-05-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 187500, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-06-30', 'valor_cuota': 187500, 'interes_mes': 14063, 'cuota_mensual': 201563, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 442,
            'capital': 24000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 48,
            'fecha_inicio': '2025-10-01',
            'socios_ids': [11],  # WILSON PADILLA JOJOA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-11-01', 'valor_cuota': 500000, 'interes_mes': 240000, 'cuota_mensual': 740000, 'saldo_capital': 23500000, 'fecha_pago': '2025-11-01'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-12-01', 'valor_cuota': 500000, 'interes_mes': 235000, 'cuota_mensual': 735000, 'saldo_capital': 23000000, 'fecha_pago': None},
                {'nro_cuota': 3, 'fecha_vencimiento': '2026-01-01', 'valor_cuota': 500000, 'interes_mes': 230000, 'cuota_mensual': 730000, 'saldo_capital': 22500000, 'fecha_pago': None},
                {'nro_cuota': 4, 'fecha_vencimiento': '2026-02-01', 'valor_cuota': 500000, 'interes_mes': 225000, 'cuota_mensual': 725000, 'saldo_capital': 22000000, 'fecha_pago': None},
                {'nro_cuota': 5, 'fecha_vencimiento': '2026-03-01', 'valor_cuota': 500000, 'interes_mes': 220000, 'cuota_mensual': 720000, 'saldo_capital': 21500000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-04-01', 'valor_cuota': 500000, 'interes_mes': 215000, 'cuota_mensual': 715000, 'saldo_capital': 21000000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-05-01', 'valor_cuota': 500000, 'interes_mes': 210000, 'cuota_mensual': 710000, 'saldo_capital': 20500000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-06-01', 'valor_cuota': 500000, 'interes_mes': 205000, 'cuota_mensual': 705000, 'saldo_capital': 20000000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-07-01', 'valor_cuota': 500000, 'interes_mes': 200000, 'cuota_mensual': 700000, 'saldo_capital': 19500000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-08-01', 'valor_cuota': 500000, 'interes_mes': 195000, 'cuota_mensual': 695000, 'saldo_capital': 19000000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-09-01', 'valor_cuota': 500000, 'interes_mes': 190000, 'cuota_mensual': 690000, 'saldo_capital': 18500000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-10-01', 'valor_cuota': 500000, 'interes_mes': 185000, 'cuota_mensual': 685000, 'saldo_capital': 18000000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-11-01', 'valor_cuota': 500000, 'interes_mes': 180000, 'cuota_mensual': 680000, 'saldo_capital': 17500000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-12-01', 'valor_cuota': 500000, 'interes_mes': 175000, 'cuota_mensual': 675000, 'saldo_capital': 17000000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2027-01-01', 'valor_cuota': 500000, 'interes_mes': 170000, 'cuota_mensual': 670000, 'saldo_capital': 16500000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2027-02-01', 'valor_cuota': 500000, 'interes_mes': 165000, 'cuota_mensual': 665000, 'saldo_capital': 16000000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2027-03-01', 'valor_cuota': 500000, 'interes_mes': 160000, 'cuota_mensual': 660000, 'saldo_capital': 15500000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-04-01', 'valor_cuota': 500000, 'interes_mes': 155000, 'cuota_mensual': 655000, 'saldo_capital': 15000000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-05-01', 'valor_cuota': 500000, 'interes_mes': 150000, 'cuota_mensual': 650000, 'saldo_capital': 14500000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-06-01', 'valor_cuota': 500000, 'interes_mes': 145000, 'cuota_mensual': 645000, 'saldo_capital': 14000000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-07-01', 'valor_cuota': 500000, 'interes_mes': 140000, 'cuota_mensual': 640000, 'saldo_capital': 13500000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-08-01', 'valor_cuota': 500000, 'interes_mes': 135000, 'cuota_mensual': 635000, 'saldo_capital': 13000000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-09-01', 'valor_cuota': 500000, 'interes_mes': 130000, 'cuota_mensual': 630000, 'saldo_capital': 12500000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-10-01', 'valor_cuota': 500000, 'interes_mes': 125000, 'cuota_mensual': 625000, 'saldo_capital': 12000000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-11-01', 'valor_cuota': 500000, 'interes_mes': 120000, 'cuota_mensual': 620000, 'saldo_capital': 11500000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-12-01', 'valor_cuota': 500000, 'interes_mes': 115000, 'cuota_mensual': 615000, 'saldo_capital': 11000000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2028-01-01', 'valor_cuota': 500000, 'interes_mes': 110000, 'cuota_mensual': 610000, 'saldo_capital': 10500000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2028-02-01', 'valor_cuota': 500000, 'interes_mes': 105000, 'cuota_mensual': 605000, 'saldo_capital': 10000000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2028-03-01', 'valor_cuota': 500000, 'interes_mes': 100000, 'cuota_mensual': 600000, 'saldo_capital': 9500000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2028-04-01', 'valor_cuota': 500000, 'interes_mes': 95000, 'cuota_mensual': 595000, 'saldo_capital': 9000000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2028-05-01', 'valor_cuota': 500000, 'interes_mes': 90000, 'cuota_mensual': 590000, 'saldo_capital': 8500000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2028-06-01', 'valor_cuota': 500000, 'interes_mes': 85000, 'cuota_mensual': 585000, 'saldo_capital': 8000000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2028-07-01', 'valor_cuota': 500000, 'interes_mes': 80000, 'cuota_mensual': 580000, 'saldo_capital': 7500000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2028-08-01', 'valor_cuota': 500000, 'interes_mes': 75000, 'cuota_mensual': 575000, 'saldo_capital': 7000000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-09-01', 'valor_cuota': 500000, 'interes_mes': 70000, 'cuota_mensual': 570000, 'saldo_capital': 6500000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-10-01', 'valor_cuota': 500000, 'interes_mes': 65000, 'cuota_mensual': 565000, 'saldo_capital': 6000000, 'fecha_pago': None},
                {'nro_cuota': 37, 'fecha_vencimiento': '2028-11-01', 'valor_cuota': 500000, 'interes_mes': 60000, 'cuota_mensual': 560000, 'saldo_capital': 5500000, 'fecha_pago': None},
                {'nro_cuota': 38, 'fecha_vencimiento': '2028-12-01', 'valor_cuota': 500000, 'interes_mes': 55000, 'cuota_mensual': 555000, 'saldo_capital': 5000000, 'fecha_pago': None},
                {'nro_cuota': 39, 'fecha_vencimiento': '2029-01-01', 'valor_cuota': 500000, 'interes_mes': 50000, 'cuota_mensual': 550000, 'saldo_capital': 4500000, 'fecha_pago': None},
                {'nro_cuota': 40, 'fecha_vencimiento': '2029-02-01', 'valor_cuota': 500000, 'interes_mes': 45000, 'cuota_mensual': 545000, 'saldo_capital': 4000000, 'fecha_pago': None},
                {'nro_cuota': 41, 'fecha_vencimiento': '2029-03-01', 'valor_cuota': 500000, 'interes_mes': 40000, 'cuota_mensual': 540000, 'saldo_capital': 3500000, 'fecha_pago': None},
                {'nro_cuota': 42, 'fecha_vencimiento': '2029-04-01', 'valor_cuota': 500000, 'interes_mes': 35000, 'cuota_mensual': 535000, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 43, 'fecha_vencimiento': '2029-05-01', 'valor_cuota': 500000, 'interes_mes': 30000, 'cuota_mensual': 530000, 'saldo_capital': 2500000, 'fecha_pago': None},
                {'nro_cuota': 44, 'fecha_vencimiento': '2029-06-01', 'valor_cuota': 500000, 'interes_mes': 25000, 'cuota_mensual': 525000, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 45, 'fecha_vencimiento': '2029-07-01', 'valor_cuota': 500000, 'interes_mes': 20000, 'cuota_mensual': 520000, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 46, 'fecha_vencimiento': '2029-08-01', 'valor_cuota': 500000, 'interes_mes': 15000, 'cuota_mensual': 515000, 'saldo_capital': 1000000, 'fecha_pago': None},
                {'nro_cuota': 47, 'fecha_vencimiento': '2029-09-01', 'valor_cuota': 500000, 'interes_mes': 10000, 'cuota_mensual': 510000, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 48, 'fecha_vencimiento': '2029-10-01', 'valor_cuota': 500000, 'interes_mes': 5000, 'cuota_mensual': 505000, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 373,
            'capital': 10000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2024-01-27',
            'socios_ids': [10],  # TEREZA PADILLA JOJOA Y/O DANNY ARCINIEGAS PADILLA
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2024-02-27', 'valor_cuota': 420000, 'interes_mes': 100000, 'cuota_mensual': 520000, 'saldo_capital': 9580000, 'fecha_pago': '2024-02-24'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2024-03-27', 'valor_cuota': 420000, 'interes_mes': 95800, 'cuota_mensual': 515800, 'saldo_capital': 9160000, 'fecha_pago': '2024-03-30'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2024-04-27', 'valor_cuota': 420000, 'interes_mes': 91600, 'cuota_mensual': 511600, 'saldo_capital': 8740000, 'fecha_pago': '2024-03-30'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2024-05-27', 'valor_cuota': 420000, 'interes_mes': 87400, 'cuota_mensual': 507400, 'saldo_capital': 8320000, 'fecha_pago': '2024-06-09'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2024-06-27', 'valor_cuota': 420000, 'interes_mes': 83200, 'cuota_mensual': 503200, 'saldo_capital': 7900000, 'fecha_pago': '2024-07-07'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2024-07-27', 'valor_cuota': 420000, 'interes_mes': 79000, 'cuota_mensual': 499000, 'saldo_capital': 7480000, 'fecha_pago': '2024-10-13'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2024-08-27', 'valor_cuota': 420000, 'interes_mes': 74800, 'cuota_mensual': 494800, 'saldo_capital': 7060000, 'fecha_pago': '2024-10-13'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2024-09-27', 'valor_cuota': 420000, 'interes_mes': 70600, 'cuota_mensual': 490600, 'saldo_capital': 6640000, 'fecha_pago': '2024-10-13'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2024-10-27', 'valor_cuota': 420000, 'interes_mes': 66400, 'cuota_mensual': 486400, 'saldo_capital': 6220000, 'fecha_pago': '2025-01-08'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2024-11-27', 'valor_cuota': 420000, 'interes_mes': 62200, 'cuota_mensual': 482200, 'saldo_capital': 5800000, 'fecha_pago': '2025-01-08'},
                {'nro_cuota': 11, 'fecha_vencimiento': '2024-12-27', 'valor_cuota': 420000, 'interes_mes': 58000, 'cuota_mensual': 478000, 'saldo_capital': 5380000, 'fecha_pago': '2025-03-07'},
                {'nro_cuota': 12, 'fecha_vencimiento': '2025-01-27', 'valor_cuota': 420000, 'interes_mes': 53800, 'cuota_mensual': 473800, 'saldo_capital': 4960000, 'fecha_pago': '2025-03-07'},
                {'nro_cuota': 13, 'fecha_vencimiento': '2025-02-27', 'valor_cuota': 420000, 'interes_mes': 49600, 'cuota_mensual': 469600, 'saldo_capital': 4540000, 'fecha_pago': '2025-03-07'},
                {'nro_cuota': 14, 'fecha_vencimiento': '2025-03-27', 'valor_cuota': 420000, 'interes_mes': 45400, 'cuota_mensual': 465400, 'saldo_capital': 4120000, 'fecha_pago': '2025-04-29'},
                {'nro_cuota': 15, 'fecha_vencimiento': '2025-04-27', 'valor_cuota': 420000, 'interes_mes': 41200, 'cuota_mensual': 461200, 'saldo_capital': 3700000, 'fecha_pago': '2025-04-29'},
                {'nro_cuota': 16, 'fecha_vencimiento': '2025-05-27', 'valor_cuota': 420000, 'interes_mes': 37000, 'cuota_mensual': 457000, 'saldo_capital': 3280000, 'fecha_pago': '2025-07-18'},
                {'nro_cuota': 17, 'fecha_vencimiento': '2025-06-27', 'valor_cuota': 420000, 'interes_mes': 32800, 'cuota_mensual': 452800, 'saldo_capital': 2860000, 'fecha_pago': '2025-07-18'},
                {'nro_cuota': 18, 'fecha_vencimiento': '2025-07-27', 'valor_cuota': 420000, 'interes_mes': 28600, 'cuota_mensual': 448600, 'saldo_capital': 2440000, 'fecha_pago': '2025-10-29'},
                {'nro_cuota': 19, 'fecha_vencimiento': '2025-08-27', 'valor_cuota': 420000, 'interes_mes': 24400, 'cuota_mensual': 444400, 'saldo_capital': 2020000, 'fecha_pago': '2025-11-09'},
                {'nro_cuota': 20, 'fecha_vencimiento': '2025-09-27', 'valor_cuota': 420000, 'interes_mes': 20200, 'cuota_mensual': 440200, 'saldo_capital': 1600000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2025-10-27', 'valor_cuota': 420000, 'interes_mes': 16000, 'cuota_mensual': 436000, 'saldo_capital': 1180000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2025-11-27', 'valor_cuota': 420000, 'interes_mes': 11800, 'cuota_mensual': 431800, 'saldo_capital': 760000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2025-12-27', 'valor_cuota': 420000, 'interes_mes': 7600, 'cuota_mensual': 427600, 'saldo_capital': 340000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2026-01-27', 'valor_cuota': 340000, 'interes_mes': 3400, 'cuota_mensual': 343400, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },


        {
            'letra': 438,
            'capital': 6000000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 24,
            'fecha_inicio': '2025-07-14',
            'socios_ids': [23],  # ANA NEREYDA BURBANO G. Y/O MANUELA CASTRO BURBANO
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-08-14', 'valor_cuota': 250000, 'interes_mes': 60000, 'cuota_mensual': 310000, 'saldo_capital': 5750000, 'fecha_pago': '2025-08-14'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-09-14', 'valor_cuota': 250000, 'interes_mes': 57500, 'cuota_mensual': 307500, 'saldo_capital': 5500000, 'fecha_pago': '2025-09-07'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-10-14', 'valor_cuota': 250000, 'interes_mes': 55000, 'cuota_mensual': 305000, 'saldo_capital': 5250000, 'fecha_pago': '2025-10-25'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-11-14', 'valor_cuota': 250000, 'interes_mes': 52500, 'cuota_mensual': 302500, 'saldo_capital': 5000000, 'fecha_pago': '2025-11-13'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-12-14', 'valor_cuota': 250000, 'interes_mes': 50000, 'cuota_mensual': 300000, 'saldo_capital': 4750000, 'fecha_pago': None},
                {'nro_cuota': 6, 'fecha_vencimiento': '2026-01-14', 'valor_cuota': 250000, 'interes_mes': 47500, 'cuota_mensual': 297500, 'saldo_capital': 4500000, 'fecha_pago': None},
                {'nro_cuota': 7, 'fecha_vencimiento': '2026-02-14', 'valor_cuota': 250000, 'interes_mes': 45000, 'cuota_mensual': 295000, 'saldo_capital': 4250000, 'fecha_pago': None},
                {'nro_cuota': 8, 'fecha_vencimiento': '2026-03-14', 'valor_cuota': 250000, 'interes_mes': 42500, 'cuota_mensual': 292500, 'saldo_capital': 4000000, 'fecha_pago': None},
                {'nro_cuota': 9, 'fecha_vencimiento': '2026-04-14', 'valor_cuota': 250000, 'interes_mes': 40000, 'cuota_mensual': 290000, 'saldo_capital': 3750000, 'fecha_pago': None},
                {'nro_cuota': 10, 'fecha_vencimiento': '2026-05-14', 'valor_cuota': 250000, 'interes_mes': 37500, 'cuota_mensual': 287500, 'saldo_capital': 3500000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-06-14', 'valor_cuota': 250000, 'interes_mes': 35000, 'cuota_mensual': 285000, 'saldo_capital': 3250000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-07-14', 'valor_cuota': 250000, 'interes_mes': 32500, 'cuota_mensual': 282500, 'saldo_capital': 3000000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-08-14', 'valor_cuota': 250000, 'interes_mes': 30000, 'cuota_mensual': 280000, 'saldo_capital': 2750000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-09-14', 'valor_cuota': 250000, 'interes_mes': 27500, 'cuota_mensual': 277500, 'saldo_capital': 2500000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-10-14', 'valor_cuota': 250000, 'interes_mes': 25000, 'cuota_mensual': 275000, 'saldo_capital': 2250000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-11-14', 'valor_cuota': 250000, 'interes_mes': 22500, 'cuota_mensual': 272500, 'saldo_capital': 2000000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-12-14', 'valor_cuota': 250000, 'interes_mes': 20000, 'cuota_mensual': 270000, 'saldo_capital': 1750000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2027-01-14', 'valor_cuota': 250000, 'interes_mes': 17500, 'cuota_mensual': 267500, 'saldo_capital': 1500000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2027-02-14', 'valor_cuota': 250000, 'interes_mes': 15000, 'cuota_mensual': 265000, 'saldo_capital': 1250000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2027-03-14', 'valor_cuota': 250000, 'interes_mes': 12500, 'cuota_mensual': 262500, 'saldo_capital': 1000000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2027-04-14', 'valor_cuota': 250000, 'interes_mes': 10000, 'cuota_mensual': 260000, 'saldo_capital': 750000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2027-05-14', 'valor_cuota': 250000, 'interes_mes': 7500, 'cuota_mensual': 257500, 'saldo_capital': 500000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-06-14', 'valor_cuota': 250000, 'interes_mes': 5000, 'cuota_mensual': 255000, 'saldo_capital': 250000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-07-14', 'valor_cuota': 250000, 'interes_mes': 2500, 'cuota_mensual': 252500, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        },

        {
            'letra': 418,
            'capital': 28767000,
            'interes': 0.01,  # 1.00% mensual
            'no_cuotas': 60,
            'fecha_inicio': '2025-02-10',
            'socios_ids': [40],  # XIOMARA GARCIA LUNA Y/O JHOAN NARVAEZ
            'cuotas': [
                {'nro_cuota': 1, 'fecha_vencimiento': '2025-03-10', 'valor_cuota': 480000, 'interes_mes': 287670, 'cuota_mensual': 767670, 'saldo_capital': 28287000, 'fecha_pago': '2025-03-03'},
                {'nro_cuota': 2, 'fecha_vencimiento': '2025-04-10', 'valor_cuota': 480000, 'interes_mes': 282870, 'cuota_mensual': 762870, 'saldo_capital': 27807000, 'fecha_pago': '2025-04-07'},
                {'nro_cuota': 3, 'fecha_vencimiento': '2025-05-10', 'valor_cuota': 480000, 'interes_mes': 278070, 'cuota_mensual': 758070, 'saldo_capital': 27327000, 'fecha_pago': '2025-05-09'},
                {'nro_cuota': 4, 'fecha_vencimiento': '2025-06-10', 'valor_cuota': 480000, 'interes_mes': 273270, 'cuota_mensual': 753270, 'saldo_capital': 26847000, 'fecha_pago': '2025-06-04'},
                {'nro_cuota': 5, 'fecha_vencimiento': '2025-07-10', 'valor_cuota': 480000, 'interes_mes': 268470, 'cuota_mensual': 748470, 'saldo_capital': 26367000, 'fecha_pago': '2025-07-10'},
                {'nro_cuota': 6, 'fecha_vencimiento': '2025-08-10', 'valor_cuota': 480000, 'interes_mes': 263670, 'cuota_mensual': 743670, 'saldo_capital': 25887000, 'fecha_pago': '2025-08-08'},
                {'nro_cuota': 7, 'fecha_vencimiento': '2025-09-10', 'valor_cuota': 480000, 'interes_mes': 258870, 'cuota_mensual': 738870, 'saldo_capital': 25407000, 'fecha_pago': '2025-09-18'},
                {'nro_cuota': 8, 'fecha_vencimiento': '2025-10-10', 'valor_cuota': 480000, 'interes_mes': 254070, 'cuota_mensual': 734070, 'saldo_capital': 24927000, 'fecha_pago': '2025-10-08'},
                {'nro_cuota': 9, 'fecha_vencimiento': '2025-11-10', 'valor_cuota': 480000, 'interes_mes': 249270, 'cuota_mensual': 729270, 'saldo_capital': 24447000, 'fecha_pago': '2025-11-10'},
                {'nro_cuota': 10, 'fecha_vencimiento': '2025-12-10', 'valor_cuota': 480000, 'interes_mes': 244470, 'cuota_mensual': 724470, 'saldo_capital': 23967000, 'fecha_pago': None},
                {'nro_cuota': 11, 'fecha_vencimiento': '2026-01-10', 'valor_cuota': 480000, 'interes_mes': 239670, 'cuota_mensual': 719670, 'saldo_capital': 23487000, 'fecha_pago': None},
                {'nro_cuota': 12, 'fecha_vencimiento': '2026-02-10', 'valor_cuota': 480000, 'interes_mes': 234870, 'cuota_mensual': 714870, 'saldo_capital': 23007000, 'fecha_pago': None},
                {'nro_cuota': 13, 'fecha_vencimiento': '2026-03-10', 'valor_cuota': 480000, 'interes_mes': 230070, 'cuota_mensual': 710070, 'saldo_capital': 22527000, 'fecha_pago': None},
                {'nro_cuota': 14, 'fecha_vencimiento': '2026-04-10', 'valor_cuota': 480000, 'interes_mes': 225270, 'cuota_mensual': 705270, 'saldo_capital': 22047000, 'fecha_pago': None},
                {'nro_cuota': 15, 'fecha_vencimiento': '2026-05-10', 'valor_cuota': 480000, 'interes_mes': 220470, 'cuota_mensual': 700470, 'saldo_capital': 21567000, 'fecha_pago': None},
                {'nro_cuota': 16, 'fecha_vencimiento': '2026-06-10', 'valor_cuota': 480000, 'interes_mes': 215670, 'cuota_mensual': 695670, 'saldo_capital': 21087000, 'fecha_pago': None},
                {'nro_cuota': 17, 'fecha_vencimiento': '2026-07-10', 'valor_cuota': 480000, 'interes_mes': 210870, 'cuota_mensual': 690870, 'saldo_capital': 20607000, 'fecha_pago': None},
                {'nro_cuota': 18, 'fecha_vencimiento': '2026-08-10', 'valor_cuota': 480000, 'interes_mes': 206070, 'cuota_mensual': 686070, 'saldo_capital': 20127000, 'fecha_pago': None},
                {'nro_cuota': 19, 'fecha_vencimiento': '2026-09-10', 'valor_cuota': 480000, 'interes_mes': 201270, 'cuota_mensual': 681270, 'saldo_capital': 19647000, 'fecha_pago': None},
                {'nro_cuota': 20, 'fecha_vencimiento': '2026-10-10', 'valor_cuota': 480000, 'interes_mes': 196470, 'cuota_mensual': 676470, 'saldo_capital': 19167000, 'fecha_pago': None},
                {'nro_cuota': 21, 'fecha_vencimiento': '2026-11-10', 'valor_cuota': 480000, 'interes_mes': 191670, 'cuota_mensual': 671670, 'saldo_capital': 18687000, 'fecha_pago': None},
                {'nro_cuota': 22, 'fecha_vencimiento': '2026-12-10', 'valor_cuota': 480000, 'interes_mes': 186870, 'cuota_mensual': 666870, 'saldo_capital': 18207000, 'fecha_pago': None},
                {'nro_cuota': 23, 'fecha_vencimiento': '2027-01-10', 'valor_cuota': 480000, 'interes_mes': 182070, 'cuota_mensual': 662070, 'saldo_capital': 17727000, 'fecha_pago': None},
                {'nro_cuota': 24, 'fecha_vencimiento': '2027-02-10', 'valor_cuota': 480000, 'interes_mes': 177270, 'cuota_mensual': 657270, 'saldo_capital': 17247000, 'fecha_pago': None},
                {'nro_cuota': 25, 'fecha_vencimiento': '2027-03-10', 'valor_cuota': 480000, 'interes_mes': 172470, 'cuota_mensual': 652470, 'saldo_capital': 16767000, 'fecha_pago': None},
                {'nro_cuota': 26, 'fecha_vencimiento': '2027-04-10', 'valor_cuota': 480000, 'interes_mes': 167670, 'cuota_mensual': 647670, 'saldo_capital': 16287000, 'fecha_pago': None},
                {'nro_cuota': 27, 'fecha_vencimiento': '2027-05-10', 'valor_cuota': 480000, 'interes_mes': 162870, 'cuota_mensual': 642870, 'saldo_capital': 15807000, 'fecha_pago': None},
                {'nro_cuota': 28, 'fecha_vencimiento': '2027-06-10', 'valor_cuota': 480000, 'interes_mes': 158070, 'cuota_mensual': 638070, 'saldo_capital': 15327000, 'fecha_pago': None},
                {'nro_cuota': 29, 'fecha_vencimiento': '2027-07-10', 'valor_cuota': 480000, 'interes_mes': 153270, 'cuota_mensual': 633270, 'saldo_capital': 14847000, 'fecha_pago': None},
                {'nro_cuota': 30, 'fecha_vencimiento': '2027-08-10', 'valor_cuota': 480000, 'interes_mes': 148470, 'cuota_mensual': 628470, 'saldo_capital': 14367000, 'fecha_pago': None},
                {'nro_cuota': 31, 'fecha_vencimiento': '2027-09-10', 'valor_cuota': 480000, 'interes_mes': 143670, 'cuota_mensual': 623670, 'saldo_capital': 13887000, 'fecha_pago': None},
                {'nro_cuota': 32, 'fecha_vencimiento': '2027-10-10', 'valor_cuota': 480000, 'interes_mes': 138870, 'cuota_mensual': 618870, 'saldo_capital': 13407000, 'fecha_pago': None},
                {'nro_cuota': 33, 'fecha_vencimiento': '2027-11-10', 'valor_cuota': 480000, 'interes_mes': 134070, 'cuota_mensual': 614070, 'saldo_capital': 12927000, 'fecha_pago': None},
                {'nro_cuota': 34, 'fecha_vencimiento': '2027-12-10', 'valor_cuota': 480000, 'interes_mes': 129270, 'cuota_mensual': 609270, 'saldo_capital': 12447000, 'fecha_pago': None},
                {'nro_cuota': 35, 'fecha_vencimiento': '2028-01-10', 'valor_cuota': 480000, 'interes_mes': 124470, 'cuota_mensual': 604470, 'saldo_capital': 11967000, 'fecha_pago': None},
                {'nro_cuota': 36, 'fecha_vencimiento': '2028-02-10', 'valor_cuota': 480000, 'interes_mes': 119670, 'cuota_mensual': 599670, 'saldo_capital': 11487000, 'fecha_pago': None},
                {'nro_cuota': 37, 'fecha_vencimiento': '2028-03-10', 'valor_cuota': 480000, 'interes_mes': 114870, 'cuota_mensual': 594870, 'saldo_capital': 11007000, 'fecha_pago': None},
                {'nro_cuota': 38, 'fecha_vencimiento': '2028-04-10', 'valor_cuota': 480000, 'interes_mes': 110070, 'cuota_mensual': 590070, 'saldo_capital': 10527000, 'fecha_pago': None},
                {'nro_cuota': 39, 'fecha_vencimiento': '2028-05-10', 'valor_cuota': 480000, 'interes_mes': 105270, 'cuota_mensual': 585270, 'saldo_capital': 10047000, 'fecha_pago': None},
                {'nro_cuota': 40, 'fecha_vencimiento': '2028-06-10', 'valor_cuota': 480000, 'interes_mes': 100470, 'cuota_mensual': 580470, 'saldo_capital': 9567000, 'fecha_pago': None},
                {'nro_cuota': 41, 'fecha_vencimiento': '2028-07-10', 'valor_cuota': 480000, 'interes_mes': 95670, 'cuota_mensual': 575670, 'saldo_capital': 9087000, 'fecha_pago': None},
                {'nro_cuota': 42, 'fecha_vencimiento': '2028-08-10', 'valor_cuota': 480000, 'interes_mes': 90870, 'cuota_mensual': 570870, 'saldo_capital': 8607000, 'fecha_pago': None},
                {'nro_cuota': 43, 'fecha_vencimiento': '2028-09-10', 'valor_cuota': 480000, 'interes_mes': 86070, 'cuota_mensual': 566070, 'saldo_capital': 8127000, 'fecha_pago': None},
                {'nro_cuota': 44, 'fecha_vencimiento': '2028-10-10', 'valor_cuota': 480000, 'interes_mes': 81270, 'cuota_mensual': 561270, 'saldo_capital': 7647000, 'fecha_pago': None},
                {'nro_cuota': 45, 'fecha_vencimiento': '2028-11-10', 'valor_cuota': 480000, 'interes_mes': 76470, 'cuota_mensual': 556470, 'saldo_capital': 7167000, 'fecha_pago': None},
                {'nro_cuota': 46, 'fecha_vencimiento': '2028-12-10', 'valor_cuota': 480000, 'interes_mes': 71670, 'cuota_mensual': 551670, 'saldo_capital': 6687000, 'fecha_pago': None},
                {'nro_cuota': 47, 'fecha_vencimiento': '2029-01-10', 'valor_cuota': 480000, 'interes_mes': 66870, 'cuota_mensual': 546870, 'saldo_capital': 6207000, 'fecha_pago': None},
                {'nro_cuota': 48, 'fecha_vencimiento': '2029-02-10', 'valor_cuota': 480000, 'interes_mes': 62070, 'cuota_mensual': 542070, 'saldo_capital': 5727000, 'fecha_pago': None},
                {'nro_cuota': 49, 'fecha_vencimiento': '2029-03-10', 'valor_cuota': 480000, 'interes_mes': 57270, 'cuota_mensual': 537270, 'saldo_capital': 5247000, 'fecha_pago': None},
                {'nro_cuota': 50, 'fecha_vencimiento': '2029-04-10', 'valor_cuota': 480000, 'interes_mes': 52470, 'cuota_mensual': 532470, 'saldo_capital': 4767000, 'fecha_pago': None},
                {'nro_cuota': 51, 'fecha_vencimiento': '2029-05-10', 'valor_cuota': 480000, 'interes_mes': 47670, 'cuota_mensual': 527670, 'saldo_capital': 4287000, 'fecha_pago': None},
                {'nro_cuota': 52, 'fecha_vencimiento': '2029-06-10', 'valor_cuota': 480000, 'interes_mes': 42870, 'cuota_mensual': 522870, 'saldo_capital': 3807000, 'fecha_pago': None},
                {'nro_cuota': 53, 'fecha_vencimiento': '2029-07-10', 'valor_cuota': 480000, 'interes_mes': 38070, 'cuota_mensual': 518070, 'saldo_capital': 3327000, 'fecha_pago': None},
                {'nro_cuota': 54, 'fecha_vencimiento': '2029-08-10', 'valor_cuota': 480000, 'interes_mes': 33270, 'cuota_mensual': 513270, 'saldo_capital': 2847000, 'fecha_pago': None},
                {'nro_cuota': 55, 'fecha_vencimiento': '2029-09-10', 'valor_cuota': 480000, 'interes_mes': 28470, 'cuota_mensual': 508470, 'saldo_capital': 2367000, 'fecha_pago': None},
                {'nro_cuota': 56, 'fecha_vencimiento': '2029-10-10', 'valor_cuota': 480000, 'interes_mes': 23670, 'cuota_mensual': 503670, 'saldo_capital': 1887000, 'fecha_pago': None},
                {'nro_cuota': 57, 'fecha_vencimiento': '2029-11-10', 'valor_cuota': 480000, 'interes_mes': 18870, 'cuota_mensual': 498870, 'saldo_capital': 1407000, 'fecha_pago': None},
                {'nro_cuota': 58, 'fecha_vencimiento': '2029-12-10', 'valor_cuota': 480000, 'interes_mes': 14070, 'cuota_mensual': 494070, 'saldo_capital': 927000, 'fecha_pago': None},
                {'nro_cuota': 59, 'fecha_vencimiento': '2030-01-10', 'valor_cuota': 480000, 'interes_mes': 9270, 'cuota_mensual': 489270, 'saldo_capital': 447000, 'fecha_pago': None},
                {'nro_cuota': 60, 'fecha_vencimiento': '2030-02-10', 'valor_cuota': 447000, 'interes_mes': 4470, 'cuota_mensual': 451470, 'saldo_capital': 0, 'fecha_pago': None}
            ]
        }
        
    ]

    db_manager.add_multiple_historical_credits(credits_list)
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
