import os
from openpyxl import load_workbook
from openpyxl.styles import Alignment 
from datetime import date
from config import format_miles_colombian_int, format_full_name_for_excel, BASE_APP_DIR

# --- Configuración de rutas (Ajusta según tu estructura de proyecto) ---
TEMPLATE_APORTE_REL_PATH = os.path.join("assets", "templates", "recibo_template_aporte.xlsx") 
TEMPLATE_APORTE_PATH = os.path.join(BASE_APP_DIR, TEMPLATE_APORTE_REL_PATH) 

# Renombrado y ajustado para tu estructura deseada
OUTPUT_FOLDER_REL_PATH = "Recibos"
OUTPUT_FOLDER_PATH = os.path.join(BASE_APP_DIR, OUTPUT_FOLDER_REL_PATH) 

# --- Constantes de Celda para recibo_template_aporte.xlsx ---
RECIBO_ID_CELL = 'D4'
FECHA_CELL = 'I4'
RECIBI_DE_CELL = 'G6' # Celda para "Recibí de"

# Aportes - Rango de 10 filas (de Fila 9 a Fila 18)
APORTE_DATA_START_ROW = 9 
APORTE_DATA_END_ROW = 18 # Fila final para datos de aportes
MAX_APORTES_ROWS_IN_TEMPLATE = 10 # 18 - 9 + 1 = 10 filas disponibles

APORTE_NOMBRE_COL = 'B'
APORTE_SALDO_COL = 'F'
APORTE_MONTO_COL = 'H'
APORTE_NUEVO_SALDO_COL = 'J'

APORTE_TOTAL_CELL = 'H19' # Celda para el Total de Aportes

# Totales Finales
GASTOS_ADMIN_CELL = 'K21' # Celda para Gastos de Administración
TOTAL_GENERAL_CELL = 'K22' # Celda para el Total a Pagar

GASTO_POR_APORTE = 3000 # Nueva constante para el valor de cada aporte

def generar_recibo_solo_aportes(
    db_manager, 
    recibo_id: int,
    recibi_de_data: dict, # Ahora se procesará para mayúsculas y alineación
    aportes_info: list = None
):
    """
    Genera un recibo de solo aportes utilizando la plantilla recibo_template_aporte.xlsx.
    Rellena hasta 10 filas de aportes y los totales.
    Ajusta el formato de los nombres de los socios y del "Recibí de".
    
    El gasto administrativo se calcula como GASTO_POR_APORTE * número de aportes.
    """
    if aportes_info is None:
        aportes_info = []

    try:
        os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
        file_name = f"Recibo_{recibo_id}_{date.today().strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER_PATH, file_name)

        wb = load_workbook(TEMPLATE_APORTE_PATH)
        ws = wb.active

        # --- Reemplazar datos de CABECERA ---
        ws[RECIBO_ID_CELL] = recibo_id
        ws[FECHA_CELL] = date.today().strftime("%d/%m/%Y")
        
        # AJUSTE 1: Nombre "Recibí de" en MAYÚSCULAS y alineado al centro
        recibi_de_full_name = f"{recibi_de_data['nombres']} {recibi_de_data['apellidos']}".upper()
        ws[RECIBI_DE_CELL] = recibi_de_full_name
        ws[RECIBI_DE_CELL].alignment = Alignment(horizontal='center') # Alineación al centro

        # --- PROCESAR APORTES ---
        total_aportes_acumulado = 0
        num_aportes_actual = len(aportes_info)
        
        for i in range(MAX_APORTES_ROWS_IN_TEMPLATE):
            row_to_fill = APORTE_DATA_START_ROW + i
            
            if i < num_aportes_actual:
                socio_data, monto_aporte, saldo_socio_antes, saldo_socio_despues = aportes_info[i]
                
                # AJUSTE 2: Formatear el nombre del socio para los detalles del aporte
                formatted_socio_name = format_full_name_for_excel(
                    socio_data['nombres'], 
                    socio_data['apellidos'], 
                    max_length=24 # Basado en tu indicación
                )
                ws[f'{APORTE_NOMBRE_COL}{row_to_fill}'] = formatted_socio_name
                ws[f'{APORTE_SALDO_COL}{row_to_fill}'] = format_miles_colombian_int(saldo_socio_antes)
                ws[f'{APORTE_MONTO_COL}{row_to_fill}'] = format_miles_colombian_int(monto_aporte)
                ws[f'{APORTE_NUEVO_SALDO_COL}{row_to_fill}'] = format_miles_colombian_int(saldo_socio_despues)
                total_aportes_acumulado += monto_aporte
            else:
                # Limpiar las filas no utilizadas
                ws[f'{APORTE_NOMBRE_COL}{row_to_fill}'] = "" 
                ws[f'{APORTE_SALDO_COL}{row_to_fill}'] = "" 
                ws[f'{APORTE_MONTO_COL}{row_to_fill}'] = "" 
                ws[f'{APORTE_NUEVO_SALDO_COL}{row_to_fill}'] = "" 

        # Escribir el total de aportes
        ws[APORTE_TOTAL_CELL] = format_miles_colombian_int(total_aportes_acumulado)

        # --- GASTOS ADMINISTRACIÓN y TOTAL GENERAL ---
        # *** ESTE ES EL CAMBIO CLAVE ***
        gastos_admin = GASTO_POR_APORTE * num_aportes_actual
        ws[GASTOS_ADMIN_CELL] = format_miles_colombian_int(gastos_admin)
        
        total_general = total_aportes_acumulado + gastos_admin
        ws[TOTAL_GENERAL_CELL] = format_miles_colombian_int(total_general)

        # --- Guardar el recibo ---
        wb.save(output_path)
        return output_path

    except Exception as e:
        print(f"Error al generar recibo solo de aportes: {e}")
        import traceback
        traceback.print_exc() 
        return None