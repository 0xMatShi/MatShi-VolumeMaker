from interface.output import show_menu
from interface.constants import MESSAGES, MAIN_MENU_OPTIONS
from interface.output import show_logo
from utils.wallets_creator.creator import creator
from utils.balance_checker.checker import checker
from utils.volume_maker.volumemaker import process


async def start():
    while True:
        show_logo()
        choice = await show_menu(MESSAGES[0], MAIN_MENU_OPTIONS)

        if choice == "Exit":
            return
        elif choice == "Create wallets":
            await creator()
        elif choice == "Check wallets balance":
            await checker()
        else:
            await process()