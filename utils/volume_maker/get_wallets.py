from interface.constants import MESSAGES, SELECT_MENU_OPTIONS
from interface.output import show_menu
from utils.init_db import get_meta

async def get_wallets():
    while True:
        choice = await show_menu(MESSAGES[1], SELECT_MENU_OPTIONS)

        if choice == "Exit":
            return

        # --- выбор мета-группы ---
        
        groups, meta_name = await get_meta()

        return groups, meta_name

