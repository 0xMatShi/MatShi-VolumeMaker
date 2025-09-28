import os
from InquirerPy import inquirer

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def show_logo():
    # Очищаем экран
    clear_console()

    blue = "\033[96m"
    white = "\033[97m"
    reset = "\033[0m"

    logo_text = rf"""
    {blue}
    ███╗   ███╗ █████╗ ████████╗███████╗██╗  ██╗██╗
    ████╗ ████║██╔══██╗╚══██╔══╝██╔════╝██║  ██║██║
    ██╔████╔██║███████║   ██║   ███████╗███████║██║██████╗
    ██║╚██╔╝██║██╔══██║   ██║   ╚════██║██╔══██║██║╚═════╝
    ██║ ╚═╝ ██║██║  ██║   ██║   ███████║██║  ██║██║
    ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝{reset}
    {white}              MatShi- Volume-Maker{reset}
    """
    print(logo_text)


async def show_menu(message, choices):
    """
    Shows main menu interface
    """
    choice = await inquirer.select(
        message=message,
        choices=choices
    ).execute_async()
    return choice