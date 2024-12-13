import asyncio
import os
import sqlite3

import yfinance as yf

from config import home_dir, logger


def get_more_info(ticker):
    stock = yf.Ticker(ticker)
    stock_info = stock.info

    recommendations = stock.recommendations

    target_data = stock.info.get("targetMeanPrice", "Target mean price not found")
    target_high = stock.info.get("targetHighPrice", "Target high price not found")
    target_low = stock.info.get("targetLowPrice", "Target low price not found")
    stock_name = stock_info.get("longName", "Name not found")
    stock_price = stock_info.get("currentPrice", "Price not found")
    market_cap = stock_info.get("marketCap", "Market cap not found")
    pe_ratio = stock_info.get("trailingPE", "P/E ratio not found")
    dividend_yield = stock_info.get("dividendYield", "Dividend yield not found")
    country = stock.info.get("country", "Country not found")
    sector = stock.info.get("sector", "Sector not found")
    eps = stock.info.get("trailingEps", "EPS not found")

    return {
        "sector": sector,
        "country": country,
        "eps": eps,
        "name": stock_name,
        "price": stock_price,
        "market_cap": market_cap,
        "pe_ratio": pe_ratio,
        "dividend_yield": dividend_yield,
        "recommendations": recommendations,
        "target_mean_price": target_data,
        "target_high_price": target_high,
        "target_low_price": target_low,
    }


def get_stock_info(ticker):
    stock = yf.Ticker(ticker)

    stock_info = stock.info

    stock_name = stock_info.get("longName", "Name not found")
    stock_price = stock_info.get("currentPrice", "Price not found")

    return stock_name, stock_price


def get_promo_by_code(ticker):
    stock = yf.Ticker(ticker)
    return stock.info["longName"]


def create_connection():
    """Creates connection to SQL DB"""
    tech_support_dir = os.path.join(home_dir, "IPSA")

    if not os.path.exists(tech_support_dir):
        os.makedirs(tech_support_dir)
        logger.debug(f"Created directory: {tech_support_dir}")

    db_path = os.path.join(tech_support_dir, "IPSA.db")
    try:
        connection = sqlite3.connect(db_path)
        logger.debug(f"Connected to SQL DB at {db_path}")
        return connection
    except Exception as e:
        logger.error(f"Error '{e}' while connecting to SQL DB at {db_path}")
        return None


def create_users_table(connection):
    """Create tables if they do not exist"""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            city TEXT)"""
        )
        connection.commit()
        logger.info("Users table created successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while creating users table")


def create_table(connection):
    """Create tables if they do not exist"""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS stocks (
            user_id INTEGER,
            username TEXT,
            stock_name TEXT,
            quantity INTEGER,
            PRIMARY KEY (user_id, stock_name)
        )"""
        )
        connection.commit()
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while creating tables")


def check_user_account(connection, user_id):
    """Check user account from DB"""
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))

    result = cursor.fetchone()

    cursor.close()

    if result:
        return True
    else:
        return False


def registering_user(connection, user_id, username):
    """Register new user in DB"""
    try:
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users (user_id, username, city) VALUES (?, ?, ?)",
            (user_id, username, "Asia/Novosibirsk"),
        )

        connection.commit()

        cursor.close()

        logger.warning(f"Registered new user: {username} ({user_id})")
    except Exception as e:
        logger.error(f"Error '{e}' while registering user")


def get_stocks(connection, user_id):
    cursor = connection.cursor()

    cursor.execute(
        "SELECT stock_name, quantity FROM stocks WHERE user_id=?", (user_id,)
    )
    rows = cursor.fetchall()

    stock_prices = {}

    for row in rows:
        stock_name = row[0]
        stock_price = get_stock_info(stock_name)[1]
        stock_prices[stock_name] = stock_price

        logger.debug(f"{user_id}: {stock_name} - {stock_price}")

    return stock_prices


def get_stocks_list(connection, user_id):
    cursor = connection.cursor()

    cursor.execute(
        "SELECT stock_name, quantity FROM stocks WHERE user_id=?", (user_id,)
    )
    rows = cursor.fetchall()

    return [(row[0], row[1]) for row in rows]


def process_stocks(connection, user_id):
    stocks_data = get_stocks_list(connection, user_id)

    stocks_info_list = []

    for ticker, quantity in stocks_data:
        stock_name, stock_price = get_stock_info(ticker)

        stocks_info_list.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "name": stock_name,
                "price": stock_price,
            }
        )

    return stocks_info_list


def get_users_stocks(connection, user_id):
    response_message = ""
    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT stock_name, quantity FROM stocks WHERE user_id=?", (user_id,)
        )
        rows = cursor.fetchall()

        total_stocks = len(rows)
        response_message += "**Your stocks:**\n\n―――――――――――――――\n"

        if total_stocks == 0:
            response_message += "You don't have any stock."
            return response_message

        for index, row in enumerate(rows):
            try:
                stock_name, stock_price = get_stock_info(row[0])

                if stock_price == "Price not found":
                    stock_price = 0

                response_message += f"🚀 **{row[0]} - {stock_name} - {stock_price}$**\n__💵 {row[1]} = {round(float(row[1]) * float(stock_price), 2)}$__\n\n"
                logger.info(
                    f"Stocks: {row[0]} - {stock_name} - {stock_price}$: {row[1]} = {float(row[1]) * float(stock_price)}"
                )
            except Exception as err:
                logger.error("Error while getting stock: " + str(err))
                response_message += f"{row[0]}: {row[1]}\n"
                logger.info(f"Stocks: {row[0]} - {row[1]} for {user_id}")

            percent_complete = (index + 1) / total_stocks * 100
            logger.debug(f"Progress: {percent_complete:.2f}%")

        connection.close()
    except Exception as e:
        logger.error(f"Error '{e}' while getting user's stocks")

    return response_message


def add_stock_to_db(user_id, username, stock_name, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO stocks (user_id, username, stock_name, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, stock_name) DO UPDATE SET quantity = quantity + excluded.quantity
        """,
            (user_id, username, stock_name, quantity),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding stock: {e}")
        return False
    finally:
        conn.close()


def remove_stock_from_db(user_id, stock_name):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM stocks WHERE user_id = ? AND stock_name = ?
        """,
            (user_id, stock_name),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error removing stock: {e}")
        return False
    finally:
        conn.close()


def update_stock_quantity(user_id, stock_name, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE stocks SET quantity = quantity - ?
            WHERE user_id = ? AND stock_name = ?
        """,
            (quantity, user_id, stock_name),
        )

        cursor.execute(
            """
            DELETE FROM stocks WHERE user_id = ? AND stock_name = ? AND quantity <= 0
        """,
            (user_id, stock_name),
        )

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating stock quantity: {e}")
        return False
    finally:
        conn.close()


def id_by_user_id(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting id: {e}")
        return None
    finally:
        conn.close()


def add_city_to_db(user_id, city):
    conn = create_connection()
    cursor = conn.cursor()

    primary_id = id_by_user_id(user_id)

    try:
        cursor.execute(
            """
            UPDATE users SET city = ?
            WHERE user_id = ?
            """,
            (city, user_id),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding city: {e}")
        return False
    finally:
        conn.close()


def get_city_from_db(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting city: {e}")
        return None
    finally:
        conn.close()
