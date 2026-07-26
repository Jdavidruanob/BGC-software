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
                WHERE COALESCE(s.activo, 1) = 1
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
        except Exception as e:
            print(f"❌ Error obteniendo socios: {e}")
            return []

    def find_all_full(self):
        """Socios activos con sus tres cifras: aportes, deuda e intereses.

        - `saldo`          → lo que el socio tiene aportado (columna de socios).
        - `saldo_credito`  → lo que le falta por pagar sumando todas sus letras.
        - `intereses`      → lo que ya ha pagado de intereses en sus créditos.

        Las dos últimas se calculan con las MISMAS fórmulas que el tablero de
        datos usa para "Cartera por cobrar" e "Intereses recaudados", de modo
        que sumar la columna de todos los socios da exactamente el total del
        tablero. Si alguna de las dos definiciones cambia, hay que cambiarla en
        los dos sitios a la vez (ver `db/db_manager.py`).

        Un crédito puede tener varios socios. En ese caso el saldo y los
        intereses se reparten en partes iguales entre ellos: es la única forma
        de que la suma por socio siga cuadrando con el total, sin contar dos
        veces la misma deuda.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                WITH socios_por_letra AS (
                    SELECT credito_letra, COUNT(*) AS n
                    FROM socio_credito GROUP BY credito_letra
                ),
                -- Próxima cuota sin pagar de cada crédito: ahí está el saldo
                -- pendiente (capital restante + la cuota que sigue).
                prox AS (
                    SELECT credito_letra, MIN(nro_cuota) AS nro
                    FROM liquidaciones WHERE fecha_pago IS NULL
                    GROUP BY credito_letra
                ),
                deuda_por_socio AS (
                    SELECT sc.socio_id,
                           SUM((l.saldo_capital + l.valor_cuota)::numeric / spl.n) AS deuda
                    FROM prox p
                    JOIN liquidaciones l
                      ON l.credito_letra = p.credito_letra AND l.nro_cuota = p.nro
                    JOIN socio_credito sc ON sc.credito_letra = l.credito_letra
                    JOIN socios_por_letra spl ON spl.credito_letra = l.credito_letra
                    GROUP BY sc.socio_id
                ),
                intereses_por_socio AS (
                    SELECT sc.socio_id,
                           SUM(l.interes_mes::numeric / spl.n) AS intereses
                    FROM liquidaciones l
                    JOIN socio_credito sc ON sc.credito_letra = l.credito_letra
                    JOIN socios_por_letra spl ON spl.credito_letra = l.credito_letra
                    WHERE l.fecha_pago IS NOT NULL
                    GROUP BY sc.socio_id
                )
                SELECT s.*,
                       (SELECT COUNT(*) FROM socio_credito sc WHERE sc.socio_id = s.id)
                           AS creditos,
                       COALESCE(ROUND(d.deuda), 0)::bigint      AS saldo_credito,
                       COALESCE(ROUND(i.intereses), 0)::bigint  AS intereses
                FROM socios s
                LEFT JOIN deuda_por_socio d     ON d.socio_id = s.id
                LEFT JOIN intereses_por_socio i ON i.socio_id = s.id
                WHERE COALESCE(s.activo, 1) = 1
                ORDER BY s.nombres
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
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
                WHERE (s.nombres LIKE %s OR s.apellidos LIKE %s)
                  AND COALESCE(s.activo, 1) = 1
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
        except Exception as e:
            print(f"❌ Error en búsqueda de socios: {e}")
            return []

    def deactivate(self, socio_id):
        """Retira al socio (soft-delete): lo marca inactivo y le deja el saldo
        en 0. Conserva la fila y su historial, pero deja de aparecer en listados
        y búsquedas. No hace commit: lo maneja el servicio en su transacción."""
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE socios SET activo = 0, saldo = 0 WHERE id = %s", (socio_id,))

    def find_by_id(self, member_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, cc, nombres, apellidos, celular, saldo, photo_path, created_at
                FROM socios WHERE id = %s
            """, (member_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"❌ Error obteniendo datos del socio: {e}")
            return None

    def get_balance(self, member_id):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT saldo FROM socios WHERE id = %s", (member_id,))
            result = cursor.fetchone()
            return result["saldo"] if result else 0
        except Exception as e:
            print(f"❌ Error obteniendo saldo del socio {member_id}: {e}")
            return 0

    def save(self, nombres, apellidos, phone, photo_path, saldo=0):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO socios (nombres, apellidos, celular, photo_path, saldo)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombres, apellidos, phone, photo_path, saldo))
            self.db.conn.commit()
            print(f"✅ Socio '{nombres} {apellidos}' agregado correctamente.")
        except Exception as e:
            print(f"❌ Error agregando socio: {e}")

    def update(self, socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT saldo FROM socios WHERE id = %s", (socio_id,))
            if not cursor.fetchone():
                print("⚠️ Socio no encontrado.")
                return False
            cursor.execute("""
                UPDATE socios
                SET nombres = %s, apellidos = %s, celular = %s, photo_path = %s, saldo = %s
                WHERE id = %s
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

            cursor.execute("SELECT saldo FROM socios WHERE id = %s", (socio_id,))
            if not cursor.fetchone():
                print("⚠️ Socio no encontrado.")
                return False

            cursor.execute("SELECT credito_letra FROM socio_credito WHERE socio_id = %s", (socio_id,))
            letras = [row["credito_letra"] for row in cursor.fetchall()]

            cursor.execute("DELETE FROM socio_credito WHERE socio_id = %s", (socio_id,))

            for letra in letras:
                cursor.execute("SELECT COUNT(*) AS n FROM socio_credito WHERE credito_letra = %s", (letra,))
                if cursor.fetchone()["n"] == 0:
                    cursor.execute("DELETE FROM liquidaciones WHERE credito_letra = %s", (letra,))
                    cursor.execute("DELETE FROM creditos WHERE letra = %s", (letra,))
                    print(f"🗑️ Crédito #{letra} eliminado por no tener más socios.")

            cursor.execute("DELETE FROM detalle_recibo WHERE socio_id = %s", (socio_id,))
            cursor.execute("DELETE FROM recibos WHERE socio_id = %s", (socio_id,))
            cursor.execute("DELETE FROM socios WHERE id = %s", (socio_id,))

            self.db.conn.commit()
            print(f"🗑️ Socio con ID {socio_id} eliminado junto con datos relacionados.")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar socio: {e}")
            self.db.conn.rollback()
            return False

    def history_counts(self, socio_id):
        """Cuenta el historial de un socio (créditos, recibos y movimientos).
        Se usa para bloquear la eliminación de socios con historial y no dejar
        la base en estado inconsistente."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) AS n FROM socio_credito WHERE socio_id = %s", (socio_id,))
            creditos = cursor.fetchone()["n"]
            cursor.execute("SELECT COUNT(*) AS n FROM recibos WHERE socio_id = %s", (socio_id,))
            recibos = cursor.fetchone()["n"]
            cursor.execute("SELECT COUNT(*) AS n FROM detalle_recibo WHERE socio_id = %s", (socio_id,))
            movimientos = cursor.fetchone()["n"]
            return {"creditos": creditos, "recibos": recibos, "movimientos": movimientos}
        except Exception as e:
            print(f"❌ Error consultando historial del socio: {e}")
            # Ante la duda, reportar historial para NO permitir un borrado peligroso.
            return {"creditos": 1, "recibos": 1, "movimientos": 1}
