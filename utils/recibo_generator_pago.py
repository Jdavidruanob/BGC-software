# utils/recibo_generator_pago.py

import os
from openpyxl import load_workbook
from openpyxl.styles import Alignment 
from datetime import date
from config import format_miles_colombian_int, format_full_name_for_excel

# --- Configuración de rutas (Ajusta según tu estructura de proyecto) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

TEMPLATE_PAGO_REL_PATH = os.path.join("assets", "templates", "recibo_template_pago.xlsx") 
TEMPLATE_PAGO_PATH = os.path.join(BASE_DIR, TEMPLATE_PAGO_REL_PATH)

OUTPUT_FOLDER_REL_PATH = "recibos_generados"
OUTPUT_FOLDER_PATH = os.path.join(BASE_DIR, OUTPUT_FOLDER_REL_PATH)

# --- Constantes de Celda Comunes (pueden ser las mismas que en el de aportes si la plantilla lo permite) ---
RECIBO_ID_CELL = 'D4'
FECHA_CELL = 'I4'
RECIBI_DE_CELL = 'G6' # Celda para "Recibí de"

# --- Constantes de Celda Específicas para recibo_template_pago.xlsx ---
CREDITO_DATA_START_ROW = 9
CREDITO_DATA_END_ROW = 19 # Fila final para datos de créditos (9 a 19 son 11 filas)
MAX_CREDITO_ROWS_IN_TEMPLATE = 11 

CREDITO_NOMBRE_COL = 'B'
CREDITO_LETRA_COL = 'F'
CREDITO_CUOTA_COL = 'G' 
CREDITO_SDO_CAP_COL = 'H' 
CREDITO_AB_CAP_COL = 'I' 
CREDITO_INTERES_COL = 'J' 
CREDITO_N_SDOCAP_COL = 'K' 

CREDITO_TOTAL_CELL = 'H20' 

# *VERIFICA ESTAS CELDAS EN TU TEMPLATE REAL `recibo_template_pago.xlsx`*
GASTOS_ADMIN_CELL_PAGO = 'K22' 
TOTAL_GENERAL_CELL_PAGO = 'K23' 

DEFAULT_GASTOS_ADMIN = 3000 
# --- Función de Generación de Recibo de Pagos ---

