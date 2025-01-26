from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

admin_kb = InlineKeyboardMarkup (
    [
        [InlineKeyboardButton(text="💵 My stocks 💵", callback_data="my_stocks")],
        [InlineKeyboardButton(text="📊 Stock details 📊", callback_data="get_price")],
        [InlineKeyboardButton(text="📄 News 📄", callback_data="news")],
        [InlineKeyboardButton(text="🛠 Settings 🛠", callback_data="settings")],
        [InlineKeyboardButton(text="🛠 Admin panel 🛠", callback_data="admin_panel")],
    ]
)

admin_panel = InlineKeyboardMarkup (
    [
        [InlineKeyboardButton(text="🔴 Add admin 🔴", callback_data="add_admin")],
        [InlineKeyboardButton(text="🔴 Remove admin 🔴", callback_data="rm_admin")],
        [InlineKeyboardButton(text="◀️ Back ◀️", callback_data="to_main")],
    ]
)