import os
from openpyxl import load_workbook
from openpyxl.styles import Alignment 
from datetime import date
from config import format_miles_colombian_int, format_full_name_for_excel, BASE_APP_DIR

# --- Rutas y Constantes ---
TEMPLATE_COMBINADO_REL_PATH = os.path.join("assets", "templates", "recibo_template_combinado.xlsx") 
TEMPLATE_COMBINADO_PATH = os.path.join(BASE_APP_DIR, TEMPLATE_COMBINADO_REL_PATH)

OUTPUT_FOLDER_REL_PATH = "Recibos"
OUTPUT_FOLDER_PATH = os.path.join(BASE_APP_DIR, OUTPUT_FOLDER_REL_PATH)

# --- Constantes de Celda Específicas para recibo_template_combinado.xlsx ---
RECIBO_ID_CELL = 'D4'
FECHA_CELL = 'I4'
RECIBI_DE_CELL = 'G6'

# Secciones de Aportes
APORTE_DATA_START_ROW = 9
APORTE_DATA_END_ROW = 18 # 9 a 18 son 10 filas
MAX_APORTE_ROWS_IN_TEMPLATE = 10 

APORTE_NOMBRE_COL = 'B'
APORTE_SALDO_APORTES_COL = 'F' 
APORTE_MONTO_COL = 'H' 
APORTE_NUEVO_SALDO_COL = 'J' 
TOTAL_APORTES_CELL = 'H19' 

# Secciones de Pagos de Crédito
CREDITO_DATA_START_ROW = 22
CREDITO_DATA_END_ROW = 32 # 22 a 32 son 11 filas
MAX_CREDITO_ROWS_IN_TEMPLATE = 11 

CREDITO_NOMBRE_COL = 'B' 
CREDITO_LETRA_COL = 'F'
CREDITO_CUOTA_COL = 'G'
CREDITO_SDO_CAP_COL = 'H'
CREDITO_AB_CAP_COL = 'I'
CREDITO_INTERES_COL = 'J' 
CREDITO_N_SDOCAP_COL = 'K' 

# Totales
TOTAL_CREDITOS_CELL = 'H33' 
GASTOS_ADMIN_CELL_COMBINADO = 'K35'
TOTAL_GENERAL_CELL_COMBINADO = 'K36'

# Valor por cada aporte
GASTO_POR_APORTE = 3000

# --- Funciones auxiliares ---
#

