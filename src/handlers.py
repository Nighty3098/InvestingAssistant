import asyncio
import os
import sys
import threading
import time
from threading import Thread

from pyrogram import Client, enums, filters
from pyrogram.types import InputMediaPhoto, Message

from config import API_HASH, API_ID, BOT_TOKEN, app, data_file, log_file, logger
from db import db
from func import (
    log_resource_usage,
    notify_user,
    process_adding_stocks,
    process_removing_stocks,
    register_user,
    send_images,
    start_monitoring_thread,
    start_parsing_thread,
    start_price_monitor_thread,
)
from kb_builder.admin_panel import admin_kb, admin_panel, users_control
from kb_builder.user_panel import (
    back_kb,
    back_stocks_kb,
    confirm_delete_account,
    main_kb,
    register_user_kb,
    settings_kb,
    stocks_management_kb,
)
from model.price_core import StockPredictor
from parsing import NewsParser, run_check_new_articles
from resources.messages import (
    ASSETS_MESSAGE,
    WELCOME_MESSAGE,
    add_asset_request,
    check_price,
    collect_data,
    confirm_delete_account_message,
    get_news_period,
    get_users_city,
    hvnt_network_tokens,
    not_register_message,
    register_message,
    remove_asset_request,
    select_lang_dialog,
)
from create_report import ReportTable
from create_report import AdvicePredictor

user_states = {}

img_path = "resources/header.png"

