from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QScrollArea
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
import os
import sys # <-- Importa sys
from datetime import date


# --- Definición de BASE_APP_DIR para desarrollo y ejecutable ---

# ==========================================
# 🕒 SISTEMA DE GESTIÓN DE TIEMPO DINÁMICO
# ==========================================

# Variable interna (Privada) para almacenar la fecha simulada
_FECHA_SIMULADA = None 

def get_hoy():
    """
    Retorna la fecha actual del sistema O la fecha simulada si se configuró.
    Usa esta función en lugar de date.today() en toda la app.
    """
    if _FECHA_SIMULADA:
        return _FECHA_SIMULADA
    return date.today()

def get_hoy_str():
    """Retorna la fecha actual en formato string 'YYYY-MM-DD'."""
    return get_hoy().strftime("%Y-%m-%d")

def set_fecha_simulada(nueva_fecha):
    """Establece una fecha fija para simulación."""
    global _FECHA_SIMULADA
    _FECHA_SIMULADA = nueva_fecha
    print(f"🕒 MODO VIAJE EN EL TIEMPO ACTIVO: {_FECHA_SIMULADA}")

def reset_fecha_normal():
    """Vuelve al modo normal (fecha real)."""
    global _FECHA_SIMULADA
    _FECHA_SIMULADA = None
    print(f"🕒 MODO NORMAL ACTIVO: {date.today()}")

# Mantenemos estas constantes por compatibilidad, pero 
# RECOMENDACIÓN: Usar get_hoy() dentro de las funciones.
HOY = get_hoy() 
HOY_STR = get_hoy_str()


# 1. Base para archivos empaquetados (Assets, Styles)
if getattr(sys, 'frozen', False):
    STATIC_BASE_DIR = sys._MEIPASS
else:
    STATIC_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 2. Base para archivos de usuario (DB, Recibos, Liquidaciones)
if getattr(sys, 'frozen', False):
    DYNAMIC_DATA_BASE_DIR = os.path.dirname(sys.executable)
else:
    DYNAMIC_DATA_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- Definir el Año Fiscal ---
from datetime import date
today = date.today()
if today.month == 12:
    # Si estamos en Diciembre, el año fiscal es el siguiente año calendario.
    FISCAL_YEAR = str(today.year + 1)
else:
    # Si estamos de Enero a Noviembre, es el año calendario actual.
    FISCAL_YEAR = str(today.year)


# Rutas que necesitan sys._MEIPASS para funcionar
ASSETS_DIR = os.path.join(STATIC_BASE_DIR, "assets")
STYLES_DIR = os.path.join(STATIC_BASE_DIR, "styles")
#  C:\App\Archivos_BGC\
DATA_ROOT_FOLDER = os.path.join(DYNAMIC_DATA_BASE_DIR, "Archivos_BGC")
#  C:\App\Archivos_BGC\2026\
YEAR_DATA_DIR = os.path.join(DATA_ROOT_FOLDER, FISCAL_YEAR)

# DB y Archivos de salida deben usar la carpeta del año fiscal
DB_PATH = os.path.join(YEAR_DATA_DIR, "BGC-software.db")
RECIBOS_OUTPUT_DIR = os.path.join(YEAR_DATA_DIR, "Recibos")
LIQUIDACIONES_OUTPUT_DIR = os.path.join(YEAR_DATA_DIR, "Liquidaciones")

# Asegura que la carpeta del año fiscal exista (la primera vez que se ejecuta)
if not os.path.exists(YEAR_DATA_DIR):
    os.makedirs(YEAR_DATA_DIR)

DB_FILE_NAME = "BGC-software.db"

DB_PATH_FINAL = os.path.join(YEAR_DATA_DIR, DB_FILE_NAME)  # RUTA FINAL: Apunta a la carpeta del año fiscal


# --- Colores globales ---

PRIMARY_COLOR = "#1a365d"        # Azul oscuro (fondo navbar)
PRIMARY_HOVER_COLOR = "#2a4a80"  # Azul hover (botones primarios)
SECONDARY_COLOR = "#8C5B2F"      # Marrón (hover y botón activo)
TEXT_COLOR = "#FFFFFF"           # Texto blanco


# --- Metodos Globales ---

def load_styles(widget, qss_path):
    """Carga shared.qss + el QSS del componente y aplica los colores y rutas globales."""
    substitutions = {
        "PRIMARY_COLOR": PRIMARY_COLOR,
        "PRIMARY_HOVER_COLOR": PRIMARY_HOVER_COLOR,
        "SECONDARY_COLOR": SECONDARY_COLOR,
        "TEXT_COLOR": TEXT_COLOR,
        "ASSETS_DIR": ASSETS_DIR.replace("\\", "/")
    }
    try:
        combined = ""
        shared_path = os.path.join(STYLES_DIR, "shared.qss")
        if os.path.exists(shared_path):
            with open(shared_path, "r") as f:
                combined = f.read() % substitutions
        with open(qss_path, "r") as f:
            combined += "\n" + f.read() % substitutions
        widget.setStyleSheet(combined)
    except Exception as e:
        print(f"❌ Error cargando estilos de {qss_path}: {e}")

