import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import random
from loguru import logger
from utils.volume_maker.transaction import (
    get_quote, 
    get_swap_tx, 
    sign_and_send_swap, 
    get_token_balance, 
    get_sol_balance
)
from interface.constants import SOL_MINT


load_dotenv()
RPC_URL = os.getenv("RPC_URL")


async def trade_group(session, group_name, wallets, token_mint):
    logger.info(f"[{group_name}] Starting trading loop")

    # ---- 1. Первая закупка на всех кошельках ----
    first_wave = wallets[:]          # копия списка
    random.shuffle(first_wave)       # перемешиваем порядок

    for addr, pk in first_wave:
        delay = random.uniform(7, 15)
        logger.info(f"[{group_name}] First buy scheduled: {addr} in {delay:.1f}s")
        await asyncio.sleep(delay)
        await buy_token(session, addr, pk, token_mint)

    logger.info(f"[{group_name}] Initial BUY done")

    # ---- 2. Бесконечный цикл BUY/SELL ----
    while True:
        # выбираем случайный кошелёк этой группы
        addr, pk = random.choice(wallets)

        # рандомно решаем продавать или покупать
        if random.random() < 0.5:
            # Продажа 51–91% (нужен баланс токена)
            sell_pct = random.uniform(0.51, 0.91)
            await sell_token(session, addr, pk, token_mint, sell_pct)
        else:
            # Допокупка на рандомный объём SOL
            await buy_token(session, addr, pk, token_mint)

        # пауза между действиями
        pause = random.uniform(7, 53)
        logger.info(f"[{addr}] Next action in {pause} seconds...")
        await asyncio.sleep(pause)


async def buy_token(session, address, privkey, token_mint):
    """
    Покупает токен на процент от текущего SOL-баланса
    """
    try:
        sol_balance = await get_sol_balance(session, address)
        logger.debug(f"[{address}] Current SOL balance: {sol_balance:.6f} SOL")
        if sol_balance == 0:
            logger.warning(f"[{address}] No SOL balance to buy.")
            return
        
        safe_balance = int(sol_balance * 0.99)
        

        # --- Покупаем от x% до x% от баланса SOL
        pct = random.uniform(0.30, 0.70)
        lamports = int(safe_balance * pct)
        amount_sol = lamports / 1_000_000_000
        logger.info(f"[{address}] BUY {pct*100:.1f}% of SOL (~{amount_sol:.4f} SOL)")

        logger.debug(f"[{address}] Requesting BUY quote...")
        quote = await get_quote(session, SOL_MINT, token_mint, lamports)
        logger.debug(f"[{address}] BUY Quote received")

        logger.debug(f"[{address}] Requesting BUY-swap transaction...")
        swap_resp = await get_swap_tx(session, quote, address)
        logger.debug(f"[{address}] BUY-swap transaction ready")

        signed_rpc_resp = await sign_and_send_swap(session, swap_resp["swapTransaction"], privkey)

        if "result" in signed_rpc_resp and signed_rpc_resp["result"]:
            logger.success(f"[{address}] ✅ BUY SUCCESS – TX: https://solscan.io/tx/{signed_rpc_resp['result']}")
        else:
            logger.error(f"[{address}] ❌ BUY RPC error: {signed_rpc_resp}")


    except Exception as e:
        logger.error(f"[BUY] {address} ERROR: {e}")


async def sell_token(session, address, privkey, token_mint, sell_pct):
    try:
        # узнаём баланс токена
        balance = await get_token_balance(session, address, token_mint)
        logger.debug(f"[{address}] Current token balance: {balance}")
        if balance == 0:
            logger.warning(f"[{address}] No token balance to sell.")
            return
        
        amount = int(balance * sell_pct)
        logger.info(f"[{address}] SELL {sell_pct*100:.1f}% (~{amount} raw units)")

        logger.debug(f"[{address}] Requesting SELL quote...")
        quote = await get_quote(session, token_mint, SOL_MINT, amount)
        logger.debug(f"[{address}] SELL-quote received")

        logger.debug(f"[{address}] Requesting SELL-swap transaction...")
        swap_resp = await get_swap_tx(session, quote, address)
        logger.debug(f"[{address}] SELL-swap transaction ready")

        signed_rpc_resp = await sign_and_send_swap(session, swap_resp["swapTransaction"], privkey)

        if "result" in signed_rpc_resp and signed_rpc_resp["result"]:
            logger.success(f"[{address}] ✅ SELL SUCCESS – TX: https://solscan.io/tx/{signed_rpc_resp['result']}")
        else:
            logger.error(f"[{address}] ❌ SELL RPC error: {signed_rpc_resp}")

    except Exception as e:
        logger.error(f"[SELL] {address} ERROR: {e}")


async def volume_trade(meta_groups: dict[str, list[tuple[str,str]]], token_mint: str):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for group_name, wallets in meta_groups.items():
            tasks.append(asyncio.create_task(
                trade_group(session, group_name, wallets, token_mint)
            ))
        await asyncio.gather(*tasks)