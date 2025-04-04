import asyncio
import os
import sqlite3
import time

import yfinance as yf
from matplotlib.backend_bases import cursors

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
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.info

            stock_name = stock_info.get("longName", "Name not found")
            stock_price = stock_info.get("currentPrice", "Price not found")

            return stock_name, stock_price
        except Exception as e:
            logger.warning(
                f"Attempt {attempt+1}/{max_retries} failed for {ticker}: {str(e)}"
            )
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(
                    f"Failed to get stock info for {ticker} after {max_retries} attempts"
                )
                return f"{ticker}", "Error"


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
    """Create users table if it does not exist."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            language INTEGER,
            network_tokens INTEGER,
            role_id INTEGER,
            city TEXT,
            is_banned INTEGER DEFAULT 0,
            FOREIGN KEY (role_id) REFERENCES roles(id))"""
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stock_name TEXT,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES user(id)
            UNIQUE (user_id, stock_name)
        )"""
        )
        connection.commit()
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while creating tables")

def check_user_ban(username, connection=create_connection()):
    """Check if user is banned"""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result[0] == 1:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error '{e}' while checking user ban")

def block_user(username, connection=create_connection()):
    """Block user by setting is_banned to 1"""
    try:
        if not hasattr(connection, 'cursor'):
            connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (username,))
        connection.commit()
        logger.info("User blocked successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while blocking user")

def unblock_user(username, connection=create_connection()):
    """Unblock user by setting is_banned to 0"""
    try:
        if not hasattr(connection, 'cursor'):
            connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (username,))
        connection.commit()
        logger.info("User unblocked successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while unblocking user")

def create_roles_table(connection=create_connection()):
    """Create roles table if it does not exist."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE)"""
        )
        connection.commit()
        logger.info("Roles table created successfully")

        # Insert default roles if they don't exist
        cursor.execute("INSERT OR IGNORE INTO roles (role_name) VALUES ('user')")
        cursor.execute("INSERT OR IGNORE INTO roles (role_name) VALUES ('admin')")
        connection.commit()
    except Exception as e:
        logger.error(f"Error '{e}' while creating roles table")


def is_admin(user_id):
    """Check if the user has admin role."""
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT r.role_name FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.user_id = ?""",
            (user_id,),
        )
        result = cursor.fetchone()

        return result and result[0] == "admin"
    except Exception as e:
        logger.error(f"Error: '{e}'")
        return False


def get_all_admins(connection=create_connection()):
    """Get all admin usernames."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT u.username FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE r.role_name = 'admin'"""
        )
        admins = cursor.fetchall()

        admin_usernames = [admin[0] for admin in admins]
        logger.info(f"Found: {len(admin_usernames)} admins.")
        return admin_usernames
    except Exception as e:
        logger.error(f"Error '{e}'")
        return []


def add_admin_role(username, connection=create_connection()):
    """Add admin role to a user."""
    try:
        cursor = connection.cursor()

        # Get the id of the 'admin' role
        cursor.execute("SELECT id FROM roles WHERE role_name = 'admin'")
        role_id = cursor.fetchone()

        if role_id:
            cursor.execute(
                "UPDATE users SET role_id = ? WHERE username = ?",
                (role_id[0], username),
            )
            connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Added admin: {username}")
                return True
            else:
                logger.warning(f"User not found: {username}")
                return False
    except Exception as e:
        logger.error(f"Error '{e}'")
    return False


def remove_admin_role(username, connection=create_connection()):
    """Remove admin role from a user."""
    try:
        cursor = connection.cursor()

        # Set role_id to NULL (or you can set it to a default user role)
        cursor.execute(
            "UPDATE users SET role_id = NULL WHERE username = ?", (username,)
        )
        connection.commit()

        if cursor.rowcount > 0:
            logger.info(f"Removed from admin: {username}")
            return True
        else:
            logger.warning(f"User not found: {username}")
            return False
    except Exception as e:
        logger.error(f"Error '{e}'")
    return False


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
    """Register new user in DB."""
    try:
        cursor = connection.cursor()

        # Get the id of the 'user' role (default)
        cursor.execute("SELECT id FROM roles WHERE role_name = 'user'")
        user_role_id = cursor.fetchone()

        if user_role_id is None:
            logger.error("User role ID not found in roles table.")
            return  # Or handle the error as needed

        # Check for special case for admin registration
        if username == "Night3098":
            # Get the id of the 'admin' role
            cursor.execute("SELECT id FROM roles WHERE role_name = 'admin'")
            admin_role_id = cursor.fetchone()

            if admin_role_id is None:
                logger.error("Admin role ID not found in roles table.")
                return  # Or handle the error as needed

            cursor.execute(
                "INSERT INTO users (user_id, username, city, network_tokens, role_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, "Europe/Moscow", 10000000000, admin_role_id[0]),
            )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, username, city, network_tokens, role_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, "Europe/Moscow", 10, user_role_id[0]),
            )

        connection.commit()

        logger.warning(f"Registered new user: {username} ({user_id})")
    except Exception as e:
        logger.error(f"Error '{e}' while registering user")


