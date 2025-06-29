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
                    socio_id INTEGER NOT NULL,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (socio_id) REFERENCES socios(id)
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
                       COUNT(c.letra) as creditos
                FROM socios s
                LEFT JOIN creditos c ON s.id = c.socio_id
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
