from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

main_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="💵 My stocks 💵", callback_data="my_stocks")],
        [InlineKeyboardButton(text="💫 Predictions 💫", callback_data="predictions")],
        [InlineKeyboardButton(text="📄 News 📄", callback_data="news")],
        [InlineKeyboardButton(text="📊 Analytics 📊", callback_data="analytics")],
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

back_kb = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="◀️ Back ◀️", callback_data="to_main")]]
)

back_stocks_kb = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="◀️ Back ◀️", callback_data="back_stocks_kb")]]
)

register_user_kb = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="🚀 Register 🚀", callback_data="register_user")]]
)
