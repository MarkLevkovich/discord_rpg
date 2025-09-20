import sqlite3
from typing import Dict, Optional, List
import traceback

def connect(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(r'game.db')
        try:
            cur = conn.cursor()
            result = func(cur, *args, **kwargs)
            conn.commit()
        except:
            conn.rollback()
            traceback.print_exc()
            return result
        finally:
            conn.close()
        return result
    return wrapper

@connect
def init_db(cur) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            player_id TEXT UNIQUE,
            current_hp INTEGER,
            max_hp INTEGER,
            damage INTEGER
    )""")


if __name__=="__main__":
    init_db()