def load_svg_icon(relative_path: str, size: QSize = QSize(24, 24)) -> QIcon:
    """
    Carga un archivo SVG combinando la ruta base de assets con la ruta relativa.
    
    :param relative_path: La ruta del ícono *dentro* de la carpeta 'assets'. 
                          Ej: "icons/pig-money.svg"
    """
    # Combina la ruta absoluta donde PyInstaller colocó 'assets' con la ruta del ícono.
    absolute_path = os.path.join(ASSETS_DIR, relative_path)
    
    # Carga y Renderizado
    renderer = QSvgRenderer(absolute_path)
    if not renderer.isValid():
        # Manejo de error si el ícono no se encuentra
        print(f"Error: No se pudo cargar el ícono SVG en la ruta: {absolute_path}")
        return QIcon() # Retorna un ícono vacío para evitar fallos
        
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)

def format_miles_colombian_int(value: int) -> str:
    """
    Recibe un entero (100000) y devuelve '100.000'.
    """
    return f"{value:,}".replace(",", ".")

def parse_miles_colombian(text: str) -> int:
    """
    Recibe un texto con puntos (p.ej. '123.456') 
    y devuelve el entero 123456.
    Cualquier caracter no dígito se elimina.
    """
    clean = "".join(ch for ch in text if ch.isdigit())
    return int(clean) if clean else 0

def format_full_name_for_excel(nombres, apellidos, max_length=24):
    """
    Formatea un nombre completo (nombres + apellidos) para que se ajuste a una longitud máxima,
    reduciendo el segundo apellido o segundo nombre a una inicial si es necesario.
    """
    original_full_name = f"{nombres} {apellidos}"
    
    if len(original_full_name) <= max_length:
        return original_full_name

    parts_nombres = nombres.split()
    parts_apellidos = apellidos.split()

    # Intentar reducir solo el segundo apellido (si existe)
    if len(parts_apellidos) > 1:
        temp_apellidos = f"{parts_apellidos[0]} {parts_apellidos[1][0]}."
        temp_full_name = f"{nombres} {temp_apellidos}"
        if len(temp_full_name) <= max_length:
            return temp_full_name
    
    # Intentar reducir solo el segundo nombre (si existe)
    if len(parts_nombres) > 1:
        temp_nombres = f"{parts_nombres[0]} {parts_nombres[1][0]}."
        temp_full_name = f"{temp_nombres} {apellidos}"
        if len(temp_full_name) <= max_length:
            return temp_full_name

    # Intentar reducir segundo nombre Y segundo apellido (si ambos existen)
    if len(parts_nombres) > 1 and len(parts_apellidos) > 1:
        reduced_nombres = f"{parts_nombres[0]} {parts_nombres[1][0]}."
        reduced_apellidos = f"{parts_apellidos[0]} {parts_apellidos[1][0]}."
        final_name = f"{reduced_nombres} {reduced_apellidos}"
        if len(final_name) <= max_length:
            return final_name
            
    # Último recurso: si nada funcionó, truncar de la manera más sensata
    # Mantener primer nombre y primer apellido. Si hay espacio, agregar iniciales.
    final_parts = [parts_nombres[0]] if parts_nombres else []
    
    if len(parts_nombres) > 1:
        initial = f"{parts_nombres[1][0]}."
        if len(" ".join(final_parts + [initial, parts_apellidos[0] if parts_apellidos else ""])) <= max_length:
            final_parts.append(initial)

    if parts_apellidos:
        final_parts.append(parts_apellidos[0])

    if len(parts_apellidos) > 1:
        initial = f"{parts_apellidos[1][0]}."
        if len(" ".join(final_parts + [initial])) <= max_length:
            final_parts.append(initial)
            
    return " ".join(final_parts) # Podría ser un poco más sofisticado, pero esto ya cubre la mayoría de los casos.

