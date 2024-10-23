from pyrogram import Client, enums, filters

from config import (API_HASH, API_ID, BOT_TOKEN, app, data_file, log_file,
                    logger)
from db import check_user_account, create_connection, create_table
from kb_builder.user_panel import (asset_management_kb, back_assets_kb,
                                   back_kb, main_kb, register_user_kb)
from resources.messages import (ASSETS_MESSAGE, WELCOME_MESSAGE,
                                add_asset_request, register_message,
                                remove_asset_request)


@app.on_message(filters.command("start"))
async def start(client, message):
    global user_id, username
    user_id = message.from_user.id
    username = message.from_user.username

    connection = create_connection()
    create_table(connection)

    if check_user_account(connection, user_id):
        photo_path = "resources/header.png"
        logger.info(f"New User: {user_id} - {username}")
        await app.send_photo(
            photo=photo_path,
            chat_id=user_id,
            caption=WELCOME_MESSAGE,
            reply_markup=main_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    else:
        photo_path = "resources/header.png"
        logger.info(f"New User: {user_id} - {username}")
        await app.send_photo(
            photo=photo_path,
            chat_id=user_id,
            caption=register_message,
            reply_markup=register_user_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )


@app.on_callback_query()
async def answer(client, callback_query):
    data = callback_query.data

    if data == "to_main":
        logger.info(f"to_main: {user_id} - {username}")
        await callback_query.message.edit_text(
            WELCOME_MESSAGE, reply_markup=main_kb, parse_mode=enums.ParseMode.MARKDOWN
        )
    if data == "my_assets":
        logger.info(f"my_assets: {user_id} - {username}")
        await callback_query.message.edit_text(
            ASSETS_MESSAGE,
            reply_markup=asset_management_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    if data == "add_asset":
        logger.info(f"add_asset: {user_id} - {username}")
        await callback_query.message.edit_text(
            add_asset_request,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=back_assets_kb,
        )
    if data == "remove_asset":
        logger.info(f"remove_asset: {user_id} - {username}")
        await callback_query.message.edit_text(
            remove_asset_request,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=back_assets_kb,
        )
    if data == "back_assets_kb":
        logger.info(f"back_assets_kb: {user_id} - {username}")
        await callback_query.message.edit_text(
            ASSETS_MESSAGE,
            reply_markup=asset_management_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    if data == "predictions":
        logger.info(f"predictions: {user_id} - {username}")
        await callback_query.message.edit_text(
            "🔮 **Predictions:** 🔮",
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    if data == "register_user":
        logger.info(f"register_user: {user_id} - {username}")
