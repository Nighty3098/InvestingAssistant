import time

from pyrogram import enums

from config import logger
from db import (add_stock_to_db, check_user_account, create_connection,
                create_table, create_users_table, get_users_stocks,
                registering_user, remove_stock_from_db, update_stock_quantity)
from kb_builder.user_panel import main_kb
from resources.messages import WELCOME_MESSAGE, register_message


async def register_user(user_id, username, callback_query):
    try:
        connection = create_connection()

        registering_user(connection, user_id, username)

        await callback_query.message.edit_text(
            register_message,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        time.sleep(2)
        if check_user_account(connection, user_id):
            await callback_query.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=main_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            logger.info(f"User {user_id} - {username} registered")
        else:
            await callback_query.message.edit_text(
                "**Error while registering user. Try again later**",
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            logger.error(f"Error while registering user")
    except Exception as e:
        logger.error(f"Error '{e}' while registering user")

async def process_adding_stocks(client, message, user_id, username):
    stocks_input = message.text.strip()
    stocks = stocks_input.split("|")

    for stock in stocks:
        name_quantity = stock.strip().split(",")
        if len(name_quantity) != 2:
            await client.send_message(
                message.chat.id, "Incorrect format. Use: stock_name, quantity."
            )
            return

        stock_name = name_quantity[0].strip()

        try:
            quantity = int(name_quantity[1].strip())
            if add_stock_to_db(user_id, username, stock_name, quantity):
                await client.send_message(
                    message.chat.id,
                    f"The asset '{stock_name}' has been successfully added or updated.",
                )
            else:
                await client.send_message(message.chat.id, "Failed to add the asset.")
        except ValueError:
            await client.send_message(message.chat.id, "The quantity must be a number.")
            return


async def process_removing_stocks(client, message, user_id):
    stocks_input = message.text.strip()
    stocks = stocks_input.split("|")

    for stock in stocks:
        name_quantity = stock.strip().split(",")
        if len(name_quantity) < 1:
            continue

        stock_name = name_quantity[0].strip()

        if len(name_quantity) == 2:
            try:
                quantity = int(name_quantity[1].strip())
                if update_stock_quantity(user_id, stock_name, quantity):
                    await client.send_message(
                        message.chat.id,
                        f"The asset '{stock_name}' has been successfully reduced.",
                    )
                else:
                    await client.send_message(
                        message.chat.id, "Failed to update the asset."
                    )
            except ValueError:
                await client.send_message(
                    message.chat.id, "The quantity must be a number."
                )
                return
        else:
            if remove_stock_from_db(user_id, stock_name):
                await client.send_message(
                    message.chat.id,
                    f"The asset '{stock_name}' has been successfully deleted.",
                )
            else:
                await client.send_message(
                    message.chat.id, "Failed to delete the asset."
                )