@app.on_message(filters.command("start"))
async def start(client, message):
    try:
        global user_id, username
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"

        db.get_connection()
        db._create_users_table()

        if db.check_user_account(user_id):
            photo_path = img_path
            logger.info(f"New User: {user_id} - {username}")

            if not db.check_user_ban(username):
                if db.is_admin(user_id):
                    await app.send_photo(
                        photo=photo_path,
                        chat_id=user_id,
                        caption=WELCOME_MESSAGE,
                        reply_markup=admin_kb,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                else:
                    await app.send_photo(
                        photo=photo_path,
                        chat_id=user_id,
                        caption=WELCOME_MESSAGE,
                        reply_markup=main_kb,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )

                start_parsing_thread(user_id)
                start_price_monitor_thread(user_id)
            else:
                photo_path = img_path
                logger.info(f"New User: {user_id} - {username} - banned")
                await app.send_photo(
                    photo=photo_path,
                    chat_id=user_id,
                    caption=f"{username}, you are banned. Please contact the administrator for details",
                    reply_markup=None,
                    parse_mode=enums.ParseMode.MARKDOWN,
                )

        else:
            photo_path = img_path
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


@app.on_message(filters.command("send_tokens"))
async def send_tokens_command(client: Client, message: Message):
    if db.is_admin(message.from_user.id):
        try:
            args = message.command[1:]
            if len(args) != 2:
                await message.reply("Use format: /send_tokens username tokens")
                return

            username = args[0]
            tokens = args[1]

            user_id = db.get_id_by_username(username)
            db.update_tokens(user_id, tokens)

            await app.send_message(
                chat_id=user_id, text=f"You have received {tokens} tokens"
            )
        except Exception as e:
            logger.error(f"Error: {e}")

    else:
        await message.reply("You are not an admin")


@app.on_callback_query()
async def answer(client, callback_query):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or "unknown"

        async def handle_admin_add_remove(action):
            if not db.is_admin(user_id):
                logger.debug(f"{user_id} - not admin")
                return
            admin_usernames = db.get_all_admins()
            if admin_usernames:
                admins_list = "\n @".join(admin_usernames)
                msg = f"\nAdmins: {admins_list}\nEnter username to {action}:"
            else:
                msg = f"\nNo admins found.\nEnter username to {action}:"
            logger.info(f"{action}: {user_id} - {username}")
            user_states[user_id] = action
            await callback_query.message.edit_text(
                msg,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=admin_panel,
            )

        async def handle_users_menu():
            users_list = db.get_users_list()
            msg = "Username - id - tokens - role - status\n"
            if users_list:
                for user in users_list:
                    user_status = "Banned" if db.check_user_ban(user[1]) else "Active"
                    msg += f"\n@{user[1]} - {user[0]} - {user[2]} - {user[3]} - {user_status}"
            if db.is_admin(user_id):
                try:
                    await callback_query.message.edit_text(
                        msg,
                        parse_mode=enums.ParseMode.MARKDOWN,
                        reply_markup=users_control,
                    )
                except Exception as e:
                    logger.error(f"Error: {e}")

        async def handle_simple_state(state, prompt, kb):
            user_states[user_id] = state
            try:
                await callback_query.message.edit_text(
                    prompt,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    reply_markup=kb,
                )
            except Exception as e:
                logger.error(f"Error: {e}")

        async def handle_get_price():
            global price_sent_message
            logger.info(f"get_price: {user_id} - {username}")
            tokens = db.get_network_tokens(user_id)
            logger.debug(f"User ID: {user_id}, user: {username}, tokens: {tokens}")
            if tokens < 1:
                price_sent_message = await callback_query.message.edit_text(
                    hvnt_network_tokens,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    reply_markup=back_kb,
                )
            else:
                user_states[user_id] = "price"
                msg = f"You have {tokens} free tokens\n\n{check_price}"
                price_sent_message = await callback_query.message.edit_text(
                    msg,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    reply_markup=back_kb,
                )

        async def handle_to_main():
            logger.info(f"to_main: {user_id} - {username}")
            user_states[user_id] = "none"
            photo_path = img_path
            sent_messages = callback_query.message
            await app.delete_messages(chat_id=user_id, message_ids=sent_messages.id)
            kb = admin_kb if db.is_admin(user_id) else main_kb
            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption=WELCOME_MESSAGE,
                reply_markup=kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        async def handle_my_stocks():
            logger.info(f"my_stocks: {user_id} - {username}")
            await callback_query.message.edit_text(
                "__Loading...__",
                reply_markup=stocks_management_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            users_stocks = db.get_users_stocks(user_id)
            msg = ASSETS_MESSAGE + "\n\n__" + users_stocks + "__"
            await callback_query.message.edit_text(
                msg,
                reply_markup=stocks_management_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        async def handle_stocks_action(state, request_msg, kb):
            logger.info(f"{state}: {user_id} - {username}")
            user_states[user_id] = state
            stocks_message = db.get_users_stocks(user_id)
            msg = request_msg + stocks_message
            await callback_query.message.edit_text(
                msg,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=kb,
            )

        async def handle_back_stocks():
            logger.info(f"back_stocks_kb: {user_id} - {username}")
            user_states[user_id] = "none"
            users_stocks = db.get_users_stocks(user_id)
            msg = ASSETS_MESSAGE + "\n\n__" + users_stocks + "__"
            await callback_query.message.edit_text(
                msg,
                reply_markup=stocks_management_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        async def handle_news():
            user_states[user_id] = "news"
            global news_sent_message
            if db.is_admin(user_id):
                news_sent_message = await callback_query.message.edit_text(
                    get_news_period,
                    parse_mode=enums.ParseMode.MARKDOWN,
                    reply_markup=back_kb,
                )
            else:
                news_sent_message = await callback_query.message.edit_text(
                    "Feature in development",
                    parse_mode=enums.ParseMode.MARKDOWN,
                )

        # Маппинг команд на обработчики
        handlers = {
            "add_admin": lambda: handle_admin_add_remove("add_admin"),
            "rm_admin": lambda: handle_admin_add_remove("rm_admin"),
            "admin_panel": lambda: (
                logger.debug(f"User: {user_id} - {username} accessed admin panel")
                if db.is_admin(user_id)
                else logger.warning(f"User: {user_id} - admin panel - blocked")
            ) or callback_query.message.edit_text(
                "Welcome to admin panel\n",
                reply_markup=admin_panel,
                parse_mode=enums.ParseMode.MARKDOWN,
            ) if db.is_admin(user_id) else None,
            "users_menu": handle_users_menu,
            "ban_user": lambda: handle_simple_state("ban_user", "Enter username:", back_kb),
            "unblock_user": lambda: handle_simple_state("unblock_user", "Enter username:", back_kb),
            "get_price": handle_get_price,
            "to_main": handle_to_main,
            "settings": lambda: callback_query.message.edit_text(
                "🛠 Settings 🛠",
                reply_markup=settings_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            ),
            "remove_account_dialog": lambda: callback_query.message.edit_text(
                f"Dear, {username}\n{confirm_delete_account_message}",
                reply_markup=confirm_delete_account,
                parse_mode=enums.ParseMode.MARKDOWN,
            ),
            "select_language": lambda: callback_query.message.edit_text(
                f"Dear, {username}\n{select_lang_dialog}",
                reply_markup=select_language,
                parse_mode=enums.ParseMode.MARKDOWN,
            ),
            "remove_account": lambda: (logger.info(f"remove_account: {user_id} - {username}"), db.remove_account(user_id)),
            "my_stocks": handle_my_stocks,
            "add_stocks": lambda: handle_stocks_action("adding", add_asset_request, back_stocks_kb),
            "remove_stocks": lambda: handle_stocks_action("removing", remove_asset_request, back_stocks_kb),
            "back_stocks_kb": handle_back_stocks,
            "predictions": lambda: callback_query.message.edit_text(
                "🔮 **Predictions:** 🔮",
                reply_markup=back_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            ),
            "register_user": lambda: (logger.info(f"register_user: {user_id} - {username}"), register_user(user_id, username, callback_query)),
            "news": handle_news,
            "set_city": lambda: (
                user_states.__setitem__(user_id, "set_city"),
                callback_query.message.edit_text(
                    get_users_city,
                    parse_mode=enums.ParseMode.MARKDOWN,
                ),
            ),
        }

        handler = handlers.get(data)
        if handler:
            result = handler()
            if hasattr(result, "__await__"):
                await result

    except Exception as e:
        logger.error(f"Error: {e}")



@app.on_message(filters.private & filters.text)
async def handle_input(client, message):

    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    state = user_states.get(user_id)
    photo_path = img_path

    if state == "unblock_user":
        db.unblock_user(username, message)
        return

    if state == "ban_user":
        db.block_user(username, message)
        return

    if state == "add_admin":
        try:
            data = message.text
            db.add_admin_role(data)

            admin_usernames = db.get_all_admins()
            admins_list = "\n".join(admin_usernames)
            msg = f"\nAdmins: {admins_list}:"

            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption=f"✅ Added successfully\n\n{msg}",
                reply_markup=back_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        except Exception as err:
            logger.error(err)

    if state == "rm_admin":
        try:
            data = message.text
            db.remove_admin_role(data)

            admin_usernames = db.get_all_admins()
            admins_list = "\n".join(admin_usernames)
            msg = f"\nAdmins: {admins_list}"

            await app.send_photo(
                photo=photo_path,
                chat_id=user_id,
                caption=f"✅ Removed successfully\n\n{msg}",
                reply_markup=back_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        except Exception as err:
            logger.error(err)

    if state == "adding":
        await process_adding_stocks(client, message, user_id)
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

        news_parser = NewsParser()
        results = news_parser.start_parsing(data, user_id)
        for result in results:
            await notify_user(user_id, result)

        photo_path = img_path
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

        db.add_city_to_db(user_id, data)

        photo_path = img_path
        await app.send_photo(
            photo=photo_path,
            chat_id=user_id,
            caption="__Done__",
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )

    elif state == "price":
        await app.delete_messages(chat_id=user_id, message_ids=price_sent_message.id)
        wait_message = await app.send_message(user_id, "⏳ Thinking...")
        data = message.text

        stock_name, _ = db.get_stock_info(data)
        info = db.get_more_info(data)

        predictor = StockPredictor()
        predict_message, price_change = predictor.analyze(data)

        advice_predictor = AdvicePredictor()
        advice_message = advice_predictor.analyze(data, price_change)

        report_table = ReportTable(data)
        report_data = report_table.download_data(data)
        report_path = report_table.save_report(report_data)

        predict_path = predictor.predict_plt(data, user_id)

        db.update_tokens(user_id, "-1")
        updated_tokens = db.get_network_tokens(user_id)

        await app.delete_messages(chat_id=user_id, message_ids=wait_message.id)
        await app.send_document(chat_id=user_id, document=report_path, caption="Ticker report")
        await app.send_photo(
            chat_id=user_id,
            photo=predict_path,
            caption=(
                f"**{stock_name}** 🏢\n\n"
                f"**📍 Location:** {info['country']} \n"
                f"**🏭 Sector:** {info['sector']}\n\n"
                f"📊 **Market cap:** {info['market_cap']}\n"
                f"💰 **Dividend yield:** {info['dividend_yield']}\n"
                f"🧮 **P/E ratio:** {info['pe_ratio']}\n"
                f"⚖️ **Quick Ratio:** {info['quick_ratio']}\n"
                f"📈 **Beta:** {info['beta']}\n"
                f"📦 **Shares Outstanding:** {info['shares_outstanding']}\n"
                f"📉 **EPS (Earnings Per Share):** {info['eps']}\n\n"
                f"{advice_message}\n\n"
                f"{predict_message}\n\n\n"
                f"You have {updated_tokens} tokens left"
            ),
            reply_markup=back_kb,
            parse_mode=enums.ParseMode.MARKDOWN,
        )

    user_states[user_id] = None
