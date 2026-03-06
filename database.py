import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
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
            # ТАБЛИЦА КОЛЛЕКЦИИ
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS collection (
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

    def add_fish(self, user_id, fish_name, price, table="inventory"):
        """Универсальная функция добавления рыбы в любую таблицу"""
        price = round(price, 1) 
        with self.connection:
            item = self.cursor.execute(
                f"SELECT count FROM {table} WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                (user_id, fish_name)
            ).fetchone()
            
            if item:
                self.cursor.execute(
                    f"UPDATE {table} SET count = count + 1, total_price = ROUND(total_price + ?, 1) "
                    f"WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (price, user_id, fish_name)
                )
            else:
                self.cursor.execute(
                    f"INSERT INTO {table} (user_id, fish_name, count, total_price) VALUES (?, ?, 1, ?)", 
                    (user_id, fish_name, price)
                )

    def move_to_collection(self, user_id, fish_name):
        """Перенос рыбы из инвентаря в коллекцию"""
        with self.connection:
            res = self.cursor.execute(
                "SELECT count, total_price FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE",
                (user_id, fish_name)
            ).fetchone()
            
            if not res or res[0] <= 0: return False
            
            price_one = round(res[1] / res[0], 1)
            
            # Убираем из инвентаря
            if res[0] > 1:
                self.cursor.execute(
                    "UPDATE inventory SET count = count - 1, total_price = ROUND(total_price - ?, 1) WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (price_one, user_id, fish_name)
                )
            else:
                self.cursor.execute(
                    "DELETE FROM inventory WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (user_id, fish_name)
                )
            
            # Добавляем в коллекцию
            self.add_fish(user_id, fish_name, price_one, table="collection")
            return True

    def remove_from_collection(self, user_id, fish_name):
        """Возврат рыбы из коллекции в инвентарь"""
        with self.connection:
            res = self.cursor.execute(
                "SELECT count, total_price FROM collection WHERE user_id = ? AND fish_name = ? COLLATE NOCASE",
                (user_id, fish_name)
            ).fetchone()
            
            if not res or res[0] <= 0: return False
            
            price_one = round(res[1] / res[0], 1)
            
            # Убираем из коллекции
            if res[0] > 1:
                self.cursor.execute(
                    "UPDATE collection SET count = count - 1, total_price = ROUND(total_price - ?, 1) WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (price_one, user_id, fish_name)
                )
            else:
                self.cursor.execute(
                    "DELETE FROM collection WHERE user_id = ? AND fish_name = ? COLLATE NOCASE", 
                    (user_id, fish_name)
                )
            
            # Возвращаем в инвентарь
            self.add_fish(user_id, fish_name, price_one, table="inventory")
            return True

    def get_inventory(self, user_id):
        """Получение инвентаря с красивой сортировкой по редкости и алфавиту"""
        with self.connection:
            query = """
                SELECT fish_name, count, total_price FROM inventory 
                WHERE user_id = ? 
                ORDER BY 
                    CASE 
                        WHEN fish_name LIKE '👑%' THEN 1
                        WHEN fish_name LIKE '🔸%' THEN 2
                        WHEN fish_name LIKE '🪵%' THEN 3
                        WHEN fish_name LIKE '🔹%' THEN 4
                        WHEN fish_name LIKE '🤢%' THEN 5
                        WHEN fish_name LIKE '🐢%' THEN 6
                        WHEN fish_name LIKE '🌶️%' THEN 7
                        ELSE 8 
                    END, 
                    fish_name ASC
            """
            return self.cursor.execute(query, (user_id,)).fetchall()

    def get_collection(self, user_id):
        """Получение коллекции с красивой сортировкой по редкости и алфавиту"""
        with self.connection:
            query = """
                SELECT fish_name, count, total_price FROM collection 
                WHERE user_id = ? 
                ORDER BY 
                    CASE 
                        WHEN fish_name LIKE '👑%' THEN 1
                        WHEN fish_name LIKE '🔸%' THEN 2
                        WHEN fish_name LIKE '🪵%' THEN 3
                        WHEN fish_name LIKE '🔹%' THEN 4
                        WHEN fish_name LIKE '🤢%' THEN 5
                        WHEN fish_name LIKE '🐢%' THEN 6
                        WHEN fish_name LIKE '🌶️%' THEN 7
                        ELSE 8 
                    END, 
                    fish_name ASC
            """
            return self.cursor.execute(query, (user_id,)).fetchall()

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
