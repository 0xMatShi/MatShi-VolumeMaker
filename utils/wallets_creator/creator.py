import os
import sqlite3
import random
from interface.constants import MESSAGES
from interface.output import clear_console
from utils.init_db import init_db
from solders.keypair import Keypair
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

async def creator():
    clear_console()

    print(MESSAGES[2])
    # Инициализация базы данных
    init_db()



    try:
        groups_count = int(input("How many groups you want: ").strip())
        if groups_count <= 0:
            logger.warning("[-] Quantity must be > 0")
            return
    except ValueError:
        logger.error("[-] Incorrect value.")
        return
    
    try:
        min_w = int(input("Enter MIN number of wallets in group: ").strip())
        max_w = int(input("Enter MAX number of wallets in group: ").strip())
        if min_w <= 0 or max_w < min_w:
            logger.warning("[-] Incorrect range.")
            return
    except ValueError:
        logger.error("[-] Incorrect input.")
        return
    
    meta_name = input("Enter name for МЕТА-group(Press 'Enter' for cancel): ").strip()
    if meta_name == "":
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cur.execute("INSERT INTO meta_groups (name, created_at) VALUES (?, ?)",
                    (meta_name, created_at))
        meta_id = cur.lastrowid
    except sqlite3.IntegrityError:
        logger.error(f"[-] МЕТА-group '{meta_name}' already exists.")
        conn.close()
        return
    
    logger.info(f"\n[+] Creating {groups_count} groups within a meta group '{meta_name}'")
    
    for g in range(1, groups_count + 1):
        group_name = f"{meta_name}_G{g}"
        try:
            cur.execute("INSERT INTO groups (name, created_at) VALUES (?, ?)",
                        (group_name, created_at))
            group_id = cur.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"[!] Group '{group_name}' already exists, skipping.")
            continue

        # связываем группу с метагруппой
        cur.execute("INSERT INTO meta_group_links (meta_group_id, group_id) VALUES (?, ?)",
                    (meta_id, group_id))
        
        wallet_count = random.randint(min_w, max_w)
        wallets = []
        for i in range(wallet_count):
            kp = Keypair()
            address = str(kp.pubkey())
            privkey = kp.__str__()
            wallets.append((group_id, i + 1, address, privkey))

        cur.executemany("""
            INSERT INTO wallets (group_id, number, address, private_key)
            VALUES (?, ?, ?, ?)
        """, wallets)

        logger.info(f"[+] Group '{group_name}': created {wallet_count} wallets")

    conn.commit()
    conn.close()

    logger.success(f"\n[+] МЕТА-group '{meta_name}' was successfully created "
                f"and includes {groups_count} groups.")
    
    input("Press any button to return to the main menu...")



