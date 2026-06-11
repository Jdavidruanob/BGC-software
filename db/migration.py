import sqlite3
from db.connection import DBConnection
from db.schema import SchemaManager


class MigrationService:
    def __init__(self, db: DBConnection, schema: SchemaManager):
        self.db = db
        self.schema = schema

    def run_annual_migration(self, prev_db_path):
        print(f"\n⏳ Iniciando migración de datos desde: {prev_db_path}")

        try:
            prev_conn = sqlite3.connect(prev_db_path)
            prev_cursor = prev_conn.cursor()
        except sqlite3.Error as e:
            print(f"❌ ERROR: No se pudo conectar a la DB anterior ({prev_db_path}). {e}")
            return

        current_cursor = self.db.conn.cursor()

        try:
            socios_to_migrate = prev_cursor.execute("""
                SELECT id, cc, nombres, apellidos, saldo, celular, photo_path, created_at
                FROM socios
            """).fetchall()

            if socios_to_migrate:
                current_cursor.executemany("""
                    INSERT INTO socios (id, cc, nombres, apellidos, saldo, celular, photo_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, socios_to_migrate)
                print(f"   ✅ {len(socios_to_migrate)} socios y saldos migrados.")

            saldo_caja = prev_cursor.execute(
                "SELECT key, value FROM config WHERE key = 'saldo_en_caja'"
            ).fetchone()

            if saldo_caja:
                current_cursor.execute(
                    "INSERT INTO config (key, value) VALUES (?, ?)",
                    (saldo_caja[0], saldo_caja[1]),
                )
                print("   ✅ Saldo de caja migrado.")

            current_cursor.execute(
                "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
                ("total_admin", "0"),
            )

            active_credits = prev_cursor.execute(
                "SELECT DISTINCT credito_letra FROM liquidaciones WHERE fecha_pago IS NULL"
            ).fetchall()
            active_credit_ids = [c[0] for c in active_credits]

            if active_credit_ids:
                placeholders = ",".join(map(str, active_credit_ids))

                credits_to_migrate = prev_cursor.execute(
                    f"SELECT letra, capital, interes, no_cuotas, fecha_inicio FROM creditos WHERE letra IN ({placeholders})"
                ).fetchall()
                current_cursor.executemany(
                    "INSERT INTO creditos (letra, capital, interes, no_cuotas, fecha_inicio) VALUES (?, ?, ?, ?, ?)",
                    credits_to_migrate,
                )
                print(f"   ✅ {len(active_credit_ids)} créditos activos migrados.")

                relations_to_migrate = prev_cursor.execute(
                    f"SELECT socio_id, credito_letra FROM socio_credito WHERE credito_letra IN ({placeholders})"
                ).fetchall()
                current_cursor.executemany(
                    "INSERT INTO socio_credito (socio_id, credito_letra) VALUES (?, ?)",
                    relations_to_migrate,
                )

                liquidations_to_migrate = prev_cursor.execute(f"""
                    SELECT credito_letra, nro_cuota, fecha_vencimiento, valor_cuota,
                           interes_mes, cuota_mensual, saldo_capital, fecha_pago
                    FROM liquidaciones
                    WHERE credito_letra IN ({placeholders})
                """).fetchall()
                current_cursor.executemany("""
                    INSERT INTO liquidaciones (credito_letra, nro_cuota, fecha_vencimiento,
                        valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_pago)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, liquidations_to_migrate)
                print("   ✅ Liquidaciones completas migradas.")

            self.schema.set_sequence_start_value("recibos", 230)
            self.schema.set_sequence_start_value("creditos", 437)

            self.db.conn.commit()
            print("🎉 Migración de año fiscal completada.")

        except sqlite3.Error as e:
            self.db.conn.rollback()
            print(f"❌ ERROR durante la migración. Se revertieron los cambios: {e}")
        finally:
            prev_conn.close()
