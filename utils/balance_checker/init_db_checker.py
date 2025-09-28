import sqlite3
import os
from InquirerPy import inquirer
from loguru import logger
from dotenv import load_dotenv


load_dotenv()
DB_PATH = os.getenv("DB_PATH")

async def get_wallets():
    if not os.path.exists(DB_PATH):
        logger.warning("\nWallets.db is not found.")
        input("\nPress any button to continue...")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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

    # --- достаём сразу имя группы и кошельки этой мета-группы ---
    cur.execute("""
        SELECT g.name, w.number, w.address
        FROM wallets w
        JOIN groups g ON w.group_id = g.id
        JOIN meta_group_links l ON l.group_id = g.id
        WHERE l.meta_group_id = ?
        ORDER BY g.name, w.number
    """, (meta_id,))
    wallets = cur.fetchall()
    conn.close()

    return meta_name, wallets
