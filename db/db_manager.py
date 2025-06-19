import sqlite3

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error:
            self.connection = None
            return False

    def close(self):
        if self.connection:
            self.connection.close()

    def create_tables(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS socios (
                    id INTEGER PRIMARY KEY,
                    cc TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.connection.commit()