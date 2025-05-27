from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

main_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="💵 My stocks 💵", callback_data="my_stocks")],
        [InlineKeyboardButton(text="📊 Stock details 📊", callback_data="get_price")],
        [InlineKeyboardButton(text="📄 News 📄", callback_data="news")],
        [InlineKeyboardButton(text="🛠 Settings 🛠", callback_data="settings")],
        [
            InlineKeyboardButton(
                text="💬 Tech Support 💬", url="https://t.me/DXS_TechSupport_bot"
            )
        ],
    ]
)

select_language = InlineKeyboardMarkup (
    [
        [InlineKeyboardButton(text="🌍 РУССКИЙ", callback_data="set_russian_lang")],
        [InlineKeyboardButton(text="🌍 ENGLISH", callback_data="set_english_lang")],
        [InlineKeyboardButton(text="🌍 日本語", callback_data="set_japan_lang")],
        [InlineKeyboardButton(text="◀️ Back ◀️", callback_data="settings")],
    ]
)

confirm_delete_account = InlineKeyboardMarkup (
    [
        [InlineKeyboardButton(text="✔ YES ✔", callback_data="remove_account")],
        [InlineKeyboardButton(text="❌ CANCEL ❌" ,callback_data="settings")],
    ]
)

stocks_management_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="🟢 Add stocks 🟢", callback_data="add_stocks")],
        [
            InlineKeyboardButton(
                text="🔴 Remove stocks 🔴", callback_data="remove_stocks"
            )
        ],
        [InlineKeyboardButton(text="◀️ Back ◀️", callback_data="to_main")],
    ]
)

settings_kb = InlineKeyboardMarkup(
    [
        # [InlineKeyboardButton(text="🌍 Set language 🌍", callback_data="select_language")],
        [InlineKeyboardButton(text="📆 Set time zone 📆", callback_data="set_city")],
        [InlineKeyboardButton(text="❌ Remove account ❌", callback_data="remove_account_dialog")],
        [InlineKeyboardButton(text="◀️ Back ◀️", callback_data="to_main")],
    ]
)

back_kb = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="◀️ Back ◀️", callback_data="to_main")]]
)

back_stocks_kb = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="◀️ Back ◀️", callback_data="back_stocks_kb")]]
)

register_user_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="🚀 Register 🚀", callback_data="register_user")],
        [
            InlineKeyboardButton(
                text="💬 Tech Support 💬", url="https://t.me/DXS_TechSupport_bot"
            )
        ],
    ]
)
