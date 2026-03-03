import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Создаем таблицы, если их еще нет"""
        with self.connection:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0.0,
                location TEXT DEFAULT 'Океан',
                bait TEXT DEFAULT 'Нет',
                last_fish_time TEXT,
                last_grid_time TEXT
            )""")
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                fish_name TEXT,
                count INTEGER DEFAULT 0,
                total_price REAL DEFAULT 0.0
            )""")

    def get_user(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def register_user(self, user_id, username):
        with self.connection:
            if not self.get_user(user_id):
                self.cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))

    def add_fish(self, user_id, fish_name, price):
        price = round(price, 1) 
        with self.connection:
            item = self.cursor.execute(
                "SELECT count FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                (user_id, fish_name)
            ).fetchone()
            if item:
                self.cursor.execute(
                    "UPDATE inventory SET count = count + 1, total_price = ROUND(total_price + ?, 1) "
                    "WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (price, user_id, fish_name)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO inventory (user_id, fish_name, count, total_price) VALUES (?, ?, 1, ?)", 
                    (user_id, fish_name, price)
                )

    def get_inventory(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT fish_name, count, total_price FROM inventory WHERE user_id = ?", (user_id,)).fetchall()

    def sell_all(self, user_id):
        with self.connection:
            res = self.cursor.execute("SELECT SUM(total_price) FROM inventory WHERE user_id = ?", (user_id,)).fetchone()
            total = round(res[0], 1) if res[0] else 0
            if total > 0:
                self.cursor.execute("UPDATE users SET balance = ROUND(balance + ?, 1) WHERE user_id = ?", (total, user_id))
                self.cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
            return total

    def get_top(self):
        with self.connection:
            return self.cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10").fetchall()
