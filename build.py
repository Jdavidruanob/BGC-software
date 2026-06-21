from PIL import Image

def crear_icono_perfecto():
    # 1. Usamos tu nuevo PNG gigante como fuente
    input_path = 'assets/logo_BGC_minimal_HQ.png'  # <--- Asegúrate que este archivo exista
    output_path = 'app_icon2.ico'
    
    try:
        img = Image.open(input_path)
        
        # 2. Definimos todos los tamaños que Windows necesita
        # 16: Explorador (lista)
        # 32: Barra de tareas
        # 48: Iconos escritorio
        # 256: Iconos gigantes (Esto es lo que te faltaba antes y causaba lo borroso)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        print(f"Generando icono desde {input_path}...")
        
        # 3. Guardamos el .ico empaquetando todas esas resoluciones dentro
        # Pillow se encarga de redimensionar el PNG gigante a cada tamaño con alta calidad (LANCZOS)
        img.save(output_path, format='ICO', sizes=icon_sizes)
        
        print(f"¡Éxito! Icono creado: {output_path}")
        print("Ahora úsalo en tu app.spec o pyinstaller.")
        
    except FileNotFoundError:
        print(f"ERROR: No encuentro el archivo '{input_path}'. Asegúrate de haber hecho el Paso 1.")

if __name__ == "__main__":
    crear_icono_perfecto()