from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

main_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text='📊 My assets 📊', callback_data="my_assets")],
        [InlineKeyboardButton(text='💫 Predictions 💫', callback_data="predictions")]
    ]
)


asset_management_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text='🟢 Add asset 🟢', callback_data="add_asset")],
        [InlineKeyboardButton(text='🔴 Remove asset 🔴', callback_data="remove_asset")],
        [InlineKeyboardButton(text='◀️ Back ◀️', callback_data="to_main")]
    ]
)

back_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text='◀️ Back ◀️', callback_data="to_main")]
    ]
)

back_assets_kb = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text='◀️ Back ◀️', callback_data="back_assets_kb")]
    ]
)
