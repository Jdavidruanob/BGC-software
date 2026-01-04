import sqlite3
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """ Conecta a la base de datos SQLite. """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acceder como diccionario
            return True
        except sqlite3.Error as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False

    def create_tables(self):
        """ Crea las tablas necesarias con la estructura completa para mora y abonos. """
        try:
            cursor = self.conn.cursor()

            # Tabla de socios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socios (
                    id INTEGER PRIMARY KEY,
                    cc TEXT,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    saldo INTEGER DEFAULT 0,
                    celular TEXT,
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla de créditos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creditos (
                    letra INTEGER PRIMARY KEY AUTOINCREMENT,
                    capital INTEGER NOT NULL,
                    interes REAL NOT NULL,
                    no_cuotas INTEGER NOT NULL,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Relación muchos a muchos: socios - créditos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socio_credito (
                    socio_id INTEGER NOT NULL,
                    credito_letra INTEGER NOT NULL,
                    PRIMARY KEY (socio_id, credito_letra),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            # Tabla de liquidaciones: cada fila es una cuota programada (Incluye Mora y Notificaciones)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liquidaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credito_letra INTEGER NOT NULL,
                    nro_cuota INTEGER NOT NULL,
                    fecha_vencimiento DATE NOT NULL,
                    valor_cuota INTEGER NOT NULL,
                    interes_mes INTEGER NOT NULL,
                    cuota_mensual INTEGER NOT NULL,
                    saldo_capital INTEGER NOT NULL,
                    fecha_pago DATE,
                    interes_mora INTEGER DEFAULT 0,
                    mora_aplicada INTEGER DEFAULT 0,
                    notif_prev_enviada INTEGER DEFAULT 0,
                    notif_venc_enviada INTEGER DEFAULT 0,
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            # Tabla de recibos (cabecera)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recibos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socio_id INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archivo_path TEXT,
                    FOREIGN KEY (socio_id) REFERENCES socios(id)
                )
            """)

            # Detalle de recibos: Incluye 'abono_capital' y columna para recaudación de mora
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_recibo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recibo_id INTEGER NOT NULL,
                    tipo_operacion TEXT NOT NULL CHECK (tipo_operacion IN ('aporte', 'pago_credito', 'retiro', 'abono_capital')),
                    socio_id INTEGER NOT NULL,
                    credito_letra INTEGER,
                    nro_cuota INTEGER,
                    monto INTEGER NOT NULL,
                    abono_mora INTEGER DEFAULT 0,
                    FOREIGN KEY (recibo_id) REFERENCES recibos(id),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            # Libro Auxiliar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auxiliar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    socio TEXT NOT NULL,
                    recibo INTEGER,         -- Nuevo: Para el # de recibo (puede ser NULL)
                    monto INTEGER NOT NULL,
                    saldo INTEGER NOT NULL,
                    cuota INTEGER,
                    id_credito TEXT         -- Ya existente: Para el # de letra
                )
            """)

            # Tabla de configuración (clave-valor)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            self.conn.commit()
            print("✅ Tablas creadas con estructura actualizada.")
        except sqlite3.Error as e:
            print(f"❌ Error creando tablas: {e}")

    def initialize_config_values(self):
            """
            Garantiza que existan los valores base en la tabla config.
            Si ya existen, NO los sobrescribe (preserva el dinero actual).
            """
            cursor = self.conn.cursor()
            
            # Diccionario con valores por defecto
            # total_admin aquí guardará el histórico de papelería/gestión
            default_values = {
                "saldo_en_caja": "0",
                "total_admin": "0",    
                "porcentaje_mora": "0.02" 
            }

            for key, default_val in default_values.items():
                # Intentamos insertar ignorando si ya existe (INSERT OR IGNORE)
                cursor.execute("""
                    INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)
                """, (key, default_val))
            
            self.conn.commit()
            print("✅ Configuración inicial verificada.")

    def run_annual_migration(self, prev_db_path):
        """
        Ejecuta la migración de saldos y créditos activos del año anterior al actual.
        
        """
        print(f"\n⏳ Iniciando migración de datos desde: {prev_db_path}")

        # 1. Conexión a la base de datos anterior (SOLO LECTURA)
        try:
            prev_conn = sqlite3.connect(prev_db_path)
            prev_cursor = prev_conn.cursor()
        except sqlite3.Error as e:
            print(f"❌ ERROR: No se pudo conectar a la DB anterior ({prev_db_path}). {e}")
            return

        current_cursor = self.conn.cursor() # Cursor de la DB actual (DB_PATH_FINAL)

        try:
            # A) Migrar Socios y Saldos Finales
            # Se leen todos los socios y sus datos (saldos) del año anterior.
            socios_to_migrate = prev_cursor.execute("""
                SELECT id, cc, nombres, apellidos, saldo, celular, photo_path, created_at
                FROM socios
            """).fetchall()

            if socios_to_migrate:
                insert_sql = """
                    INSERT INTO socios (id, cc, nombres, apellidos, saldo, celular, photo_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                current_cursor.executemany(insert_sql, socios_to_migrate)
                print(f"   ✅ {len(socios_to_migrate)} socios y saldos migrados.")

            saldo_caja_to_migrate = prev_cursor.execute("""
                SELECT key, value
                FROM config
                WHERE key = 'saldo_en_caja'
            """).fetchone() # Usamos fetchone() porque solo esperamos una fila

            if saldo_caja_to_migrate:
                insert_config_sql = "INSERT INTO config (key, value) VALUES (?, ?)"
                # Insertamos solo el saldo_en_caja en la nueva tabla config
                current_cursor.execute(insert_config_sql, (saldo_caja_to_migrate['key'], saldo_caja_to_migrate['value']))
                print("   ✅ Saldo de caja migrado de la tabla 'config'.")
            
            # Opcional: Asegurar que otros contadores de config se reseteen (si los tienes)
            # Por ejemplo, si total_admin debe empezar en 0:
            current_cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ('total_admin', '0'))

            # B) Identificar y Migrar Créditos Activos (Cuotas pendientes en 'liquidaciones')
            # Buscamos créditos que tengan al menos UNA cuota con fecha_pago NULL.
            active_credits_query = """
                SELECT DISTINCT credito_letra FROM liquidaciones WHERE fecha_pago IS NULL;
            """
            active_credits = prev_cursor.execute(active_credits_query).fetchall()
            active_credit_ids = [c[0] for c in active_credits]
            
            if active_credit_ids:
                # 1. Migrar la tabla 'creditos' para los activos
                credits_to_migrate = prev_cursor.execute(f"SELECT letra, capital, interes, no_cuotas, fecha_inicio FROM creditos WHERE letra IN ({','.join(map(str, active_credit_ids))})").fetchall()
                insert_credits_sql = "INSERT INTO creditos (letra, capital, interes, no_cuotas, fecha_inicio) VALUES (?, ?, ?, ?, ?)"
                current_cursor.executemany(insert_credits_sql, credits_to_migrate)
                print(f"   ✅ {len(active_credit_ids)} créditos activos migrados.")

                # 2. Migrar la tabla 'socio_credito' (Relación)
                relations_to_migrate = prev_cursor.execute(f"SELECT socio_id, credito_letra FROM socio_credito WHERE credito_letra IN ({','.join(map(str, active_credit_ids))})").fetchall()
                insert_relations_sql = "INSERT INTO socio_credito (socio_id, credito_letra) VALUES (?, ?)"
                current_cursor.executemany(insert_relations_sql, relations_to_migrate)

                # 3. Migrar TODAS las cuotas (pagadas y pendientes) de liquidaciones
                liquidations_to_migrate = prev_cursor.execute(f"""
                    SELECT credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_pago 
                    FROM liquidaciones 
                    WHERE credito_letra IN ({','.join(map(str, active_credit_ids))})
                """).fetchall()
                
                insert_liquidations_sql = """
                    INSERT INTO liquidaciones (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_pago) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                current_cursor.executemany(insert_liquidations_sql, liquidations_to_migrate)
                print("   ✅ Liquidaciones completas (cuotas pagadas y pendientes) de créditos activos migrados.")

            # C) Resetear Secuencias (Contadores Anuales)
            self.set_sequence_start_value("recibos", 230) 
            self.set_sequence_start_value("creditos", 437) 
            

            self.conn.commit()
            print("🎉 Migración de año fiscal completada.")

        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ ERROR durante la migración. Se revertieron los cambios: {e}")
        finally:
            prev_conn.close()

    def get_all_members(self):
        """ Devuelve una lista de todos los socios con ID, nombre corto, foto y créditos activos. """
        try:
            cursor = self.conn.cursor() # Cursor de la DB actual
            # Consulta para obtener socios y contar créditos activos
            cursor.execute("""         
                SELECT s.id,
                       s.nombres,
                       s.apellidos,
                       COALESCE(s.photo_path, '') as photo_path,
                       COUNT(sc.credito_letra) as creditos
                FROM socios s
                LEFT JOIN socio_credito sc ON s.id = sc.socio_id --
                GROUP BY s.id
                ORDER BY s.nombres  
            """)

            results = []
            for row in cursor.fetchall(): # fetchall devuelve una lista de filas
                # Procesar cada fila para obtener los datos requeridos
                member_id = row["id"]
                primer_nombre = row["nombres"].split()[0]
                primer_apellido = row["apellidos"].split()[0]
                nombre_corto = f"{primer_nombre} {primer_apellido}"
                foto = row["photo_path"] or "assets/photos/default_user.png"
                creditos = row["creditos"]
                label = "Sin créditos activos" if creditos == 0 else f"{creditos} crédito(s) activo(s)" # Etiqueta según créditos
                results.append((member_id, nombre_corto, foto, label)) 
            return results
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo socios: {e}")
            return []
        
    def get_all_members_full(self):
        """ Devuelve una lista de todos los socios con todos sus datos. """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT s.*,
                    COUNT(sc.credito_letra) as creditos
                FROM socios s
                LEFT JOIN socio_credito sc ON s.id = sc.socio_id
                GROUP BY s.id
                ORDER BY s.nombres
            """)
            return [dict(row) for row in cursor.fetchall()] # Convertir cada fila a diccionario 
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo socios completos: {e}")
            return []

    def search_members_by_name(self, search_term):
        """ Busca socios cuyo nombre o apellido contenga el término dado. """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT s.id,
                       s.nombres,
                       s.apellidos,
                       COALESCE(s.photo_path, '') as photo_path,
                       COUNT(sc.credito_letra) as creditos
                FROM socios s
                LEFT JOIN socio_credito sc ON s.id = sc.socio_id
                WHERE s.nombres LIKE ? OR s.apellidos LIKE ?
                GROUP BY s.id
                ORDER BY s.nombres
            """, (f"%{search_term}%", f"%{search_term}%"))

            results = []
            for row in cursor.fetchall():
                member_id = row["id"]
                primer_nombre = row["nombres"].split()[0]
                primer_apellido = row["apellidos"].split()[0]
                nombre_corto = f"{primer_nombre} {primer_apellido}"
                foto = row["photo_path"] or "assets/photos/default_user.png"
                creditos = row["creditos"]
                label = "Sin créditos activos" if creditos == 0 else f"{creditos} crédito(s) activo(s)"
                results.append((member_id, nombre_corto, foto, label))
            return results
        except sqlite3.Error as e:
            print(f"❌ Error en búsqueda de socios: {e}")
            return []

    def get_member_by_id(self, member_id):
        """ Devuelve todos los datos de un socio dado su ID. """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, cc, nombres, apellidos, celular, saldo, photo_path, created_at
                FROM socios
                WHERE id = ?
            """, (member_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo datos del socio: {e}")
            return None

    def get_active_credits_by_member(self, member_id):
        """ Devuelve los créditos activos (con cuotas pendientes) de un socio. """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT c.letra, c.capital, c.interes, c.no_cuotas
                FROM creditos c
                JOIN socio_credito sc ON c.letra = sc.credito_letra
                WHERE sc.socio_id = ?
            """, (member_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo créditos activos: {e}")
            return []

    def add_credit(self, socio_ids, capital, interes, no_cuotas):
            """ Agrega un nuevo crédito y lo asocia a los socios dados. """
            try:
                cursor = self.conn.cursor()

                # *** CAMBIO AQUÍ: ***
                # Quita las líneas de cálculo de max_letra y new_letra
                # cursor.execute("SELECT MAX(letra) FROM creditos")
                # max_letra = cursor.fetchone()[0]
                # new_letra = (max_letra or 0) + 1

                # Inserta SIN mencionar 'letra' en la lista de columnas.
                # SQLite lo asignará automáticamente porque es AUTOINCREMENT.
                cursor.execute("""
                    INSERT INTO creditos (capital, interes, no_cuotas, fecha_inicio) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP) 
                """, (capital, interes, no_cuotas)) # <-- Quita new_letra de aquí

                # Obtén la letra generada por AUTOINCREMENT
                new_letra = cursor.lastrowid # <--- ¡Ahora sí usa lastrowid para obtener el ID generado!

                for socio_id in socio_ids:
                    cursor.execute("""
                        INSERT INTO socio_credito (socio_id, credito_letra)
                        VALUES (?, ?)
                    """, (socio_id, new_letra))

                self.conn.commit()
                print(f"✅ Crédito #{new_letra} creado exitosamente.")
                return new_letra
            except Exception as e:
                print(f"❌ Error al crear crédito: {e}")
                self.conn.rollback() # Añade rollback en caso de error
                return None

    
# socios operacones

    def add_member(self, nombres, apellidos, phone, photo_path, saldo=0):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO socios (nombres, apellidos, celular, photo_path, saldo)
                VALUES (?, ?, ?, ?, ?)
            """, (nombres, apellidos, phone, photo_path, saldo))

            # Actualizar saldo_en_caja en config
            """ saldo_actual = self.get_config_value_as_int("saldo_en_caja")#FIXME: sumar saldo
            nuevo_saldo = saldo_actual + saldo
            self.set_config_value("saldo_en_caja", str(nuevo_saldo)) """

            self.conn.commit()
            print(f"✅ Socio '{nombres} {apellidos}' agregado correctamente.")
        except Exception as e:
            print(f"❌ Error agregando socio: {e}")


    def delete_member(self, socio_id):
        try:
            cursor = self.conn.cursor()

            # 1. Obtener saldo del socio antes de eliminarlo
            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (socio_id,))
            row = cursor.fetchone()
            if not row:
                print("⚠️ Socio no encontrado.")
                return False
            saldo_socio = row[0]

            # 2. Obtener letras de créditos del socio
            cursor.execute("""
                SELECT credito_letra FROM socio_credito WHERE socio_id = ?
            """, (socio_id,))
            letras = [row[0] for row in cursor.fetchall()]

            # 3. Eliminar relación socio_credito
            cursor.execute("DELETE FROM socio_credito WHERE socio_id = ?", (socio_id,))

            # 4. Verificar qué créditos quedaron sin socios
            letras_a_eliminar = []
            for letra in letras:
                cursor.execute("""
                    SELECT COUNT(*) FROM socio_credito WHERE credito_letra = ?
                """, (letra,))
                count = cursor.fetchone()[0]
                if count == 0:
                    letras_a_eliminar.append(letra)

            # 5. Eliminar liquidaciones y créditos sin socios
            for letra in letras_a_eliminar:
                cursor.execute("DELETE FROM liquidaciones WHERE credito_letra = ?", (letra,))
                cursor.execute("DELETE FROM creditos WHERE letra = ?", (letra,))
                print(f"🗑️ Crédito #{letra} eliminado por no tener más socios.")

            # 6. Eliminar detalle_recibo relacionados con el socio
            cursor.execute("DELETE FROM detalle_recibo WHERE socio_id = ?", (socio_id,))

            # 7. Eliminar recibos donde el socio sea quien entregó el dinero
            cursor.execute("DELETE FROM recibos WHERE socio_id = ?", (socio_id,))

            # 8. Eliminar al socio
            cursor.execute("DELETE FROM socios WHERE id = ?", (socio_id,))

            # 9. Actualizar saldo en caja
            """ saldo_caja = self.get_config_value_as_int("saldo_en_caja")
            nuevo_saldo = saldo_caja - saldo_socio
            self.set_config_value("saldo_en_caja", str(nuevo_saldo))
            """
            self.conn.commit()
            print(f"🗑️ Socio con ID {socio_id} eliminado junto con datos relacionados.")
            return True

        except Exception as e:
            print(f"❌ Error al eliminar socio: {e}")
            self.conn.rollback()
            return False


        
    def update_member(self, socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo):
        try:
            cursor = self.conn.cursor()

            # Obtener saldo anterior
            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (socio_id,))
            row = cursor.fetchone()
            if not row:
                print("⚠️ Socio no encontrado.")
                return False
            saldo_anterior = row[0]

            # Actualizar datos
            cursor.execute("""
                UPDATE socios
                SET nombres = ?, apellidos = ?, celular = ?, photo_path = ?, saldo = ?
                WHERE id = ?
            """, (nombres, apellidos, phone, photo_path, nuevo_saldo, socio_id))

            # Ajustar saldo_en_caja
            """ diferencia = nuevo_saldo - saldo_anterior
            saldo_caja = self.get_config_value_as_int("saldo_en_caja")
            nuevo_saldo_caja = saldo_caja + diferencia
            self.set_config_value("saldo_en_caja", str(nuevo_saldo_caja)) """

            self.conn.commit()
            print(f"✏️ Socio '{nombres} {apellidos}' actualizado correctamente.")
            return True
        except Exception as e:
            print(f"❌ Error actualizando socio: {e}")
            self.conn.rollback()
            return False


    def get_credit_by_letra(self, letra):
        query = """
        SELECT c.*, GROUP_CONCAT(s.nombres || ' ' || s.apellidos, ', ') AS socios
        FROM creditos c
        JOIN socio_credito sc ON sc.credito_letra = c.letra
        JOIN socios s ON s.id = sc.socio_id
        WHERE c.letra = ?
        GROUP BY c.letra
        """
        return self.conn.execute(query, (letra,)).fetchone()

    def guardar_liquidaciones(self, lista_cuotas):
        try:
            query = """
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
            """
            self.conn.executemany(query, lista_cuotas)
            self.conn.commit()
            print("✅ Liquidaciones guardadas.")
        except sqlite3.Error as e:
            print(f"❌ Error guardando liquidaciones: {e}")

    def create_aporte_recibo(self, recibi_de_id, aportes):
        """
        - recibi_de_id: int, socio que entrega el dinero
        - aportes: lista de tuplas [(socio_id, monto), ...]
        Devuelve el id del recibo creado.
        """
        try:
            cursor = self.conn.cursor()
            # 1. Insertar cabecera en recibos
            cursor.execute("""
                INSERT INTO recibos (socio_id)
                VALUES (?)
            """, (recibi_de_id,))
            recibo_id = cursor.lastrowid

            # 2. Para cada aporte: insertar detalle y actualizar saldo socio
            for socio_id, monto in aportes:
                # 2.1 insertar detalle
                cursor.execute("""
                    INSERT INTO detalle_recibo (
                        recibo_id, tipo_operacion, socio_id, monto
                    ) VALUES (?, 'aporte', ?, ?)
                """, (recibo_id, socio_id, monto))
                # 2.2 actualizar saldo
                cursor.execute("""
                    UPDATE socios
                    SET saldo = saldo + ?
                    WHERE id = ?
                """, (monto, socio_id))

            self.conn.commit()
            return recibo_id

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error creando recibo de aporte: {e}")
            return None

    def get_recibo(self, recibo_id):
        """(Opcional) devuelve cabecera y detalles si los necesitas luego."""
        # implementación según conveniencia...
        pass

    def get_letras_by_socio_id(self, socio_id):
        """ Devuelve las letras de crédito asociadas a un socio. """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT c.letra, c.capital, c.interes, c.no_cuotas
                FROM creditos c
                JOIN socio_credito sc ON c.letra = sc.credito_letra
                WHERE sc.socio_id = ?
            """, (socio_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo letras por socio: {e}")
            return []
        
    def add_to_auxiliar(self, fecha, tipo, socio, monto, saldo, recibo=None, cuota=None, id_credito=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO auxiliar (fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito))
            self.conn.commit()
        except Exception as e:
            print(f"❌ Error al añadir al auxiliar: {e}")
            self.conn.rollback()

    def get_auxiliary_operations(self, limit=10, offset=0, 
                            start_date=None, end_date=None, 
                            operation_type=None, socio_name=None,
                            numero=None, 
                            letra_credito=None):

        # CAMBIO 1: Seleccionamos 'recibo' en lugar de 'numero'
        # 'id_credito' se mantiene igual
        query = """
            SELECT fecha, tipo, socio, recibo, monto, saldo, cuota, id_credito
            FROM auxiliar
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND fecha >= ?"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= ?"
            params.append(end_date)
        if operation_type:
            query += " AND tipo = ?"
            params.append(operation_type)
        if socio_name:
            query += " AND LOWER(socio) LIKE ?"
            params.append(f"%{socio_name.lower()}%")
        
        # CAMBIO 2: El filtro 'numero' ahora busca en la columna 'recibo'
        if numero is not None:
            query += " AND recibo = ?"
            params.append(numero)
        
        # Este filtro busca en la columna 'id_credito' (esto no cambia)
        if letra_credito:
            query += " AND id_credito = ?" 
            params.append(letra_credito)

        query += " ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, tuple(params))
            
            # Tu corrección se mantiene: primero fetch, luego description
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            operations = [dict(zip(column_names, row)) for row in rows]
            
            print(f"✅ Se recuperaron {len(operations)} operaciones")
            return operations
        except Exception as e:
            print(f"❌ Error obteniendo operaciones del auxiliar: {e}")
            return []
        
    def get_config_value_as_int(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return int(row["value"]) if row else 0

    def set_config_value(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO config (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        self.conn.commit()

    # --- MÉTODO QUE FALTABA ---
    def get_total_cuotas_credito(self, credito_letra):
        """
        Obtiene el número total de cuotas para un crédito específico.
        Este valor está en la tabla 'creditos' en la columna 'no_cuotas'.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT no_cuotas FROM creditos WHERE letra = ?", (credito_letra,))
            result = cursor.fetchone()
            if result:
                return result['no_cuotas']
            return 0 # Retorna 0 si la letra no se encuentra
        except sqlite3.Error as e:
            print(f"Error al obtener el total de cuotas para la letra {credito_letra}: {e}")
            return 0
        
    def get_member_balance(self, member_id):
        """
        Obtiene el saldo actual de un socio por su ID.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (member_id,))
            result = cursor.fetchone()
            return result['saldo'] if result else 0
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo saldo del socio {member_id}: {e}")
            return 0 # Retorna 0 en caso de error o si el socio no existe

    def set_sequence_start_value(self, table_name: str, start_value: int):
            """
            Establece el valor de la secuencia AUTOINCREMENT para una tabla dada.
            Usa INSERT OR REPLACE para asegurar que la entrada existe o se actualiza.
            Esto asegura que el próximo ID insertado sea start_value + 1.
            """
            try:
                cursor = self.conn.cursor()
                # *** CAMBIO AQUÍ: Usamos INSERT OR REPLACE ***
                cursor.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES (?, ?)", (table_name, start_value))
                self.conn.commit()
                print(f"✅ Secuencia de '{table_name}' establecida a {start_value}. Siguiente ID será {start_value + 1}.")
            except Exception as e:
                print(f"❌ Error al establecer la secuencia para '{table_name}': {e}")
                self.conn.rollback()

    def debug_check_auxiliar(self):
        """Método temporal para verificar qué hay en la tabla auxiliar"""
        try:
            cursor = self.conn.cursor()
            
            # 1. Contar todas las filas
            cursor.execute("SELECT COUNT(*) as total FROM auxiliar")
            result = cursor.fetchone()
            total = result['total'] if result else 0
            
            print(f"\n🔍 DEBUG AUXILIAR:")
            print(f"   Total de filas en tabla: {total}")
            
            if total > 0:
                # 2. Mostrar todas las columnas
                cursor.execute("PRAGMA table_info(auxiliar)")
                columns = cursor.fetchall()
                print(f"   Columnas en la tabla:")
                for col in columns:
                    print(f"      - {col['name']} ({col['type']})")
                
                # 3. Mostrar primeras 3 filas completas
                cursor.execute("SELECT * FROM auxiliar LIMIT 3")
                rows = cursor.fetchall()
                print(f"\n   Primeras 3 filas:")
                for i, row in enumerate(rows, 1):
                    print(f"      Fila {i}: {dict(row)}")
                
                # 4. Probar la query exacta que usa get_auxiliary_operations()
                print(f"\n   Probando query de get_auxiliary_operations():")
                query = """
                    SELECT fecha, tipo, socio, numero, monto, saldo, cuota, id_credito
                    FROM auxiliar
                    WHERE 1=1
                    ORDER BY fecha DESC, id DESC 
                    LIMIT 10 OFFSET 0
                """
                cursor.execute(query)
                test_rows = cursor.fetchall()
                print(f"   Resultado: {len(test_rows)} filas")
                if test_rows:
                    print(f"   Primera fila: {dict(test_rows[0])}")
            else:
                print("   ⚠️ La tabla auxiliar está VACÍA")
                
        except Exception as e:
            print(f"❌ Error en debug_check_auxiliar: {e}")
            import traceback
            traceback.print_exc()

    def add_historical_credit(self, letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data):
        """
        Agrega un crédito histórico permitiendo especificar el número de letra manualmente.
        """
        try:
            cursor = self.conn.cursor()
            
            # 1. Insertar el crédito especificando la letra (ID)
            # Si letra es None, SQLite usará AUTOINCREMENT, pero aquí lo forzamos.
            cursor.execute("""
                INSERT INTO creditos (letra, capital, interes, no_cuotas, fecha_inicio)
                VALUES (?, ?, ?, ?, ?)
            """, (letra, capital, interes, no_cuotas, fecha_inicio))
            
            # Si pasamos letra=None, recuperamos la asignada, si no, usamos la que pasamos.
            nueva_letra = letra if letra is not None else cursor.lastrowid
            print(f"✅ Crédito histórico #{nueva_letra} creado.")
            
            # 2. Asociar el crédito a los socios
            for socio_id in socios_ids:
                cursor.execute("""
                    INSERT INTO socio_credito (socio_id, credito_letra)
                    VALUES (?, ?)
                """, (socio_id, nueva_letra))
            
            # 3. Insertar las cuotas en 'liquidaciones'
            for cuota in cuotas_data:
                cursor.execute("""
                    INSERT INTO liquidaciones (
                        credito_letra, nro_cuota, fecha_vencimiento, valor_cuota,
                        interes_mes, cuota_mensual, saldo_capital, fecha_pago
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nueva_letra,
                    cuota['nro_cuota'],
                    cuota['fecha_vencimiento'],
                    cuota['valor_cuota'],
                    cuota['interes_mes'],
                    cuota['cuota_mensual'],
                    cuota['saldo_capital'],
                    cuota['fecha_pago']
                ))
            
            # 4. Registrar en auxiliar
            socios_nombres = []
            for socio_id in socios_ids:
                cursor.execute("SELECT nombres, apellidos FROM socios WHERE id = ?", (socio_id,))
                row = cursor.fetchone()
                if row:
                    # row es una tupla o dict según tu configuración de row_factory
                    socios_nombres.append(f"{row[0]} {row[1]}") 
            
            
            self.conn.commit()
            return nueva_letra
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error al crear crédito histórico letra {letra}: {e}")
            return None
        
    def add_multiple_historical_credits(self, credits_list):
        """
        Agrega múltiples créditos históricos procesando el campo 'letra' de cada uno.
        """
        print(f"\n📋 Iniciando carga masiva de {len(credits_list)} créditos...\n")
        
        resultados = []
        for i, credit in enumerate(credits_list, 1):
            # Extraemos la letra si existe en el dict, si no, enviamos None
            letra_especifica = credit.get('letra') 
            
            print(f"[{i}/{len(credits_list)}] Procesando Letra: {letra_especifica}")
            
            res = self.add_historical_credit(
                letra=letra_especifica,
                capital=credit['capital'],
                interes=credit['interes'],
                no_cuotas=credit['no_cuotas'],
                fecha_inicio=credit['fecha_inicio'],
                socios_ids=credit['socios_ids'],
                cuotas_data=credit['cuotas']
            )
            resultados.append(res)
        
        exitosos = len([l for l in resultados if l])
        print(f"\n✅ Proceso finalizado: {exitosos} créditos creados correctamente.")
        return resultados
    
    def registrar_credito_completo(self, socio_ids, capital, interes_tasa, n_cuotas, usuario_tesorero="ALVARO L. BURBANO GARCIA"):
        """
        Crea el crédito, calcula la liquidación robusta, descuenta caja y registra en auxiliar.
        Todo en una sola transacción atómica.
        Retorna: (letra_id, saldo_nuevo_caja)
        """
        try:
            cursor = self.conn.cursor()
            fecha_actual_str = date.today().strftime("%Y-%m-%d")

            # 1. INSERTAR CABECERA DEL CRÉDITO
            # Convertimos la lista de IDs a string "1, 2" para visualización rápida en columna 'socios'
            # (Aunque idealmente usas la tabla relacional socio_credito, aquí mantenemos tu lógica actual)
            # Primero obtenemos nombres para guardar el string "Nombres..."
            placeholders = ','.join(['?'] * len(socio_ids))
            cursor.execute(f"SELECT nombres, apellidos FROM socios WHERE id IN ({placeholders})", socio_ids)
            socios_data = cursor.fetchall()
            nombres_txt = ", ".join([f"{s['nombres']} {s['apellidos']}" for s in socios_data])

            cursor.execute("""
                INSERT INTO creditos (capital, interes, no_cuotas, fecha_inicio)
                VALUES (?, ?, ?, ?)
            """, (capital, interes_tasa, n_cuotas, fecha_actual_str))
            
            letra_id = cursor.lastrowid

            # Insertar relaciones muchos a muchos
            for sid in socio_ids:
                cursor.execute("INSERT INTO socio_credito (socio_id, credito_letra) VALUES (?, ?)", (sid, letra_id))

            # 2. CALCULAR LIQUIDACIÓN (LÓGICA ROBUSTA)
            cuota_base = None
            cuota_final = None

            for redondeo in [10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]:
                posible_cuota = round((capital / n_cuotas) / redondeo) * redondeo
                total_normales = posible_cuota * (n_cuotas - 1)
                ultima_cuota = capital - total_normales
                
                if 10000 <= ultima_cuota <= posible_cuota * 1.5:
                    cuota_base = posible_cuota
                    cuota_final = ultima_cuota
                    break

            if cuota_base is None:
                cuota_base = capital // n_cuotas
                cuota_final = capital - cuota_base * (n_cuotas - 1)

            # Generar filas
            cuotas_db = []
            saldo_temp = capital
            fecha_inicio_dt = date.today()
            
            for i in range(n_cuotas):
                nro = i + 1
                fecha_venc = fecha_inicio_dt + relativedelta(months=+nro)
                
                cuota_cap = cuota_final if i == n_cuotas - 1 else cuota_base
                interes_val = int(round(saldo_temp * interes_tasa))
                cuota_mensual = int(cuota_cap + interes_val)
                saldo_final = int(saldo_temp - cuota_cap)
                if saldo_final < 0: saldo_final = 0

                cuotas_db.append((
                    letra_id, nro, fecha_venc.strftime("%Y-%m-%d"),
                    int(cuota_cap), interes_val, cuota_mensual, saldo_final
                ))
                saldo_temp = saldo_final

            # 3. INSERTAR LIQUIDACIONES
            cursor.executemany("""
                INSERT INTO liquidaciones 
                (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, cuotas_db)

            # 4. ACTUALIZAR CAJA
            # Leer saldo actual de forma segura dentro de la transacción
            cursor.execute("SELECT value FROM config WHERE key='saldo_en_caja'")
            row = cursor.fetchone()
            saldo_actual = int(row['value']) if row else 0
            nuevo_saldo = saldo_actual - capital
            
            self.conn.commit()
            return letra_id, nuevo_saldo

        except Exception as e:
            self.conn.rollback()
            raise e  # Relanzar el error para que la UI lo muestre
        
        # Asegúrate de tener estos imports al inicio de db_manager.py
    

    # --- NUEVOS MÉTODOS PARA LÓGICA FINANCIERA ---

    def get_deuda_capital_actual(self, letra_id):
        """Calcula el saldo de capital pendiente real mirando la tabla."""
        try:
            cursor = self.conn.cursor()
            # Busca la primera cuota NO pagada
            cursor.execute("""
                SELECT valor_cuota, saldo_capital 
                FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NULL 
                ORDER BY nro_cuota ASC LIMIT 1
            """, (letra_id,))
            row = cursor.fetchone()
            
            if row:
                # Deuda = Saldo Final de esa cuota + Lo que amortiza esa cuota
                return row['saldo_capital'] + row['valor_cuota']
            else:
                # Si no hay pendientes, verifica el saldo final de la última pagada
                cursor.execute("SELECT saldo_capital FROM liquidaciones WHERE credito_letra = ? ORDER BY nro_cuota DESC LIMIT 1", (letra_id,))
                last = cursor.fetchone()
                return last['saldo_capital'] if last else 0
        except Exception as e:
            print(f"Error calculando deuda actual: {e}")
            return 0

    def recalcular_tabla_amortizacion(self, letra_id, abono_capital_recien_registrado):
        """
        Regenera la tabla de amortización tras un abono extra.
        Calcula el saldo por diferencia (Capital - Pagos) y respeta las cuotas vencidas.
        """
        try:
            cursor = self.conn.cursor()
            hoy = date.today().strftime("%Y-%m-%d")

            # 1. Obtener datos maestros
            cursor.execute("SELECT capital, interes, fecha_inicio FROM creditos WHERE letra = ?", (letra_id,))
            credito = cursor.fetchone()
            if not credito: return
            
            capital_original = credito['capital']
            tasa_interes = credito['interes']

            # 2. Calcular Pagos Realizados
            # A) Capital en cuotas normales
            cursor.execute("SELECT SUM(valor_cuota) FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NOT NULL", (letra_id,))
            pagado_cuotas = cursor.fetchone()[0] or 0

            # B) Abonos Extra (Buscamos 'abono_capital')
            cursor.execute("""
                SELECT SUM(monto) FROM detalle_recibo 
                WHERE credito_letra = ? AND tipo_operacion = 'abono_capital'
            """, (letra_id,))
            pagado_abonos = cursor.fetchone()[0] or 0

            # Saldo Real Nuevo
            saldo_real_nuevo = capital_original - pagado_cuotas - pagado_abonos

            # Si ya pagó todo
            if saldo_real_nuevo <= 0:
                cursor.execute("DELETE FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL", (letra_id,))
                self.conn.commit()
                return

            # 3. Respetar Vencidas (El Pasado)
            cursor.execute("""
                SELECT id, valor_cuota FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento < ?
            """, (letra_id, hoy))
            vencidas = cursor.fetchall()
            capital_en_vencidas = sum(v['valor_cuota'] for v in vencidas)
            
            capital_para_futuro = saldo_real_nuevo - capital_en_vencidas
            if capital_para_futuro < 0: capital_para_futuro = 0

            # 4. Borrar Futuro
            cursor.execute("""
                DELETE FROM liquidaciones 
                WHERE credito_letra = ? AND fecha_pago IS NULL AND fecha_vencimiento >= ?
            """, (letra_id, hoy))

            if capital_para_futuro == 0:
                self.conn.commit()
                return

            # 5. Regenerar Proyección
            # Cuota Base
            cursor.execute("SELECT valor_cuota FROM liquidaciones WHERE credito_letra = ? AND nro_cuota = 1", (letra_id,))
            row_base = cursor.fetchone()
            amortizacion_fija = row_base['valor_cuota'] if row_base else (capital_original // 10)

            # Fecha de arranque
            cursor.execute("SELECT nro_cuota, fecha_vencimiento FROM liquidaciones WHERE credito_letra = ? ORDER BY nro_cuota DESC LIMIT 1", (letra_id,))
            ultimo_reg = cursor.fetchone()
            
            nro_start = ultimo_reg['nro_cuota'] + 1 if ultimo_reg else 1
            fecha_start = datetime.strptime(ultimo_reg['fecha_vencimiento'], "%Y-%m-%d") if ultimo_reg else datetime.strptime(credito['fecha_inicio'][:10], "%Y-%m-%d")

            nuevas_cuotas = []
            saldo_iter = capital_para_futuro
            
            while saldo_iter > 0:
                fecha_start = fecha_start + relativedelta(months=+1)
                cap_pago = min(saldo_iter, amortizacion_fija)
                int_mes = int((saldo_iter + capital_en_vencidas) * tasa_interes)
                cuota_total = cap_pago + int_mes
                saldo_final_row = (saldo_iter - cap_pago) + capital_en_vencidas
                
                nuevas_cuotas.append((
                    letra_id, nro_start, fecha_start.strftime("%Y-%m-%d"),
                    int(cap_pago), int(int_mes), int(cuota_total), int(saldo_final_row)
                ))
                saldo_iter -= cap_pago
                nro_start += 1

            cursor.executemany("""
                INSERT INTO liquidaciones 
                (credito_letra, nro_cuota, fecha_vencimiento, valor_cuota, interes_mes, cuota_mensual, saldo_capital, interes_mora, mora_aplicada, notif_prev_enviada, notif_venc_enviada, fecha_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, NULL)
            """, nuevas_cuotas)

            self.conn.commit()
            print("✅ Tabla recalculada correctamente.")

        except Exception as e:
            print(f"❌ Error recalculando tabla: {e}")
            self.conn.rollback()