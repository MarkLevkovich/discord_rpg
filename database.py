import sqlite3
from typing import Dict, Optional, List
import traceback
from game_data import locations


def connect(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(r"prikladnoi\sb_15_00\28_les\game.db")
        result = None
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

    cur.execute('''CREATE TABLE IF NOT EXISTS locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT UNIQUE,
            boss_name TEXT,
            boss_hp INTEGER,
            boss_dmg INTEGER,
            hp_bonus INTEGER,
            dmg_bonus INTEGER
        )''')

    cur.executemany('''INSERT OR IGNORE INTO locations
                          (location_name, boss_name, boss_hp, boss_dmg, hp_bonus, dmg_bonus)
                          VALUES (?, ?, ?, ?, ?, ?)''', locations)


@connect
def load_player(cur, player_id: str) -> Optional[Dict[str, int]]:
    cur.execute('''
        SELECT current_hp, max_hp, damage, current_location_id, passed_locations, current_boss_hp
        FROM players 
        WHERE player_id = ?
    ''', (player_id,))

    result = cur.fetchone()

    if result:
        return {
            'current_hp': result[0],
            'max_hp': result[1],
            'damage': result[2],
            'current_location_id': result[3],
            'passed_locs': result[4] if result[4] else '',
            'current_boss_hp': result[5]
        }
    return None


@connect
def save_player(cur, player_id: str, player_data: list) -> None:
    cur.execute('''
        INSERT OR REPLACE INTO players (player_id, current_hp, max_hp, damage, current_location_id, passed_locations, current_boss_hp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [player_id] + player_data)


@connect
def load_locations(cur, loc_id: int = None, loc_name: str = None) -> List[Dict]:
    sql = 'SELECT location_id, location_name, boss_name, boss_hp, boss_dmg FROM locations'
    params = ()

    if loc_id is not None:
        sql += ' WHERE location_id = ?'
        params = (loc_id,)
    elif loc_name:
        sql += ' WHERE location_name LIKE ? '
        params = (f"%{loc_name}%",)  # %деревня 🌾 Деревня, Деревня🌾, старая деревня у реки, город

    cur.execute(sql, params)
    result = cur.fetchall()

    keys = ['id', 'name', 'boss_name', 'boss_hp', 'boss_dmg', 'hp_bonus', 'dmg_bonus']
    return [dict(zip(keys, row)) for row in result]


@connect
def update_location(cur, player_id: str, loc_id: int) -> None:
    cur.execute('UPDATE players SET current_location_id = ? WHERE player_id = ?', (loc_id, player_id))


@connect
def update_current_boss_hp(cur, player_id: str, val: int) -> None:
    cur.execute('UPDATE players SET current_boss_hp = ? WHERE player_id = ?', (val, player_id))


@connect
def pass_location(cur, player_id: str, loc_id: int) -> None:
    cur.execute("SELECT passed_locations FROM players WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    passed_locations = result[0] if result[0] else ''
    passed_locs = passed_locations.split(',') if passed_locations else []
    if str(loc_id) not in passed_locs:
        passed_locations = passed_locations + (',' if passed_locations else '') + str(loc_id)
        cur.execute('UPDATE players SET passed_locations = ? WHERE player_id = ?', (passed_locations, player_id))


@connect
def add_bonus(cur, player_id: str, hp_bonus: int = 0, dmg_bonus: int = 0) -> None:
    cur.execute("""
        UPDATE players SET
        max_hp = max_hp + ?,
        damage = damage + ?,
        current_hp = max_hp + ?,
        current_boss_hp = 0
        WHERE player_id = ?
    """, (hp_bonus, dmg_bonus, hp_bonus, player_id))

@connect
def restore_hp(cur, player_id: str) -> None:
    cur.execute('UPDATE players SET current_hp = max_hp WHERE player_id = ?', (player_id,))

@connect
def delete_player(cur, player_id: str) -> None:
    cur.execute('DELETE FROM players WHERE player_id = ?', (player_id,))

@connect
def update_hp(cur, player_id: str, player_hp: int, boss_hp: int) -> None:
    cur.execute('UPDATE players SET current_hp = ?, current_boss_hp = ? WHERE player_id = ?', (player_hp, boss_hp, player_id))

@connect
def check_win(cur, passed_locs: str) -> bool:
    cur.execute('SELECT COUNT(*) FROM locations WHERE location_id != 1')
    total_locs = cur.fetchone()[0]
    passed_locs_list = passed_locs.split(",") if passed_locs else []
    return len([loc for loc in passed_locs_list if loc != "1"]) >= total_locs



if __name__ == "__main__":
    init_db()
    save_player(1, [100, 100, 15, 1, "", 0])
    # print(load_player(2))