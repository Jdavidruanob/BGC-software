import sqlite3

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acceder como diccionario
            return True
        except sqlite3.Error as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False

    def create_tables(self):
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

            # Tabla de liquidaciones: cada fila es una cuota programada
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
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            # Tabla de recibos (cabecera)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recibos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socio_id INTEGER NOT NULL,  -- quien entrega el dinero
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archivo_path TEXT,
                    FOREIGN KEY (socio_id) REFERENCES socios(id)
                )
            """)

            # Detalle de recibos (cada movimiento registrado)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_recibo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recibo_id INTEGER NOT NULL,
                    tipo_operacion TEXT NOT NULL CHECK (tipo_operacion IN ('aporte', 'pago_credito', 'retiro')),
                    socio_id INTEGER NOT NULL,  -- a quién aplica el movimiento
                    credito_letra INTEGER,      -- si es pago_credito
                    nro_cuota INTEGER,          -- si es pago_credito
                    monto INTEGER NOT NULL,
                    FOREIGN KEY (recibo_id) REFERENCES recibos(id),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            self.conn.commit()
            print("✅ Tablas creadas.")
        except sqlite3.Error as e:
            print(f"❌ Error creando tablas: {e}")


    def add_member(self, cc, nombres, apellidos, phone, photo_path, saldo=0):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO socios (cc, nombres, apellidos, celular, photo_path, saldo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cc, nombres, apellidos, phone, photo_path, saldo))
            self.conn.commit()
            print(f"✅ Socio '{nombres} {apellidos}' agregado correctamente.")
        except sqlite3.Error as e:
            print(f"❌ Error agregando socio: {e}")

    def get_all_members(self):
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
                GROUP BY s.id
                ORDER BY s.nombres
            """)
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
            print(f"❌ Error obteniendo socios: {e}")
            return []
        
    def get_all_members_full(self):
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
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo socios completos: {e}")
            return []

    def search_members_by_name(self, search_term):
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
        try:
            cursor = self.conn.cursor()

            # Asignar automáticamente un número de letra (id de crédito)
            cursor.execute("SELECT MAX(letra) FROM creditos")
            max_letra = cursor.fetchone()[0]
            new_letra = (max_letra or 0) + 1

            cursor.execute("""
                INSERT INTO creditos (letra, capital, interes, no_cuotas)
                VALUES (?, ?, ?, ?)
            """, (new_letra, capital, interes, no_cuotas))

            for socio_id in socio_ids:
                cursor.execute("""
                    INSERT INTO socio_credito (socio_id, credito_letra)
                    VALUES (?, ?)
                """, (socio_id, new_letra))

            self.conn.commit()
            print(f"✅ Crédito #{new_letra} creado exitosamente.")
            return True
        except Exception as e:
            print(f"❌ Error al crear crédito: {e}")
            return False
    def delete_member(self, member_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM socios WHERE id = ?", (member_id,))
            self.conn.commit()
            print(f"✅ Socio con ID {member_id} eliminado correctamente.")
            return True
        except sqlite3.Error as e:
            print(f"❌ Error eliminando socio: {e}")
            return False
        
    def update_member(self, member_id, nombres, apellidos, cc, phone, photo_path, saldo):
    
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE socios
                SET nombres = ?, apellidos = ?, cc = ?, celular = ?, photo_path = ?, saldo = ?
                WHERE id = ?
            """, (nombres, apellidos, cc, phone, photo_path, saldo, member_id))
            self.conn.commit()
            print(f"✅ Socio con ID {member_id} actualizado correctamente.")
            return True
        except sqlite3.Error as e:
            print(f"❌ Error actualizando socio: {e}")
            return False
        
    def get_auxiliary_operations(self, limit=10, offset=0):
        operaciones = [
            {"fecha": "2025-01-15", "tipo": "Aporte", "socio": "Carlos Pérez", "numero": 1001, "monto": 100000, "saldo": 1200000},
            {"fecha": "2025-01-17", "tipo": "Nuevo Credito", "socio": "Nathalia Burbano", "numero": 3, "monto": 1500000, "saldo": 0},
            {"fecha": "2025-02-01", "tipo": "Pago Credito", "socio": "Carlos Pérez", "numero": 1002, "monto": 125000, "saldo": 1075000},
            {"fecha": "2025-02-01", "tipo": "Aporte", "socio": "Lucía Gómez", "numero": 1003, "monto": 50000, "saldo": 200000},
            {"fecha": "2025-02-05", "tipo": "Pago Credito", "socio": "Nathalia Burbano", "numero": 1004, "monto": 125000, "saldo": 1375000},
            {"fecha": "2025-02-07", "tipo": "Aporte", "socio": "Carlos Pérez", "numero": 1005, "monto": 80000, "saldo": 1150000},
            {"fecha": "2025-02-10", "tipo": "Retiro", "socio": "Lucía Gómez", "numero": 1006, "monto": -70000, "saldo": 193000},
        ]
        start = offset
        end = offset + limit
        return operaciones[start:end]

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
