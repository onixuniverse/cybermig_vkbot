def check(conn, cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        vk_user_id INT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        patronymic TEXT,
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
