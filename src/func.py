import asyncio
import os
import re
import threading
import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import psutil
import pytz
import requests
import yfinance as yf
from pyrogram import enums

from config import app, logger
from db import (
    add_stock_to_db,
    check_user_account,
    create_connection,
    get_city_from_db,
    get_users_stocks,
    registering_user,
    remove_stock_from_db,
    update_stock_quantity,
)
from kb_builder.user_panel import main_kb
from resources.messages import WELCOME_MESSAGE, register_message

user_price_thread = {}
user_parse_thread = {}


def is_string(value):
    return isinstance(value, str)


def is_integer(value):
    return str(value).isdigit()


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def create_plt_price(ticker, user_id):
    try:
        period = "5d"
        interval = "1h"

        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            threads=True,
            prepost=True,
        )

        logger.debug(data)

        plt.figure(figsize=(20, 15))
        plt.plot(
            data["Adj Close"],
            label="Adjusted Close Price",
            marker="o",
            color="blue",
            linestyle="-",
            linewidth=2,
            markersize=5,
        )

        max_price = data["Adj Close"].max()
        min_price = data["Adj Close"].min()
        max_date = data["Adj Close"].idxmax()
        min_date = data["Adj Close"].idxmin()

        for i, price in enumerate(data["Adj Close"]):
            if i % 2 == 0:
                plt.text(
                    data.index[i],
                    price + 1,
                    f"{price:.1f}",
                    fontsize=8,
                    ha="center",
                    va="top",
                )
                plt.plot(
                    [data.index[i], data.index[i]],
                    [price, price + 1],
                    color="black",
                    linestyle="--",
                    linewidth=0.5,
                )

        plt.annotate(
            f"Max: {max_price:.2f}",
            xy=(max_date, max_price),
            xytext=(max_date, max_price + 5),
            arrowprops=dict(
                facecolor="black",
            ),
            fontsize=10,
        )
        plt.annotate(
            f"Min: {min_price:.2f}",
            xy=(min_date, min_price),
            xytext=(min_date, min_price - 5),
            arrowprops=dict(
                facecolor="black",
            ),
            fontsize=10,
        )

        plt.title(
            f"{ticker} Price Over the {period} with interval {interval}", fontsize=16
        )
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Price (USD)", fontsize=14)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(
            visible=True,
            linestyle="--",
        )

        plt.axhline(y=max_price, color="red", linestyle="--", label="Resistance")
        plt.axhline(y=min_price, color="green", linestyle="--", label="Support")

        plt.legend()
        plt.tight_layout()
        plt.savefig("stock_price_chart.png")
        plt.close()

        image_path = "stock_price_chart.png"

        return image_path
    except Exception as e:
        logger.error(f"Error in create_plt_price: {e}")
        return None


def get_time_difference(document_date, timezone):
    current_time = datetime.now()

    if isinstance(timezone, tuple):
        timezone = timezone[0]

    new_user_time_str = convert_to_utc(
        timezone, current_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    new_user_time = datetime.strptime(new_user_time_str, "%Y-%m-%d %H:%M:%S")
    input_date = datetime.strptime(document_date, "%Y-%m-%d %H:%M:%S")
    time_difference = abs(new_user_time - input_date)

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    time_parts = []
    if days > 0:
        time_parts.append(f"{days} day{'s' if days > 1 else ''} ago")
    if hours > 0:
        time_parts.append(f"{hours} hour{'s' if hours > 1 else ''} ago")
    if minutes > 0:
        time_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''} ago")

    if not time_parts:
        return "just now"

    return ", ".join(time_parts)


