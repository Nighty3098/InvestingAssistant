import asyncio
import os
import sys
import threading
import time
from threading import Thread

from pyrogram import Client, enums, filters
from pyrogram.types import InputMediaPhoto

from config import (API_HASH, API_ID, BOT_TOKEN, app, data_file, log_file,
                    logger)
from db import (add_city_to_db, add_stock_to_db, check_user_account,
                create_connection, create_table, create_users_table,
                get_users_stocks, registering_user, remove_stock_from_db,
                update_stock_quantity, remove_account)
from func import (log_resource_usage, notify_user, process_adding_stocks,
                  process_removing_stocks, register_user, send_images,
                  start_monitoring_thread, start_parsing_thread,
                  start_price_monitor_thread)
from kb_builder.user_panel import (back_kb, back_stocks_kb, main_kb,
                                   register_user_kb, stocks_management_kb, settings_kb, confirm_delete_account)
from model.price_core import StockPredictor
from parsing import (check_new_articles, parse_investing_news,
                     run_check_new_articles, start_parsing)
from resources.messages import (ASSETS_MESSAGE, WELCOME_MESSAGE,
                                add_asset_request, check_price, collect_data,
                                get_news_period, get_users_city,
                                not_register_message, register_message,
                                remove_asset_request, confirm_delete_account_message, select_lang_dialog)

user_states = {}


@app.on_message(filters.command("start"))
async def start(client, message):
    try:
        global user_id, username
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"

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

            # start_parsing_thread(user_id)
            # start_price_monitor_thread(user_id)

        else:
            photo_path = "resources/header.png"
            logger.info(f"New User: {user_id} - {username} on registering")
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

        if data == "get_price":
            global price_sent_message

            logger.info(f"get_price: {user_id} - {username}")

            user_states[user_id] = "price"

            price_sent_message = await callback_query.message.edit_text(
                check_price,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=back_kb,
            )

        if data == "to_main":
            logger.info(f"to_main: {user_id} - {username}")

            user_states[user_id] = "none"
            photo_path = "resources/header.png"

            sent_messages = callback_query.message

            await app.delete_messages(chat_id=user_id, message_ids=sent_messages.id)
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption=WELCOME_MESSAGE,
                reply_markup=main_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "settings":
            logger.info(f"settings: {user_id} - {username}")

            message = "🛠 Settings 🛠"

            await callback_query.message.edit_text(
                message,
                reply_markup=settings_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "remove_account_dialog":
            logger.info(f"remove_account_dialog: {user_id} - {username}")

            message = f"Dear, {username}\n{confirm_delete_account_message}"

            await callback_query.message.edit_text(
                message,
                reply_markup=confirm_delete_account,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "select_language":
            logger.info(f"select_language: {user_id} - {username}")

            message = f"Dear, {username}\n{select_lang_dialog}"

            await callback_query.message.edit_text(
                message,
                reply_markup=select_language,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "remove_account":
            logger.info(f"remove_account: {user_id} - {username}")

            remove_account(create_connection(), user_id)

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
            stocks_message = get_users_stocks(create_connection(), user_id)
            message = add_asset_request + stocks_message
            await callback_query.message.edit_text(
                message,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=back_stocks_kb,
            )

        if data == "remove_stocks":
            logger.info(f"remove_stocks: {user_id} - {username}")
            user_states[user_id] = "removing"
            stocks_message = get_users_stocks(create_connection(), user_id)
            message = remove_asset_request + stocks_message
            await callback_query.message.edit_text(
                message,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=back_stocks_kb,
            )

        if data == "back_stocks_kb":
            logger.info(f"back_stocks_kb: {user_id} - {username}")

            user_states[user_id] = "none"

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
            user_states[user_id] = "news"
            global news_sent_message

            news_sent_message = await callback_query.message.edit_text(
                get_news_period,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if data == "set_city":
            user_states[user_id] = "set_city"
            global city_sent_message

            city_sent_message = await callback_query.message.edit_text(
                get_users_city,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(f"Error: {e}")


@app.on_message(filters.private & filters.text)
async def handle_stock_input(client, message):

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

    elif state == "news":
        await app.delete_messages(chat_id=user_id, message_ids=news_sent_message.id)

        data = message.text

        results = start_parsing(data, user_id)
        for result in results:
            await notify_user(user_id, result)

        photo_path = "resources/header.png"
        await app.send_photo(
            photo=photo_path,
            chat_id=user_id,
            caption="__Done__",
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    elif state == "set_city":
        await app.delete_messages(chat_id=user_id, message_ids=city_sent_message.id)

        data = message.text

        add_city_to_db(user_id, data)

        photo_path = "resources/header.png"
        await app.send_photo(
            photo=photo_path,
            chat_id=user_id,
            caption="__Done__",
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )

    elif state == "price":
        from db import get_more_info, get_stock_info
        from func import create_plt_price

        await app.delete_messages(chat_id=user_id, message_ids=price_sent_message.id)

        wait_message = await app.send_message(user_id, "⏳ Please wait...")

        data = message.text

        stock_name, stock_price = get_stock_info(data)
        info = get_more_info(data)

        predictor = StockPredictor()
        advice_message = predictor.analyze(data)

        predict_path = predictor.predict_plt(data, user_id)
        image_path = create_plt_price(data, user_id)

        # images = []
        # images.append(InputMediaPhoto(image_path))
        # images.append(InputMediaPhoto(predict_path))

        await app.delete_messages(chat_id=user_id, message_ids=wait_message.id)
        # await app.send_media_group(chat_id=user_id, media=images)
        await app.send_photo(
            chat_id=user_id,
            photo=predict_path,
            caption=(
                f"**{stock_name}**:\n\n"
                f"Current price: {stock_price}$\n\n"
                f"────────────────────────────\n"
                # f"{info['recommendations']}\n\n"
                # f"────────────────\n"
                f"P/E ratio: {info['pe_ratio']}\n"
                f"Target mean price: {info['target_mean_price']}$\n"
                f"Target high price: {info['target_high_price']}$\n"
                f"Target low price: {info['target_low_price']}$\n"
                f"────────────────────────────\n"
                f"{advice_message}"
            ),
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )

    user_states[user_id] = None