def remove_account(connection, user_id):
    """Remove user's account"""
    try:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM stocks WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        connection.commit()
        logger.warning(f"User with user_id {user_id} deleted successfully")
    except Exception as e:
        logger.error(f"Error '{e}' while deleting user with user_id {user_id}")


def get_user_role(connection, user_id):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT role_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result is not None:
            cursor.execute("SELECT role_name FROM roles WHERE id = ?", (result[0],))
            role_name = cursor.fetchone()
            return role_name[0] if role_name else ""
        else:
            return ""
    except Exception as e:
        logger.error(f"Error fetching user role for user_id {user_id}: {e}")
        return ""

def get_users_list(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, username, network_tokens, role_id FROM users")
        result = cursor.fetchall()
        return result
    except Exception as e:
        logger.error(f"Error fetching users list: {e}")
        return []

def get_network_tokens(connection, user_id):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT network_tokens FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result is not None:
            return result[0]
        else:
            return 0
    except Exception as e:
        logger.error(f"Error fetching network tokens for user_id {user_id}: {e}")
        return 0


def update_tokens(connection, user_id, token_change):
    sign = token_change[0]
    amount = int(token_change[1:])

    if sign == "+":
        update_query = (
            "UPDATE users SET network_tokens = network_tokens + ? WHERE user_id = ?"
        )
        params = (amount, user_id)
    elif sign == "-":
        update_query = (
            "UPDATE users SET network_tokens = network_tokens - ? WHERE user_id = ?"
        )
        params = (amount, user_id)
    else:
        raise ValueError("Invalid token change format. Use '+<number>' or '-<number>'.")

    try:
        cursor = connection.cursor()
        cursor.execute(update_query, params)
        connection.commit()
        logger.info(f"Updated network_tokens for user_id {user_id}: {token_change}")
        return True
    except Exception as e:
        logger.error(f"Error updating network_tokens: {e}")
        return False


def get_id_by_username(connection, username):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result is not None:
            return result[0]
        else:
            return 0
    except Exception as e:
        logger.error(f"Error fetching network tokens for username {username}: {e}")
        return 0


def get_stocks(connection, user_id):
    cursor = connection.cursor()

    cursor.execute("SELECT stock_name FROM stocks WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()

    stock_prices = {}

    for row in rows:
        stock_name = row[0]
        try:
            name, price = get_stock_info(stock_name)

            if price != "Error" and not isinstance(price, str):
                stock_prices[stock_name] = price
            else:
                stock_prices[stock_name] = 0
                logger.warning(
                    f"Could not get valid price for {stock_name}, using default value 0"
                )

            logger.debug(f"{user_id}: {stock_name} - {price}")
        except Exception as e:
            logger.error(f"Error getting stock price for {stock_name}: {e}")
            stock_prices[stock_name] = 0

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
            stock_name = row[0]
            quantity = row[1]
            stock_price = get_stock_info(stock_name)[1] or 0

            response_message += (
                f"🚀 **{stock_name} - {stock_price}$**\n"
                f"__💵 {quantity} = {round(float(quantity) * float(stock_price), 2)}$__\n\n"
            )
            logger.info(
                f"Stocks: {stock_name} - {stock_price}$: {quantity} = {float(quantity) * float(stock_price)}"
            )

            percent_complete = (index + 1) / total_stocks * 100
            logger.debug(f"Progress: {percent_complete:.2f}%")

    except Exception as e:
        logger.error(f"Error '{e}' while getting user's stocks")

    return response_message


def add_stock_to_db(user_id, username, stock_name, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO stocks (user_id, stock_name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, stock_name) DO UPDATE SET quantity = quantity + excluded.quantity
            """,
            (user_id, stock_name, quantity),
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

        # Удаление акций с нулевым или отрицательным количеством
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
