import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        with self.connection:
            # Таблица юзеров (добавили время последней сетки)
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0.0,
                location TEXT DEFAULT 'Океан',
                bait TEXT DEFAULT 'Нет',
                last_fish_time TEXT,
                last_net_time TEXT
            )""")
            # Таблица инвентаря (теперь каждая рыба — отдельная строка с ID)
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                fish_name TEXT,
                weight REAL,
                price REAL
            )""")
            # Таблица коллекции (твои трофеи)
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS collection (
                user_id INTEGER,
                fish_name TEXT,
                weight REAL
            )""")

    def get_user(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def register_user(self, user_id, username):
        with self.connection:
            if not self.get_user(user_id):
                self.cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))

    def add_fish(self, user_id, fish_name, weight, price):
        with self.connection:
            # Теперь просто добавляем новую строку для каждой рыбы
            self.cursor.execute("INSERT INTO inventory (user_id, fish_name, weight, price) VALUES (?, ?, ?, ?)", 
                                (user_id, fish_name, weight, price))

    def get_inventory(self, user_id):
        with self.connection:
            # Возвращаем ID, имя и цену для вывода в меню
            return self.cursor.execute("SELECT id, fish_name, weight, price FROM inventory WHERE user_id = ?", (user_id,)).fetchall()

    def add_to_collection(self, user_id, fish_id):
        with self.connection:
            # Берем рыбу из инвентаря
            fish = self.cursor.execute("SELECT fish_name, weight FROM inventory WHERE id = ? AND user_id = ?", (fish_id, user_id)).fetchone()
            if fish:
                # Переносим в коллекцию и удаляем из инвентаря
                self.cursor.execute("INSERT INTO collection (user_id, fish_name, weight) VALUES (?, ?, ?)", (user_id, fish[0], fish[1]))
                self.cursor.execute("DELETE FROM inventory WHERE id = ?", (fish_id,))
                return True
            return False

    def get_collection(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT fish_name, weight FROM collection WHERE user_id = ?", (user_id,)).fetchall()

    def sell_all(self, user_id):
        with self.connection:
            res = self.cursor.execute("SELECT SUM(price) FROM inventory WHERE user_id = ?", (user_id,)).fetchone()
            total = res[0] if res[0] else 0
            if total > 0:
                self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total, user_id))
                self.cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
            return round(total, 1)

    def get_top(self):
        with self.connection:
            # ТОП-10: Наличка + Стоимость всех рыб в сумке + Очки за коллекцию
            query = """
            SELECT u.username, 
            ROUND(u.balance + 
            COALESCE((SELECT SUM(price) FROM inventory WHERE user_id = u.user_id), 0) +
            COALESCE((SELECT SUM(weight * 5) FROM collection WHERE user_id = u.user_id), 0), 1) as total_wealth
            FROM users u
            ORDER BY total_wealth DESC
            LIMIT 10
            """
            return self.cursor.execute(query).fetchall()

    def transfer_fish(self, from_user_id, to_user_id, fish_id):
        with self.connection:
            # Меняем владельца рыбы в базе
            res = self.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ? AND user_id = ?", 
                                      (to_user_id, fish_id, from_user_id))
            return res.rowcount > 0
