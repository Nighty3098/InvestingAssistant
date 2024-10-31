import os
import re
import time
from datetime import datetime, timedelta

import investpy
import psutil
import requests
import yfinance as yf
from pyrogram import enums

from config import app, logger
from db import (add_stock_to_db, check_user_account, create_connection,
                get_users_stocks, registering_user, remove_stock_from_db,
                update_stock_quantity)
from kb_builder.user_panel import main_kb
from resources.messages import WELCOME_MESSAGE, register_message


async def notify_user(user_id, message):
    try:
        await app.send_message(user_id, message)
    except Exception as e:
        logger.error(f"Error: {e}")


def parse_time_period(period_string):
    """Parse a time period string into a timedelta object."""
    try:
        pattern = r"(\d+)\s*(days?|hours?|minutes?|seconds?)"
        match = re.match(pattern, period_string.strip())

        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()

            if "day" in unit:
                return timedelta(days=value)
            elif "hour" in unit:
                return timedelta(hours=value)
            elif "minute" in unit:
                return timedelta(minutes=value)
            elif "second" in unit:
                return timedelta(seconds=value)

        raise ValueError("Invalid time period format")
    except Exception as e:
        logger.error(f"Error in parse_time_period: {e}")
        return None

def is_within_period(date_string, period_string):
    """Check if the given date is within the specified period from now."""
    try:
        input_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        time_difference = abs(now - input_date)
        period = parse_time_period(period_string)

        if period is None:
            logger.error("Invalid period string provided.")
            return False

        logger.debug(f"Period: {period} Time difference: {time_difference}")
        return time_difference <= period
    except Exception as e:
        logger.error(f"Error in is_within_period: {e}")
        return False



def log_resource_usage():
    """RESOURCE USAGE."""
    process = psutil.Process(os.getpid())

    while True:
        cpu_usage = process.cpu_percent(interval=1)
        memory_info = process.memory_percent()

        logger.info(f"{process}")
        logger.info(f"CPU Usage: {cpu_usage}% - Memory Usage: {memory_info}%")

        time.sleep(5)


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
