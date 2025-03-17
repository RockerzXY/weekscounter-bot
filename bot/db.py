import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """Создание таблиц, если они не существуют."""
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT UNIQUE,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    custom_name VARCHAR(255),
                    birthdate DATE,
                    handshake TIMESTAMP,
                    notify_day SMALLINT,
                    notify_time TIME,
                    last_notification DATE
                )
            """)

    def user_exists(self, user_id):
        """Проверка существования пользователя."""
        with self.connection:
            result = self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return bool(result)

    def add_user(self, user_id, username, full_name, custom_name, birthdate, notify_day, notify_time):
        """Добавление нового пользователя."""
        handshake = datetime.now()
        with self.connection:
            self.cursor.execute("""
                INSERT INTO users (user_id, username, full_name, custom_name, birthdate, handshake, notify_day, notify_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, custom_name, birthdate, handshake, notify_day, notify_time))

    def update_user(self, user_id, custom_name=None, birthdate=None, notify_day=None, notify_time=None):
        """Обновление данных пользователя."""
        with self.connection:
            if custom_name:
                self.cursor.execute("UPDATE users SET custom_name = ? WHERE user_id = ?", (custom_name, user_id))
            if birthdate:
                self.cursor.execute("UPDATE users SET birthdate = ? WHERE user_id = ?", (birthdate, user_id))
            if notify_day:
                self.cursor.execute("UPDATE users SET notify_day = ? WHERE user_id = ?", (notify_day, user_id))
            if notify_time:
                self.cursor.execute("UPDATE users SET notify_time = ? WHERE user_id = ?", (notify_time, user_id))

    def update_birthdate(self, user_id, birthdate):
        """Обновление даты рождения пользователя."""
        with self.connection:
            self.cursor.execute("UPDATE users SET birthdate = ? WHERE user_id = ?", (birthdate, user_id))

    def update_notification_settings(self, user_id, notify_day, notify_time):
        """Обновление настроек уведомлений."""
        with self.connection:
            self.cursor.execute("UPDATE users SET notify_day = ?, notify_time = ? WHERE user_id = ?", (notify_day, notify_time, user_id))

    def update_last_notification(self, user_id, date):
        """Обновление даты последнего уведомления."""
        with self.connection:
            self.cursor.execute("UPDATE users SET last_notification = ? WHERE user_id = ?", (date, user_id))

    def get_user_info(self, user_id):
        """Получение информации о пользователе."""
        with self.connection:
            result = self.cursor.execute(
                "SELECT custom_name, birthdate, notify_day, notify_time FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            if result:
                return {
                    "custom_name": result[0],
                    "birthdate": result[1],
                    "notify_day": result[2],
                    "notify_time": result[3]
                }
            return None

    def get_all_users(self):
        """Получение списка всех пользователей."""
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM users").fetchall()
            return [row[0] for row in result]

    def delete_user(self, user_id):
        """Удаление пользователя."""
        with self.connection:
            self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def close(self):
        """Закрытие соединения с базой данных."""
        self.connection.close()
