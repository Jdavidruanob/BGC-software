import sqlite3
from db.connection import DBConnection


class SociosRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def find_all(self):
        try:
            cursor = self.db.conn.cursor()
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
                primer_nombre = row["nombres"].split()[0]
                primer_apellido = row["apellidos"].split()[0]
                nombre_corto = f"{primer_nombre} {primer_apellido}"
                foto = row["photo_path"] or "assets/photos/default_user.png"
                creditos = row["creditos"]
                label = "Sin créditos activos" if creditos == 0 else f"{creditos} crédito(s) activo(s)"
                results.append((row["id"], nombre_corto, foto, label))
            return results
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo socios: {e}")
            return []

    def find_all_full(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT s.*, COUNT(sc.credito_letra) as creditos
                FROM socios s
                LEFT JOIN socio_credito sc ON s.id = sc.socio_id
                GROUP BY s.id
                ORDER BY s.nombres
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo socios completos: {e}")
            return []

    def search_by_name(self, search_term):
        try:
            cursor = self.db.conn.cursor()
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
                primer_nombre = row["nombres"].split()[0]
                primer_apellido = row["apellidos"].split()[0]
                nombre_corto = f"{primer_nombre} {primer_apellido}"
                foto = row["photo_path"] or "assets/photos/default_user.png"
                creditos = row["creditos"]
                label = "Sin créditos activos" if creditos == 0 else f"{creditos} crédito(s) activo(s)"
                results.append((row["id"], nombre_corto, foto, label))
            return results
        except sqlite3.Error as e:
            print(f"❌ Error en búsqueda de socios: {e}")
            return []

    def find_by_id(self, member_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, cc, nombres, apellidos, celular, saldo, photo_path, created_at
                FROM socios WHERE id = ?
            """, (member_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo datos del socio: {e}")
            return None

    def get_balance(self, member_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (member_id,))
            result = cursor.fetchone()
            return result["saldo"] if result else 0
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo saldo del socio {member_id}: {e}")
            return 0

    def save(self, nombres, apellidos, phone, photo_path, saldo=0):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO socios (nombres, apellidos, celular, photo_path, saldo)
                VALUES (?, ?, ?, ?, ?)
            """, (nombres, apellidos, phone, photo_path, saldo))
            self.db.conn.commit()
            print(f"✅ Socio '{nombres} {apellidos}' agregado correctamente.")
        except Exception as e:
            print(f"❌ Error agregando socio: {e}")

    def update(self, socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (socio_id,))
            if not cursor.fetchone():
                print("⚠️ Socio no encontrado.")
                return False
            cursor.execute("""
                UPDATE socios
                SET nombres = ?, apellidos = ?, celular = ?, photo_path = ?, saldo = ?
                WHERE id = ?
            """, (nombres, apellidos, phone, photo_path, nuevo_saldo, socio_id))
            self.db.conn.commit()
            print(f"✏️ Socio '{nombres} {apellidos}' actualizado correctamente.")
            return True
        except Exception as e:
            print(f"❌ Error actualizando socio: {e}")
            self.db.conn.rollback()
            return False

    def delete(self, socio_id):
        try:
            cursor = self.db.conn.cursor()

            cursor.execute("SELECT saldo FROM socios WHERE id = ?", (socio_id,))
            if not cursor.fetchone():
                print("⚠️ Socio no encontrado.")
                return False

            cursor.execute("SELECT credito_letra FROM socio_credito WHERE socio_id = ?", (socio_id,))
            letras = [row[0] for row in cursor.fetchall()]

            cursor.execute("DELETE FROM socio_credito WHERE socio_id = ?", (socio_id,))

            for letra in letras:
                cursor.execute("SELECT COUNT(*) FROM socio_credito WHERE credito_letra = ?", (letra,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM liquidaciones WHERE credito_letra = ?", (letra,))
                    cursor.execute("DELETE FROM creditos WHERE letra = ?", (letra,))
                    print(f"🗑️ Crédito #{letra} eliminado por no tener más socios.")

            cursor.execute("DELETE FROM detalle_recibo WHERE socio_id = ?", (socio_id,))
            cursor.execute("DELETE FROM recibos WHERE socio_id = ?", (socio_id,))
            cursor.execute("DELETE FROM socios WHERE id = ?", (socio_id,))

            self.db.conn.commit()
            print(f"🗑️ Socio con ID {socio_id} eliminado junto con datos relacionados.")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar socio: {e}")
            self.db.conn.rollback()
            return False
