import os
import sqlite3
from InquirerPy import inquirer
from loguru import logger
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def init_db():
    os.makedirs("./data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- таблицы обычных групп и кошельков
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            number INTEGER,
            address TEXT,
            private_key TEXT,
            FOREIGN KEY(group_id) REFERENCES groups(id)
        )
    """)

    # --- новая таблица МЕТА-групп
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_at TEXT
        )
    """)

    # --- связь между МЕТА-группами и обычными группами
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta_group_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meta_group_id INTEGER,
            group_id INTEGER,
            FOREIGN KEY(meta_group_id) REFERENCES meta_groups(id),
            FOREIGN KEY(group_id) REFERENCES groups(id)
        )
    """)

    conn.commit()
    conn.close()

async def get_meta():
    """
    Возвращает:
        meta_name: str  – имя выбранной мета-группы
        groups: dict    – { 'GroupName': [(address, privkey), ...], ... }
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Выбор мета-группы ---
    cur.execute("SELECT id, name FROM meta_groups")
    meta_groups = cur.fetchall()

    if not meta_groups:
        logger.warning("\nNo Meta-groups in database.")
        conn.close()
        input("\nPress any button to continue...")
        return

    meta_choices = [f"{name} (ID: {mid})" for mid, name in meta_groups]
    meta_choice = await inquirer.select(
        message="Meta-groups:",
        choices=meta_choices,
    ).execute_async()

    meta_id, meta_name = meta_groups[meta_choices.index(meta_choice)]

    # --- получаем список групп внутри этой мета-группы ---
    cur.execute("""
        SELECT g.id, g.name
        FROM groups g
        JOIN meta_group_links l ON l.group_id = g.id
        WHERE l.meta_group_id = ?
    """, (meta_id,))
    linked_groups = cur.fetchall()

    if not linked_groups:
        logger.warning(f"\nMETA-group '{meta_name}' has no linked groups.")
        conn.close()
        input("\nPress any button to continue...")
        return {}, meta_name
    
    # --- собираем кошельки по группам ---
    groups = {}
    for gid, gname in linked_groups:
        cur.execute("""
            SELECT w.address, w.private_key
            FROM wallets w
            WHERE w.group_id = ?
        """, (gid,))
        wallets = cur.fetchall()
        if wallets:
            groups[gname] = wallets

    conn.close()

    return groups, meta_name


