import sqlite3


class DBConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