def generar_recibo_combinado(
    db_manager, 
    recibo_id: int,
    recibi_de_data: dict, 
    aportes_info: list = None, 
    pagos_credito_info: list = None
):
    """
    Genera un recibo combinado de aportes y pagos de crédito.
    El gasto administrativo se calcula como GASTO_POR_APORTE * número de aportes.
    """
    if aportes_info is None:
        aportes_info = []
    if pagos_credito_info is None:
        pagos_credito_info = []

    try:
        os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
        file_name = f"Recibo_{recibo_id}_{date.today().strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER_PATH, file_name)

        wb = load_workbook(TEMPLATE_COMBINADO_PATH) 
        ws = wb.active

        # --- Reemplazar datos de CABECERA ---
        ws[RECIBO_ID_CELL] = recibo_id
        ws[FECHA_CELL] = date.today().strftime("%d/%m/%Y")
        
        recibi_de_full_name = f"{recibi_de_data['nombres']} {recibi_de_data['apellidos']}".upper()
        ws[RECIBI_DE_CELL] = recibi_de_full_name
        ws[RECIBI_DE_CELL].alignment = Alignment(horizontal='center') 

        # --- PROCESAR APORTES ---
        num_aportes_to_display = len(aportes_info)
        total_aportes_monto = 0 

        if num_aportes_to_display > MAX_APORTE_ROWS_IN_TEMPLATE:
            print(f"ADVERTENCIA: Se intentaron procesar {num_aportes_to_display} aportes, "
                    f"pero la plantilla solo soporta {MAX_APORTE_ROWS_IN_TEMPLATE}. Se truncará.")
            aportes_info = aportes_info[:MAX_APORTE_ROWS_IN_TEMPLATE]
            num_aportes_to_display = len(aportes_info)

        for i in range(MAX_APORTE_ROWS_IN_TEMPLATE):
            row_to_fill = APORTE_DATA_START_ROW + i
            if i < num_aportes_to_display:
                aporte_detail = aportes_info[i]
                socio_data = aporte_detail['socio_data'] 
                monto_aporte = aporte_detail['monto']
                saldo_anterior_aporte = aporte_detail['saldo_anterior_aporte'] 
                nuevo_saldo_aporte = aporte_detail['nuevo_saldo_aporte'] 

                formatted_socio_name = format_full_name_for_excel(
                    socio_data['nombres'], 
                    socio_data['apellidos'], 
                    max_length=24
                )
                ws[f'{APORTE_NOMBRE_COL}{row_to_fill}'] = formatted_socio_name
                ws[f'{APORTE_SALDO_APORTES_COL}{row_to_fill}'] = format_miles_colombian_int(saldo_anterior_aporte) 
                ws[f'{APORTE_MONTO_COL}{row_to_fill}'] = format_miles_colombian_int(monto_aporte)
                ws[f'{APORTE_NUEVO_SALDO_COL}{row_to_fill}'] = format_miles_colombian_int(nuevo_saldo_aporte) 
                
                total_aportes_monto += monto_aporte 
            else:
                # Limpiar filas no utilizadas
                ws[f'{APORTE_NOMBRE_COL}{row_to_fill}'] = ""
                ws[f'{APORTE_SALDO_APORTES_COL}{row_to_fill}'] = ""
                ws[f'{APORTE_MONTO_COL}{row_to_fill}'] = ""
                ws[f'{APORTE_NUEVO_SALDO_COL}{row_to_fill}'] = ""
        
        ws[TOTAL_APORTES_CELL] = format_miles_colombian_int(total_aportes_monto)

        # --- PROCESAR PAGOS DE CRÉDITO CONSOLIDADOS ---
        total_pagos_credito_monto_total = 0 
        num_credit_details_consolidated = len(pagos_credito_info)

        if num_credit_details_consolidated > MAX_CREDITO_ROWS_IN_TEMPLATE:
            print(f"ADVERTENCIA: Se intentaron procesar {num_credit_details_consolidated} pagos de crédito consolidados, "
                    f"pero la plantilla solo soporta {MAX_CREDITO_ROWS_IN_TEMPLATE}. Se truncará.")
            pagos_credito_info = pagos_credito_info[:MAX_CREDITO_ROWS_IN_TEMPLATE]
            num_credit_details_consolidated = len(pagos_credito_info)
        
        # Cache para almacenar el número total de cuotas por letra
        cuotas_info_cache = {}

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

                if letra_id not in cuotas_info_cache:
                    total_cuotas_credito = db_manager.get_total_cuotas_credito(letra_id)
                    cuotas_info_cache[letra_id] = total_cuotas_credito
                
                if nro_cuotas_start == nro_cuotas_end:
                    cuota_display = f"{nro_cuotas_start}/{cuotas_info_cache[letra_id]}"
                else:
                    cuota_display = f"{nro_cuotas_start}-{nro_cuotas_end}/{cuotas_info_cache[letra_id]}"
                
                ws[f'{CREDITO_CUOTA_COL}{row_to_fill}'] = cuota_display
                
                ws[f'{CREDITO_SDO_CAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['saldo_capital_antes_pago']) 
                ws[f'{CREDITO_AB_CAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['valor_capital_consolidado'])
                ws[f'{CREDITO_INTERES_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['interes_consolidado'])
                ws[f'{CREDITO_N_SDOCAP_COL}{row_to_fill}'] = format_miles_colombian_int(detalle_consolidado['saldo_capital_despues_pago'])
                
                total_pagos_credito_monto_total += (detalle_consolidado['valor_capital_consolidado'] + detalle_consolidado['interes_consolidado'])
            else:
                # Limpiar las filas no utilizadas
                ws[f'{CREDITO_NOMBRE_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_LETRA_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_CUOTA_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_SDO_CAP_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_AB_CAP_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_INTERES_COL}{row_to_fill}'] = "" 
                ws[f'{CREDITO_N_SDOCAP_COL}{row_to_fill}'] = "" 
        
        ws[TOTAL_CREDITOS_CELL] = format_miles_colombian_int(total_pagos_credito_monto_total)

        # --- GASTOS ADMINISTRACIÓN y TOTAL GENERAL ---
        # *** ESTE ES EL CAMBIO CLAVE ***
        # El gasto administrativo ahora se calcula internamente
        gastos_admin = GASTO_POR_APORTE * num_aportes_to_display
        ws[GASTOS_ADMIN_CELL_COMBINADO] = format_miles_colombian_int(gastos_admin) 
        
        total_general = total_aportes_monto + total_pagos_credito_monto_total + gastos_admin
        ws[TOTAL_GENERAL_CELL_COMBINADO] = format_miles_colombian_int(total_general) 
    
        # --- Guardar el recibo ---
        wb.save(output_path)
        return output_path

    except Exception as e:
        print(f"Error al generar recibo combinado: {e}")
        import traceback
        traceback.print_exc() 
        return None