def generar_recibo_solo_pagos(
    db_manager, 
    recibo_id: int,
    recibi_de_data: dict, 
    pagos_credito_info: list = None, # Ahora esta lista contiene entradas CONSOLIDADAS
    gastos_admin: int = DEFAULT_GASTOS_ADMIN 
):
    """
    Genera un recibo de solo pagos de crédito utilizando la plantilla recibo_template_pago.xlsx.
    Rellena hasta 11 filas de pagos consolidados, calcula los totales y formatea nombres.
    
    pagos_credito_info: List[Dict] donde cada dict contiene detalles CONSOLIDADOS:
    {
      'socio_data': {...},                 # Diccionario completo del socio
      'letra_id': 'ABC-123',               # ID de la letra
      'nro_cuotas_pagadas_start': 1,       # Número de la primera cuota pagada
      'nro_cuotas_pagadas_end': 3,         # Número de la última cuota pagada
      'valor_capital_consolidado': 30000,  # Suma de los capitales de las cuotas
      'interes_consolidado': 1500,         # Suma de los intereses de las cuotas
      'saldo_capital_antes_pago': 50000,   # Saldo antes del primer pago en este grupo
      'saldo_capital_despues_pago': 40000  # Saldo después del último pago en este grupo
    }
    """
    if pagos_credito_info is None:
        pagos_credito_info = []

    try:
        os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
        file_name = f"Recibo_Pago_{recibo_id}_{date.today().strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER_PATH, file_name)

        wb = load_workbook(TEMPLATE_PAGO_PATH) 
        ws = wb.active

        # --- Reemplazar datos de CABECERA ---
        ws[RECIBO_ID_CELL] = recibo_id
        ws[FECHA_CELL] = date.today().strftime("%d/%m/%Y")
        
        recibi_de_full_name = f"{recibi_de_data['nombres']} {recibi_de_data['apellidos']}".upper()
        ws[RECIBI_DE_CELL] = recibi_de_full_name
        ws[RECIBI_DE_CELL].alignment = Alignment(horizontal='center') 

        # --- PROCESAR PAGOS DE CRÉDITO CONSOLIDADOS ---
        total_acumulado_capital_interes = 0
        num_credit_details_consolidated = len(pagos_credito_info)

        # Si el número de detalles excede el máximo, truncar para evitar errores en la plantilla.
        if num_credit_details_consolidated > MAX_CREDITO_ROWS_IN_TEMPLATE:
            print(f"ADVERTENCIA: Se intentaron procesar {num_credit_details_consolidated} entradas consolidadas, "
                  f"pero la plantilla solo soporta {MAX_CREDITO_ROWS_IN_TEMPLATE}. Se truncará.")
            pagos_credito_info = pagos_credito_info[:MAX_CREDITO_ROWS_IN_TEMPLATE]
            num_credit_details_consolidated = len(pagos_credito_info)
        
        # Cache para almacenar el número total de cuotas por letra
        cuotas_info_cache = {}

        # Iterar sobre los detalles consolidados para llenar las filas
        for i in range(MAX_CREDITO_ROWS_IN_TEMPLATE):
            row_to_fill = CREDITO_DATA_START_ROW + i
            
            if i < num_credit_details_consolidated:
                detalle_consolidado = pagos_credito_info[i]
                
                socio_data = detalle_consolidado['socio_data'] 
                letra_id = detalle_consolidado['letra_id']
                nro_cuotas_start = detalle_consolidado['nro_cuotas_pagadas_start']
                nro_cuotas_end = detalle_consolidado['nro_cuotas_pagadas_end']

                formatted_socio_name = format_full_name_for_excel(
                    socio_data['nombres'], 
                    socio_data['apellidos'], 
                    max_length=24
                )
                ws[f'{CREDITO_NOMBRE_COL}{row_to_fill}'] = formatted_socio_name
                ws[f'{CREDITO_LETRA_COL}{row_to_fill}'] = letra_id

                # Formato de la columna 'cuota' (ej: "1-3/36" o "1/36" si es una sola)
                if letra_id not in cuotas_info_cache:
                    total_cuotas_credito = db_manager.get_total_cuotas_credito(letra_id)
                    cuotas_info_cache[letra_id] = total_cuotas_credito
                
                if nro_cuotas_start == nro_cuotas_end:
                    cuota_display = f"{nro_cuotas_start} / {cuotas_info_cache[letra_id]}"
                else:
                    cuota_display = f"{nro_cuotas_start}-{nro_cuotas_end} / {cuotas_info_cache[letra_id]}"
                
                ws[f'{CREDITO_CUOTA_COL}{row_to_fill}'] = cuota_display
                
                ws[f'{CREDITO_SDO_CAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['saldo_capital_antes_pago']) 
                ws[f'{CREDITO_AB_CAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['valor_capital_consolidado'])
                ws[f'{CREDITO_INTERES_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['interes_consolidado'])
                ws[f'{CREDITO_N_SDOCAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['saldo_capital_despues_pago'])
                
                total_acumulado_capital_interes += (detalle_consolidado['valor_capital_consolidado'] + detalle_consolidado['interes_consolidado'])
            else:
                # Limpiar las filas no utilizadas
                ws[f'{CREDITO_NOMBRE_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_LETRA_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_CUOTA_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_SDO_CAP_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_AB_CAP_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_INTERES_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_N_SDOCAP_COL}{row_to_fill}'] = "" 

        # Escribir el total consolidado
        ws[CREDITO_TOTAL_CELL] = format_miles_colombian_int(total_acumulado_capital_interes)

        # --- GASTOS ADMINISTRACIÓN y TOTAL GENERAL ---
        ws[GASTOS_ADMIN_CELL_PAGO] = format_miles_colombian_int(gastos_admin) 
        
        total_general = total_acumulado_capital_interes + gastos_admin
        ws[TOTAL_GENERAL_CELL_PAGO] = format_miles_colombian_int(total_general) 

        # --- Guardar el recibo ---
        wb.save(output_path)
        return output_path

    except Exception as e:
        print(f"Error al generar recibo solo de pagos: {e}")
        import traceback
        traceback.print_exc() 
        return None