from db.connection import DBConnection


class ConfigRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def get(self, key):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None
        except Exception:
            return None

    def get_int(self, key):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return int(row["value"]) if row else 0

    def set(self, key, value):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO config (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        self.db.conn.commit()
