from dotenv import load_dotenv
load_dotenv()

import sys
import json
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from app.service.git import check_for_updates
from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance, get_tiering_info
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import (
    fetch_my_packages,
    get_packages_by_family,
    show_package_details,
)
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import (
    show_family_list_menu,
    show_store_packages_menu,
)
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil


console = Console()
LAST_CHOICE = None
THEME = "dark"  # dark | minimal


THEMES = {
    "dark": {
        "panel": "neon_cyan",
        "title": "neon_pink",
        "key": "neon_cyan",
        "menu": "bold white",
        "warn": "bold red",
    },
    "minimal": {
        "panel": "white",
        "title": "bold white",
        "key": "bold white",
        "menu": "white",
        "warn": "bold red",
    },
}


def t(key):
    return THEMES[THEME][key]


def print_panel(content, title):
    console.print(
        Panel(
            Align.left(content),
            title=f"[{t('title')}]{title}[/]",
            border_style=t("panel"),
            padding=(1, 2),
        )
    )


def show_main_menu(profile):
    clear_screen()

    expired_at = datetime.fromtimestamp(
        profile["balance_expired_at"]
    ).strftime("%Y-%m-%d")

    profile_table = Table(show_header=False, box=None, padding=(0, 2))
    profile_table.add_column("Key", style=t("key"), justify="right", width=12)
    profile_table.add_column("Value", style="bold white")

    profile_table.add_row("Nomor", profile["number"])
    profile_table.add_row("Type", profile["subscription_type"])
    profile_table.add_row("Pulsa", f"Rp {profile['balance']}")
    profile_table.add_row("Aktif s/d", expired_at)
    profile_table.add_row("Info", profile["point_info"])

    print_panel(profile_table, "USER PROFILE")

    menu = Table(show_header=True, box=None, padding=(0, 1))
    menu.add_column("ID", style="bold green", justify="right", width=4)
    menu.add_column("MENU", style=t("menu"))

    menu.add_row("1", "Login / Ganti Akun")
    menu.add_row("2", "Lihat Paket Saya")
    menu.add_row("3", "🔥 HOT Package")
    menu.add_row("4", "🔥 HOT Package 2")
    menu.add_row("5", "Beli Paket (Option Code)")
    menu.add_row("6", "Beli Paket (Family Code)")
    menu.add_row(
        "7",
        f"[{t('warn')}]⚠ AUTO BUY LOOP (BERBAHAYA)[/]",
    )
    menu.add_row("8", "Riwayat Transaksi")
    menu.add_row("9", "Family Plan / Akrab")
    menu.add_row("10", "Circle")
    menu.add_row("11", "Store Segments")
    menu.add_row("12", "Store Family List")
    menu.add_row("13", "Store Packages")
    menu.add_row("14", "Redeemables")
    menu.add_row("00", "Bookmark Paket")
    menu.add_row("T", "Switch Theme (Dark / Minimal)")
    menu.add_row("99", "Keluar Aplikasi")

    print_panel(menu, "MAIN MENU")
    console.print("[bold cyan]Pilih menu (ENTER = ulang terakhir) ➜ [/]", end="")



def main():
    global LAST_CHOICE, THEME

    while True:
        user = AuthInstance.get_active_user()

        if user:
            balance = get_balance(
                AuthInstance.api_key,
                user["tokens"]["id_token"],
            )

            point_info = "Points: N/A | Tier: N/A"
            if user["subscription_type"] == "PREPAID":
                tier = get_tiering_info(
                    AuthInstance.api_key,
                    user["tokens"],
                )
                point_info = f"Points: {tier.get('current_point')} | Tier: {tier.get('tier')}"

            profile = {
                "number": user["number"],
                "subscriber_id": user["subscriber_id"],
                "subscription_type": user["subscription_type"],
                "balance": balance.get("remaining"),
                "balance_expired_at": balance.get("expired_at"),
                "point_info": point_info,
            }

            show_main_menu(profile)
            choice = input().strip()

            if not choice and LAST_CHOICE:
                choice = LAST_CHOICE
            else:
                LAST_CHOICE = choice

            if choice == "1":
                sel = show_account_menu()
                if sel:
                    AuthInstance.set_active_user(sel)

            elif choice == "2":
                fetch_my_packages()

            elif choice == "3":
                show_hot_menu()

            elif choice == "4":
                show_hot_menu2()

            elif choice == "5":
                code = input("Option code: ")
                show_package_details(
                    AuthInstance.api_key,
                    user["tokens"],
                    code,
                    False,
                )

            elif choice == "6":
                get_packages_by_family(input("Family code: "))

            elif choice == "7":
                console.print(
                    "[bold red]⚠ WARNING: AUTO LOOP PURCHASE[/]\n"
                    "Tekan CTRL+C untuk batal kapan saja\n"
                )
                pause()
                purchase_by_family(
                    input("Family code: "),
                    input("Use decoy? (y/n): ").lower() == "y",
                    input("Pause on success? (y/n): ").lower() == "y",
                    int(input("Delay seconds: ") or 0),
                    1,
                )

            elif choice == "8":
                show_transaction_history(
                    AuthInstance.api_key,
                    user["tokens"],
                )

            elif choice == "9":
                show_family_info(
                    AuthInstance.api_key,
                    user["tokens"],
                )

            elif choice == "10":
                show_circle_info(
                    AuthInstance.api_key,
                    user["tokens"],
                )

            elif choice == "11":
                show_store_segments_menu(
                    input("Enterprise? (y/n): ").lower() == "y"
                )

            elif choice == "12":
                show_family_list_menu(
                    profile["subscription_type"],
                    input("Enterprise? (y/n): ").lower() == "y",
                )

            elif choice == "13":
                show_store_packages_menu(
                    profile["subscription_type"],
                    input("Enterprise? (y/n): ").lower() == "y",
                )

            elif choice == "14":
                show_redeemables_menu(
                    input("Enterprise? (y/n): ").lower() == "y"
                )

            elif choice == "00":
                show_bookmark_menu()

            elif choice.upper() == "T":
                THEME = "minimal" if THEME == "dark" else "dark"

            elif choice == "99":
                sys.exit(0)

            else:
                pause()

        else:
            sel = show_account_menu()
            if sel:
                AuthInstance.set_active_user(sel)



if __name__ == "__main__":
    try:
        if check_for_updates():
            pause()
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Application closed[/]")
