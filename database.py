import sqlite3
from typing import Dict, Optional, List
import traceback
from game_data import locations


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
            damage INTEGER,
            current_location_id INTEGER,
            passed_locations TEXT,
            current_boss_hp INTEGER,
            FOREIGN KEY (current_location_id) REFERENCES locations(location_id)
    )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT UNIQUE,
            boss_name TEXT,
            boss_hp INTEGER,
            boss_dmg INTEGER
    )""")

    cur.executemany('''INSERT OR IGNORE INTO locations
                              (location_name, boss_name, boss_hp, boss_dmg)
                              VALUES (?, ?, ?, ?)''', locations)

@connect
def load_players(cur, player_id: str) -> Optional[Dict[str, int]]:
    cur.execute("""
        SELECT current_hp, max_hp, damage
        FROM players
        WHERE player_id = ?
    """, (player_id,))

    result = cur.fetchone()

    if result:
        return {'current_hp': result[0], 'max_hp': result[1], 'damage': result[2]}
    return None



@connect
def save_player(cur, player_id: str, player_data: list) -> None:
    cur.execute("""
        INSERT OR REPLACE INTO players (player_id, current_hp, max_hp, damage)
        VALUES (?,?,?,?)
    """, [player_id] + player_data)



if __name__=="__main__":
    init_db()
    # print(load_players(1))
    # save_player(2, [100,100,50])