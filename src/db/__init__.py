import os
import sqlite3

from src import logger


def connect():
    """Подключение к БД"""
    try:
        connection = sqlite3.connect(os.getenv("DB_URL"), check_same_thread=False)
        logger.info("БД успешно подключена!")

        return connection
    except sqlite3.DatabaseError:
        logger.error("Не удалось подключить БД.")


def check(conn, cur):
    """Проверка на существование таблицы"""

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        vk_user_id INT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        patronymic TEXT,
        age TEXT,
        school_name TEXT,
        class_name TEXT,
        CODE TEXT);
    """)
    conn.commit()


def execute(conn, cur, query, fmt):
    cur.execute(query, fmt)
    conn.commit()


def fetchall(cur, query):
    cur.execute(query)
    return cur.fetchall()


def fetchone(cur, query, fmt=None):
    cur.execute(query, fmt)
    return cur.fetchone()
