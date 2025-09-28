import os
import sqlite3
from tabulate import tabulate
from InquirerPy import inquirer
from loguru import logger
import aiohttp
import asyncio
from interface.output import clear_console, show_menu
from interface.constants import MESSAGES, SELECT_MENU_OPTIONS
from utils.balance_checker.init_db_checker import get_wallets
from dotenv import load_dotenv

load_dotenv()
RPC_URL = os.getenv("RPC_URL")

# === Get Balance func ===
async def get_balance_async(session, pubkey: str) -> float:
    """Асинхронный запрос баланса через Solana RPC"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [pubkey]
    }
    try:
        async with session.post(RPC_URL, json=payload) as resp:
            data = await resp.json()
            lamports = data.get("result", {}).get("value", 0)
            return lamports / 1_000_000_000
    except Exception as e:
        return f"Ошибка: {e}"

# === Checker func ===
async def checker():
    while True:
        clear_console()
        choice = await show_menu(MESSAGES[3], SELECT_MENU_OPTIONS)

        if choice == "Exit":
            return

        meta_name, wallets = await get_wallets()

        if not wallets:
            logger.warning(f"\nMeta-group '{meta_name}' has no wallets.")
            input("\nPress any button to continue...")
            continue

        # --- асинхронно получаем балансы ---
        async def fetch_all():
            async with aiohttp.ClientSession() as session:
                tasks = [get_balance_async(session, addr) for _, _, addr in wallets]
                return await asyncio.gather(*tasks)

        balances = await fetch_all()

        # --- красиво группируем вывод ---
        grouped_table = []
        current_group = None
        for (grp_name, num, addr), bal in zip(wallets, balances):
            if grp_name != current_group:
                grouped_table.append([f"[{grp_name}]", "", ""])
                current_group = grp_name
            grouped_table.append([num, addr, bal])

        logger.info(
            f"\n\nBalances of wallets (Meta-group '{meta_name}'):\n"
            + tabulate(
                grouped_table,
                headers=["№ / Group", "Address", "Balance (SOL)"],
                tablefmt="pretty"
            )
        )

        input("\nPress any button to continue...")