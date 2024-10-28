import sys
import threading
import time
from threading import Thread

from pyrogram import Client, enums, filters

from config import (API_HASH, API_ID, BOT_TOKEN, app, data_file, log_file,
                    logger)
from db import (add_stock_to_db, check_user_account, create_connection,
                create_table, create_users_table, get_users_stocks,
                registering_user, remove_stock_from_db, update_stock_quantity)
from func import (log_resource_usage, process_adding_stocks,
                  process_removing_stocks, register_user)
from kb_builder.user_panel import (back_kb, back_stocks_kb, main_kb,
                                   register_user_kb, stocks_management_kb)
from parsing import (check_new_articles, parse_investing_news,
                     run_check_new_articles, start_parsing)
from resources.messages import (ASSETS_MESSAGE, WELCOME_MESSAGE,
                                add_asset_request, collect_data,
                                not_register_message, register_message,
                                remove_asset_request)

user_states = {}


@app.on_message(filters.command("start"))
async def start(client, message):
    try:
        global user_id, username
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"

        Thread(target=log_resource_usage).start()

        connection = create_connection()
        create_users_table(connection)

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

            # thread = threading.Thread(target=run_check_new_articles, args=(user_id,))
            # thread.start()
            # logger.info(
            #    f"Started thread for checking new articles for user ID: {user_id}"
            # )

        else:
            photo_path = "resources/header.png"
            logger.info(f"New User: {user_id} - {username}")
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption=not_register_message,
                reply_markup=register_user_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
    except Exception as e:
        logger.error(f"Error: {e}")


@app.on_callback_query()
async def answer(client, callback_query):
    try:
        data = callback_query.data

        if data == "to_main":
            logger.info(f"to_main: {user_id} - {username}")
            await callback_query.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=main_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "my_stocks":
            logger.info(f"my_stocks: {user_id} - {username}")

            await callback_query.message.edit_text(
                "__Loading...__",
                reply_markup=stocks_management_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

            connection = create_connection()
            users_stocks = get_users_stocks(connection, user_id)
            message = ASSETS_MESSAGE + "\n\n__" + users_stocks + "__"

            await callback_query.message.edit_text(
                message,
                reply_markup=stocks_management_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "add_stocks":
            logger.info(f"add_stocks: {user_id} - {username}")
            user_states[user_id] = "adding"
            await callback_query.message.edit_text(
                add_asset_request,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=back_stocks_kb,
            )

        if data == "remove_stocks":
            logger.info(f"remove_stocks: {user_id} - {username}")
            user_states[user_id] = "removing"
            await callback_query.message.edit_text(
                remove_asset_request,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=back_stocks_kb,
            )

        if data == "back_stocks_kb":
            logger.info(f"back_stocks_kb: {user_id} - {username}")

            connection = create_connection()
            users_stocks = get_users_stocks(connection, user_id)
            message = ASSETS_MESSAGE + "\n\n__" + users_stocks + "__"

            await callback_query.message.edit_text(
                message,
                reply_markup=stocks_management_kb,
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
            await register_user(user_id, username, callback_query)

        if data == "news":
            sent_message = await callback_query.message.edit_text(
                collect_data,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

            results = start_parsing()
            for result in results:
                logger.info(f"Sending result to {user_id} - {username}")
                await app.send_message(
                    user_id,
                    result,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )

            await app.delete_messages(
                chat_id=callback_query.message.chat.id, message_ids=sent_message.id
            )
            photo_path = "resources/header.png"
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption="__Done__",
                reply_markup=back_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(f"Error: {e}")


@app.on_message(filters.private & filters.text)
async def handle_stock_input(client, message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"

        state = user_states.get(user_id)
        photo_path = "resources/header.png"

        if state == "adding":
            await process_adding_stocks(client, message, user_id, username)
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption="✅ Added successfully",
                reply_markup=back_stocks_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
        elif state == "removing":
            await process_removing_stocks(client, message, user_id)
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption="✅ Removed successfully",
                reply_markup=back_stocks_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        user_states[user_id] = None
    except Exception as e:
        logger.error(f"Error: {e}")
