from loguru import logger
from utils.volume_maker.start_trade import volume_trade
from interface.output import show_menu
from utils.init_db import get_meta
from interface.constants import MESSAGES, SELECT_MENU_OPTIONS



async def process():
    while True:
        # --- Ввод токена для торговли ---
        token_mint = input("Enter token mint address to trade: ").strip()
        if not token_mint:
            logger.warning("Token mint is empty. Cancelled.")
            return
        
        # --- Получаем кошельки для торговли ---
        choice = await show_menu(MESSAGES[1], SELECT_MENU_OPTIONS)
        if choice == "Exit":
            return
        
        groups, meta_name = await get_meta()
        logger.info(f"[+] Selected META-group: {meta_name}")
        if not groups:
            logger.error("No wallets to trade.")
            input("Press any button to continue...")
            return
        
        # --- Подтверждение ---
        ready = input("Are you ready to start making volume? (y/n): ").strip().lower()
        if ready != "y":
            logger.info("Cancelled by user.")
            return
        
        logger.info(
            f"[+] Starting volume trading in META-group '{meta_name}' "
            f"with token {token_mint}"
        )

        await volume_trade(groups, token_mint)