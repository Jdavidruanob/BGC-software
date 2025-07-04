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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socios (
                    id INTEGER PRIMARY KEY,
                    cc TEXT UNIQUE,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    saldo INTEGER DEFAULT 0,
                    celular TEXT UNIQUE,
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creditos (
                    letra INTEGER PRIMARY KEY,
                    capital INTEGER NOT NULL,
                    interes REAL NOT NULL,
                    no_cuotas INTEGER NOT NULL,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS socio_credito (
                    socio_id INTEGER NOT NULL,
                    credito_letra INTEGER NOT NULL,
                    PRIMARY KEY (socio_id, credito_letra),
                    FOREIGN KEY (socio_id) REFERENCES socios(id),
                    FOREIGN KEY (credito_letra) REFERENCES creditos(letra)
                )
            """)

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aportes (
                    key TEXT PRIMARY KEY,
                    value TEXT
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

    def add_member(self, cc, nombres, apellidos, phone, photo_path):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO socios (cc, nombres, apellidos, celular, photo_path)
                VALUES (?, ?, ?, ?, ?)
            """, (cc, nombres, apellidos, phone, photo_path))
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