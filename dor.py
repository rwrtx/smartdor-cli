from dotenv import load_dotenv
load_dotenv()

import sys
from datetime import datetime

from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from app.console import (
    console,
    cyber_input,
    loading_animation,
    print_step,
    print_cyber_panel,
)
from app.menus.util import clear_screen, pause
from app.service.git import check_for_updates
from app.service.auth import AuthInstance
from app.client.engsel import get_balance, get_tiering_info
from app.client.famplan import validate_msisdn
from app.client.registration import dukcapil

from app.menus.account import show_account_menu
from app.menus.bookmark import show_bookmark_menu
from app.menus.payment import show_transaction_history
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.service.sentry import enter_sentry_mode


# ==================================================
# GLOBAL
# ==================================================
LAST_CHOICE = None


# ==================================================
# UI HELPERS
# ==================================================
def safe(val, default="-"):
    return default if val is None else str(val)


def rupiah(val):
    try:
        return f"Rp {int(val):,}".replace(",", ".")
    except Exception:
        return f"Rp {safe(val)}"


# ==================================================
# MAIN MENU UI
# ==================================================
def show_main_menu(profile):
    clear_screen()

    expired_at = datetime.fromtimestamp(
        profile["balance_expired_at"]
    ).strftime("%Y-%m-%d")

    profile_table = Table(show_header=False, box=None, padding=(0, 2))
    profile_table.add_column("Key", style="bright_cyan", justify="right", width=12)
    profile_table.add_column("Value", style="bold white")

    profile_table.add_row("Nomor", safe(profile["number"]))
    profile_table.add_row("Type", safe(profile["subscription_type"]))
    profile_table.add_row("Pulsa", rupiah(profile["balance"]))
    profile_table.add_row("Aktif s/d", expired_at)
    profile_table.add_row("Info", safe(profile["point_info"]))

    print_cyber_panel(profile_table, title="USER PROFILE")

    menu = Table(show_header=True, box=None, padding=(0, 1))
    menu.add_column("ID", style="bold bright_green", justify="right", width=4)
    menu.add_column("MENU", style="bold white")

    menu_items = [
        ("1", "Login / Ganti Akun"),
        ("2", "Lihat Paket Saya"),
        ("3", "🔥 HOT Package"),
        ("4", "🔥 HOT Package 2"),
        ("5", "Beli Paket (Option Code)"),
        ("6", "Beli Paket (Family Code)"),
        ("7", "⚠ AUTO BUY LOOP (BERBAHAYA)"),
        ("8", "Riwayat Transaksi"),
        ("9", "Family Plan / Akrab"),
        ("10", "Circle"),
        ("11", "Store Segments"),
        ("12", "Store Family List"),
        ("13", "Store Packages"),
        ("14", "Redeemables"),
        ("R", "Register Dukcapil"),
        ("V", "Validate MSISDN"),
        ("N", "Notifikasi"),
        ("S", "Sentry Mode"),
        ("00", "Bookmark Paket"),
        ("99", "Keluar"),
    ]

    for k, v in menu_items:
        menu.add_row(k, v)

    console.print(
        Panel(
            Align.left(menu),
            title="[bold bright_magenta]MAIN MENU[/]",
            border_style="bright_cyan",
        )
    )

    console.print("[dim]ENTER = ulang menu terakhir | CTRL+C = keluar[/]\n")


# ==================================================
# MAIN LOGIC
# ==================================================
def main():
    global LAST_CHOICE

    while True:
        user = AuthInstance.get_active_user()

        if not user:
            sel = show_account_menu()
            if sel:
                AuthInstance.set_active_user(sel)
            continue

        with loading_animation("Fetching user data..."):
            balance = get_balance(AuthInstance.api_key, user["tokens"]["id_token"])

            point_info = "Points: N/A | Tier: N/A"
            if user["subscription_type"] == "PREPAID":
                tier = get_tiering_info(AuthInstance.api_key, user["tokens"])
                point_info = f"Points: {tier.get('current_point', 0)} | Tier: {tier.get('tier', 0)}"

        profile = {
            "number": user["number"],
            "subscription_type": user["subscription_type"],
            "balance": balance.get("remaining"),
            "balance_expired_at": balance.get("expired_at"),
            "point_info": point_info,
        }

        show_main_menu(profile)

        choice = cyber_input("Pilih menu").strip()
        if not choice and LAST_CHOICE:
            choice = LAST_CHOICE
        else:
            LAST_CHOICE = choice

        # ================= HANDLER =================
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
            code = cyber_input("Option code")
            show_package_details(AuthInstance.api_key, user["tokens"], code, False)

        elif choice == "6":
            get_packages_by_family(cyber_input("Family code"))

        elif choice == "7":
            console.print("[bold red]⚠ MODE BERBAHAYA[/]")
            if cyber_input("Ketik YES untuk lanjut").upper() == "YES":
                purchase_by_family(
                    cyber_input("Family code"),
                    cyber_input("Use decoy? (y/n)").lower() == "y",
                    cyber_input("Pause on success? (y/n)").lower() == "y",
                    int(cyber_input("Delay seconds") or 0),
                    1,
                )

        elif choice == "8":
            show_transaction_history(AuthInstance.api_key, user["tokens"])

        elif choice == "9":
            show_family_info(AuthInstance.api_key, user["tokens"])

        elif choice == "10":
            show_circle_info(AuthInstance.api_key, user["tokens"])

        elif choice == "11":
            show_store_segments_menu(cyber_input("Enterprise? (y/n)").lower() == "y")

        elif choice == "12":
            show_family_list_menu(
                user["subscription_type"],
                cyber_input("Enterprise? (y/n)").lower() == "y",
            )

        elif choice == "13":
            show_store_packages_menu(
                user["subscription_type"],
                cyber_input("Enterprise? (y/n)").lower() == "y",
            )

        elif choice == "14":
            show_redeemables_menu(cyber_input("Enterprise? (y/n)").lower() == "y")

        elif choice == "R":
            res = dukcapil(
                AuthInstance.api_key,
                cyber_input("MSISDN"),
                cyber_input("KK"),
                cyber_input("NIK"),
            )
            console.print_json(res)
            pause()

        elif choice == "V":
            res = validate_msisdn(
                AuthInstance.api_key,
                user["tokens"],
                cyber_input("MSISDN"),
            )
            console.print_json(res)
            pause()

        elif choice == "N":
            show_notification_menu()

        elif choice == "S":
            enter_sentry_mode()

        elif choice == "00":
            show_bookmark_menu()

        elif choice == "99":
            sys.exit(0)

        else:
            pause()


# ==================================================
# ENTRY
# ==================================================
if __name__ == "__main__":
    try:
        print_step("Checking for updates...")
        with loading_animation("Checking git..."):
            if check_for_updates():
                pause()
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Aplikasi ditutup[/]")