async def check_stock_prices(user_id):
    from db import get_stock_info, get_stocks

    while True:
        stock_prices = get_stocks(create_connection(), user_id)
        logger.debug(f"Old stock prices: {stock_prices}")

        for stock_name in stock_prices.keys():
            current_price = get_stock_info(stock_name)[1]
            if is_string(current_price):
                logger.error(
                    f"Error getting stock price for: {stock_name} {current_price}"
                )
            else:
                if float(current_price) != float(stock_prices[stock_name]):
                    if float(current_price) < float(stock_prices[stock_name]):
                        label = "🔴"
                    if float(current_price) > float(stock_prices[stock_name]):
                        label = "🟢"
                    else:
                        label = "🟡"
                    logger.info(
                        f"New message for {user_id}: Stock price {stock_name} from {stock_prices[stock_name]} to {current_price}"
                    )
                    await app.send_message(
                        user_id,
                        f"{label} Update stock price: {stock_name}\nOld: {stock_prices[stock_name]}\nNew: {current_price}",
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                    stock_prices[stock_name] = str(current_price)
                    logger.info(
                        f"Updated old stock price from {stock_prices[stock_name]} to {current_price}"
                    )
                else:
                    pass
        time.sleep(10)


def start_monitoring_thread():
    try:
        monitor_thread = threading.Thread(target=log_resource_usage)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info(f"Started thread for monitoring")
    except Exception as e:
        logger.error(f"Error in start_monitoring_thread: {e}")


def create_price_loop(user_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_stock_prices(user_id))
    loop.close()


def create_article_loop(user_id: str):
    from parsing import run_check_new_articles

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_check_new_articles(user_id))
    loop.close()


def start_price_monitor_thread(user_id: str):
    try:
        if user_id in user_price_thread:
            logger.info(
                f"Price thread already running for user ID: {user_id}. Skipped..."
            )
        else:
            price_thread = threading.Thread(target=create_price_loop, args=(user_id,))
            price_thread.daemon = True
            price_thread.start()

            user_price_thread[user_id] = price_thread

            logger.info(
                f"Started price thread for checking new articles for user ID: {user_id}"
            )
    except Exception as e:
        logger.error(f"Error in start_parsing_thread: {e}")
    finally:
        pass


def start_parsing_thread(user_id: str):
    try:
        if user_id in user_parse_thread:
            logger.info(f"Thread already running for user ID: {user_id}. Skipped...")
        else:
            thread = threading.Thread(target=create_article_loop, args=(user_id,))
            thread.daemon = True
            thread.start()

            user_parse_thread[user_id] = thread

            logger.info(
                f"Started thread for checking new articles for user ID: {user_id}"
            )
    except Exception as e:
        logger.error(f"Error in start_parsing_thread: {e}")


async def notify_user(user_id, message):
    try:
        await app.send_message(
            user_id,
            message,
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        logger.debug(f"Notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error: {e}")


def convert_to_utc(user_timezone, local_time_str):
    """Convert local time string to UTC based on user's timezone."""
    local_time = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
    local_tz = pytz.timezone(user_timezone)
    localized_time = local_tz.localize(local_time)
    utc_time = localized_time.astimezone(pytz.utc)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


def to_local(user_timezone, utc_time_str):
    """Convert UTC time string to local time based on user's timezone."""
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
    utc_time = pytz.utc.localize(utc_time)
    local_tz = pytz.timezone(user_timezone)
    local_time = utc_time.astimezone(local_tz)
    return local_time.strftime("%Y-%m-%d %H:%M:%S")


def parse_time_period(period_string):
    """Parse a time period string into a timedelta object."""
    try:
        pattern = r"(\d+)\s*(days?|hours?|minutes?|seconds?)"
        match = re.match(pattern, period_string.strip())

        logger.debug(f"Period: {period_string}")

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


def is_within_period(date_string, period_string, user_id):
    """Check if the given date is within the specified period from now."""
    try:
        input_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()

        timezone = get_city_from_db(user_id)

        if isinstance(timezone, tuple):
            timezone = timezone[0]

        new_user_time_str = convert_to_utc(
            timezone, current_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        new_user_time = datetime.strptime(new_user_time_str, "%Y-%m-%d %H:%M:%S")

        logger.debug(f"Input Date: {input_date}")
        logger.debug(f"Current Time in User's Timezone: {new_user_time}")

        time_difference = abs(new_user_time - input_date)
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

        logger.debug(f"{process}")
        logger.debug(f"CPU Usage: {cpu_usage}% - Memory Usage: {memory_info}%")

        time.sleep(60)


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

            start_parsing_thread(user_id)
            start_price_monitor_thread(user_id)

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