def add_historical_credit(self, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data):
    """
    Agrega un crédito histórico (de años anteriores) con su liquidación manual.
    
    Args:
        capital (int): Monto del crédito
        interes (float): Tasa de interés mensual (ej: 0.05 para 5%)
        no_cuotas (int): Número total de cuotas
        fecha_inicio (str): Fecha en formato "YYYY-MM-DD"
        socios_ids (list): Lista de IDs de socios asociados al crédito
        cuotas_data (list): Lista de dicts con datos de cada cuota:
            [{
                'nro_cuota': 1,
                'fecha_vencimiento': '2024-01-15',
                'valor_cuota': 50000,
                'interes_mes': 5000,
                'cuota_mensual': 55000,
                'saldo_capital': 450000,
                'fecha_pago': '2024-01-16',  # None si no está pagada
            }, ...]
    
    Returns:
        int: La letra (ID) del crédito creado, o None si hay error
    
    Ejemplo de uso:
        cuotas = [
            {
                'nro_cuota': 1,
                'fecha_vencimiento': '2024-01-15',
                'valor_cuota': 50000,
                'interes_mes': 5000,
                'cuota_mensual': 55000,
                'saldo_capital': 450000,
                'fecha_pago': '2024-01-16',
            },
            {
                'nro_cuota': 2,
                'fecha_vencimiento': '2024-02-15',
                'valor_cuota': 50000,
                'interes_mes': 5000,
                'cuota_mensual': 55000,
                'saldo_capital': 400000,
                'fecha_pago': '2024-02-16',
            },
            # ... más cuotas ...
        ]
        
        nueva_letra = db_manager.add_historical_credit(
            capital=500000,
            interes=0.05,
            no_cuotas=12,
            fecha_inicio='2024-01-01',
            socios_ids=[1, 2, 3],
            cuotas_data=cuotas
        )
    """
    try:
        cursor = self.conn.cursor()
        
        # 1. Insertar el crédito en la tabla 'creditos'
        cursor.execute("""
            INSERT INTO creditos (capital, interes, no_cuotas, fecha_inicio)
            VALUES (?, ?, ?, ?)
        """, (capital, interes, no_cuotas, fecha_inicio))
        
        nueva_letra = cursor.lastrowid
        print(f"✅ Crédito histórico #{nueva_letra} creado.")
        
        # 2. Asociar el crédito a los socios en 'socio_credito'
        for socio_id in socios_ids:
            cursor.execute("""
                INSERT INTO socio_credito (socio_id, credito_letra)
                VALUES (?, ?)
            """, (socio_id, nueva_letra))
        
        print(f"   ✅ Crédito asociado a {len(socios_ids)} socio(s).")
        
        # 3. Insertar las cuotas en 'liquidaciones'
        for cuota in cuotas_data:
            cursor.execute("""
                INSERT INTO liquidaciones (
                    credito_letra,
                    nro_cuota,
                    fecha_vencimiento,
                    valor_cuota,
                    interes_mes,
                    cuota_mensual,
                    saldo_capital,
                    fecha_pago
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nueva_letra,
                cuota['nro_cuota'],
                cuota['fecha_vencimiento'],
                cuota['valor_cuota'],
                cuota['interes_mes'],
                cuota['cuota_mensual'],
                cuota['saldo_capital'],
                cuota['fecha_pago']  # None si no está pagada
            ))
        
        print(f"   ✅ {len(cuotas_data)} cuota(s) registrada(s) en liquidaciones.")
        
        # 4. (Opcional) Registrar en auxiliar si quieres un histórico
        # Por ejemplo, la creación del crédito como operación
        socios_nombres = []
        for socio_id in socios_ids:
            cursor.execute("SELECT nombres, apellidos FROM socios WHERE id = ?", (socio_id,))
            row = cursor.fetchone()
            if row:
                socios_nombres.append(f"{row['nombres']} {row['apellidos']}")
        
        socio_str = ", ".join(socios_nombres)
        
        self.add_to_auxiliar(
            fecha=fecha_inicio,
            tipo="Nuevo Crédito",
            socio=socio_str,
            numero=nueva_letra,
            monto=capital,
            saldo=capital,
            cuota=None,
            id_credito=str(nueva_letra)
        )
        
        print(f"   ✅ Operación registrada en auxiliar.")
        
        self.conn.commit()
        print(f"🎉 Crédito histórico #{nueva_letra} completamente creado con {len(cuotas_data)} cuotas.")
        return nueva_letra
        
    except Exception as e:
        self.conn.rollback()
        print(f"❌ Error al crear crédito histórico: {e}")
        import traceback
        traceback.print_exc()
        return None
    

def add_multiple_historical_credits(self, credits_list):
    """
    Agrega múltiples créditos históricos de una sola vez.
    
    Args:
        credits_list: Lista de dicts con la estructura:
        [
            {
                'capital': 500000,
                'interes': 0.05,
                'no_cuotas': 12,
                'fecha_inicio': '2024-01-01',
                'socios_ids': [1, 2, 3],
                'cuotas': [
                    {
                        'nro_cuota': 1,
                        'fecha_vencimiento': '2024-01-15',
                        'valor_cuota': 50000,
                        'interes_mes': 5000,
                        'cuota_mensual': 55000,
                        'saldo_capital': 450000,
                        'fecha_pago': '2024-01-16',
                    },
                    # ... más cuotas ...
                ]
            },
            # ... más créditos ...
        ]
    """
    print(f"\n📋 Iniciando carga de {len(credits_list)} créditos históricos...\n")
    
    resultados = []
    for i, credit in enumerate(credits_list, 1):
        print(f"[{i}/{len(credits_list)}]")
        letra = self.add_historical_credit(
            capital=credit['capital'],
            interes=credit['interes'],
            no_cuotas=credit['no_cuotas'],
            fecha_inicio=credit['fecha_inicio'],
            socios_ids=credit['socios_ids'],
            cuotas_data=credit['cuotas']
        )
        resultados.append(letra)
        print()
    
    print(f"✅ Se crearon {len([l for l in resultados if l])} créditos correctamente.")
    return resultados