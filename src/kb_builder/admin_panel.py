from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

admin_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="💵 My stocks 💵", callback_data="my_stocks")],
        [InlineKeyboardButton(text="📊 Stock details 📊", callback_data="get_price")],
        [InlineKeyboardButton(text="📄 News 📄", callback_data="news")],
        [InlineKeyboardButton(text="🛠 Settings 🛠", callback_data="settings")],
        [InlineKeyboardButton(text="🛠 Admin panel 🛠", callback_data="admin_panel")],
    ]
)

admin_panel = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="ADD ADMIN", callback_data="add_admin")],
        [InlineKeyboardButton(text="REMOVE ADMIN", callback_data="rm_admin")],
        [InlineKeyboardButton(text="USERS", callback_data="users_menu")],
        [InlineKeyboardButton(text="BACK", callback_data="to_main")],
    ]
)

users_control = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="BAN USER", callback_data="ban_user")],
        [InlineKeyboardButton(text="UNBLOCK USER", callback_data="unblock_user")],
        [InlineKeyboardButton(text="Back", callback_data="admin_panel")],
    ]
)

