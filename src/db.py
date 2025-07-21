import asyncio
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Optional, Tuple, List, Dict, Any

import yfinance as yf
from matplotlib.backend_bases import cursors
import requests

from config import DEVELOPER, home_dir, logger

class DatabaseManager:
    def __init__(self):
        self.db_path = self._init_db_path()
        self._init_database()

    def _init_db_path(self) -> str:
        data_dir = os.path.join(home_dir, "IPSA")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.debug(f"Created directory: {data_dir}")
        return os.path.join(data_dir, "IPSA.db")

    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = sqlite3.connect(self.db_path)
            logger.debug(f"Connected to SQL DB at {self.db_path}")
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Database connection closed")

    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Optional[List]:
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                
                conn.commit()
                return None
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                conn.rollback()
                raise

    def _init_database(self):
        self._create_users_table()
        self._create_roles_table()
        self._create_stocks_table()

    def _create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            language INTEGER,
            network_tokens INTEGER DEFAULT 10,
            role_id INTEGER,
            city TEXT DEFAULT 'Europe/Moscow',
            is_banned INTEGER DEFAULT 0,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )"""
        self.execute_query(query)

    def _create_roles_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE
        )"""
        self.execute_query(query)
        
        self.execute_query("INSERT OR IGNORE INTO roles (role_name) VALUES ('user')")
        self.execute_query("INSERT OR IGNORE INTO roles (role_name) VALUES ('admin')")

    def _create_stocks_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stock_name TEXT,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE (user_id, stock_name)
        )"""
        self.execute_query(query)

    @staticmethod
    def get_stock_info(ticker: str) -> Tuple[str, float]:
        def _get_info(stock):
            try:
                stock_info = stock.info
                if not isinstance(stock_info, dict) or stock_info is None:
                    logger.warning(f"Invalid stock info received for {ticker}: {stock_info}")
                    return None, "Error"
                name = stock_info.get("longName")
                price = stock_info.get("currentPrice")
                if name is None and price is None:
                    logger.warning(f"No price/name data available for {ticker}")
                    return None, "Error"
                return name or "Name not found", price or 0.0
            except AttributeError as ae:
                logger.warning(f"AttributeError for {ticker}: {ae}")
                return None, "Error"

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                if stock is None:
                    logger.warning(f"Failed to create Ticker object for {ticker}")
                    return ticker, "Error"
                name, price = _get_info(stock)
                if price == "Error":
                    return ticker, "Error"
                return name, price
            except requests.exceptions.HTTPError as e:
                if "404" in str(e):
                    logger.warning(f"Ticker {ticker} not found (404 error)")
                    return ticker, "Error"
                logger.warning(f"HTTP error for {ticker}: {str(e)}")
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {ticker}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return ticker, "Error"
        return ticker, "Error"

    def check_user_ban(self, username: str) -> bool:
        result = self.execute_query(
            "SELECT is_banned FROM users WHERE username = ?",
            (username,),
            fetch=True
        )
        return bool(result and result[0][0])

    def is_admin(self, user_id: int) -> bool:
        result = self.execute_query(
            """
            SELECT r.role_name FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.user_id = ?
            """,
            (user_id,),
            fetch=True
        )
        return bool(result and result[0][0] == "admin")

    def register_user(self, user_id: int, username: str):
        role_query = "SELECT id FROM roles WHERE role_name = ?"
        role_name = "admin" if username == DEVELOPER else "user"
        tokens = 10000000000 if username == DEVELOPER else 10
        
        role_id = self.execute_query(role_query, (role_name,), fetch=True)[0][0]
        
        self.execute_query(
            """
            INSERT INTO users (user_id, username, network_tokens, role_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, tokens, role_id)
        )
        logger.info(f"Registered new user: {username} ({user_id})")

    def get_user_stocks(self, user_id: int) -> Dict[str, float]:
        stocks = self.execute_query(
            "SELECT stock_name FROM stocks WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        result = {}
        for (stock_name,) in stocks:
            _, price = self.get_stock_info(stock_name)
            result[stock_name] = float(price) if price != "Error" else 0.0
            
        return result

    def _is_crypto(self, ticker):
        return ticker.upper().endswith("-USD")

    def _fetch_stock_info_and_recommendations(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.info
            recommendations = stock.recommendations
            return stock_info, recommendations
        except Exception as e:
            logger.warning(f"Error fetching info for {ticker}: {e}")
            return {"longName": ticker}, None

    def _format_stock_info_dict(self, stock_info, recommendations):
        return {
            "sector": stock_info.get("sector", "Sector not found"),
            "country": stock_info.get("country", "Country not found"),
            "eps": stock_info.get("trailingEps", "EPS not found"),
            "name": stock_info.get("longName", "Name not found"),
            "price": stock_info.get("currentPrice", "Price not found"),
            "market_cap": stock_info.get("marketCap", "Market cap not found"),
            "pe_ratio": stock_info.get("trailingPE", "P/E ratio not found"),
            "dividend_yield": stock_info.get("dividendYield", "Dividend yield not found"),
            "recommendations": recommendations,
            "target_mean_price": stock_info.get("targetMeanPrice", "Target mean price not found"),
            "target_high_price": stock_info.get("targetHighPrice", "Target high price not found"),
            "target_low_price": stock_info.get("targetLowPrice", "Target low price not found"),
            "quick_ratio": stock_info.get("quickRatio", "N/A"),
            "beta": stock_info.get("beta", "N/A"),
            "shares_outstanding": stock_info.get("sharesOutstanding", "N/A"),
            "audit_risk": stock_info.get("auditRisk", "N/A"),
            "board_risk": stock_info.get("boardRisk", "N/A"),
            "compensation_risk": stock_info.get("compensationRisk", "N/A"),
            "shareHolderRights_risk": stock_info.get("shareHolderRightsRisk", "N/A"),
            "overall_risk": stock_info.get("overallRisk", "N/A"),
        }

    def _crypto_stub_info(self, ticker):
        return {
            "sector": "-",
            "country": "-",
            "eps": "-",
            "name": ticker,
            "price": "-",
            "market_cap": "-",
            "pe_ratio": "-",
            "dividend_yield": "-",
            "recommendations": "Недоступно для криптовалют",
            "target_mean_price": "-",
            "target_high_price": "-",
            "target_low_price": "-",
            "quick_ratio": "-",
            "beta": "-",
            "shares_outstanding": "-",
            "audit_risk": "-",
            "board_risk": "-",
            "compensation_risk": "-",
            "shareHolderRights_risk": "-",
            "overall_risk": "-",
        }

    def get_more_info(self, ticker):
        if self._is_crypto(ticker):
            return self._crypto_stub_info(ticker)
        stock_info, recommendations = self._fetch_stock_info_and_recommendations(ticker)
        return self._format_stock_info_dict(stock_info, recommendations)

    def get_promo_by_code(self, ticker):
        stock = yf.Ticker(ticker)
        return stock.info["longName"]

    def create_users_table(self, connection):
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

    def create_table(self, connection):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
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

    def block_user(self, username):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (username,))
                conn.commit()
                logger.info("User blocked successfully")
            except Exception as e:
                logger.error(f"Error '{e}' while blocking user")

    def unblock_user(self, username):
        """Unblock user by setting is_banned to 0"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (username,))
                conn.commit()
                logger.info("User unblocked successfully")
            except Exception as e:
                logger.error(f"Error '{e}' while unblocking user")

    def create_roles_table(self):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT UNIQUE)"""
                )
                conn.commit()
                logger.info("Roles table created successfully")

                cursor.execute("INSERT OR IGNORE INTO roles (role_name) VALUES ('user')")
                cursor.execute("INSERT OR IGNORE INTO roles (role_name) VALUES ('admin')")
                conn.commit()
            except Exception as e:
                logger.error(f"Error '{e}' while creating roles table")

    def get_all_admins(self):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
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

    def add_admin_role(self, username):
        if connection is None:
            connection = self.get_connection()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

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

    def remove_admin_role(self, username):
        """Remove admin role from a user."""
        if connection is None:
            connection = self.get_connection()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

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

    def check_user_account(self, user_id):
        """Check user account from DB"""
        result = self.execute_query(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        return bool(result)

    def registering_user(self, user_id, username):
        """Register new user in DB."""
        try:
            user_role_id = self.execute_query(
                "SELECT id FROM roles WHERE role_name = 'user'",
                fetch=True
            )

            if not user_role_id:
                logger.error("User role ID not found in roles table.")
                return

            if username == DEVELOPER:
                admin_role_id = self.execute_query(
                    "SELECT id FROM roles WHERE role_name = 'admin'",
                    fetch=True
                )
                if not admin_role_id:
                    logger.error("Admin role ID not found in roles table.")
                    return

                self.execute_query(
                    """INSERT INTO users (user_id, username, city, network_tokens, role_id) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, username, "Europe/Moscow", 10000000000, admin_role_id[0][0])
                )
            else:
                self.execute_query(
                    """INSERT INTO users (user_id, username, city, network_tokens, role_id) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, username, "Europe/Moscow", 10, user_role_id[0][0])
                )

            logger.info(f"Registered new user: {username} ({user_id})")
        except Exception as e:
            logger.error(f"Error '{e}' while registering user")

    def remove_account(self, user_id):
        """Remove user's account"""
        try:
            self.execute_query("DELETE FROM stocks WHERE user_id = ?", (user_id,))
            self.execute_query("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            logger.warning(f"User with user_id {user_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error '{e}' while deleting user with user_id {user_id}")

    def get_user_role(self, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
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

    def get_users_list(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, network_tokens, role_id FROM users")
                result = cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"Error fetching users list: {e}")
            return []

    def get_network_tokens(self, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT network_tokens FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()

            if result is not None:
                return result[0]
            else:
                return 0
        except Exception as e:
            logger.error(f"Error fetching network tokens for user_id {user_id}: {e}")
            return 0

    def update_tokens(self, user_id, token_change):
        try:
            sign = token_change[0]
            amount = int(token_change[1:])

            if sign not in ('+', '-'):
                raise ValueError("Invalid token change format. Use '+<number>' or '-<number>'.")

            update_query = """
                UPDATE users 
                SET network_tokens = network_tokens {} ? 
                WHERE user_id = ?
            """.format('+' if sign == '+' else '-')

            self.execute_query(update_query, (amount, user_id))
            logger.info(f"Updated network_tokens for user_id {user_id}: {token_change}")
            return True
        except Exception as e:
            logger.error(f"Error updating network_tokens: {e}")
            return False

    def get_id_by_username(self, username):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()

                if result is not None:
                    return result[0]
                else:
                    return 0
        except Exception as e:
            logger.error(f"Error fetching network tokens for username {username}: {e}")
            return 0

    def get_stocks(self, user_id):
        rows = self.execute_query(
            "SELECT stock_name FROM stocks WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        stock_prices = {}
        for (stock_name,) in rows:
            try:
                _, price = self.get_stock_info(stock_name)
                stock_prices[stock_name] = float(price) if price != "Error" and not isinstance(price, str) else 0
                logger.debug(f"{user_id}: {stock_name} - {price}")
            except Exception as e:
                logger.error(f"Error getting stock price for {stock_name}: {e}")
                stock_prices[stock_name] = 0

        return stock_prices

    def get_stocks_list(self, user_id):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stock_name, quantity FROM stocks WHERE user_id=?", 
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [(row[0], row[1]) for row in rows]
            except Exception as e:
                logger.error(f"Error getting stocks list: {e}")
                return []

    def process_stocks(self, user_id):
        stocks_data = self.get_stocks_list(user_id)

        stocks_info_list = []

        for ticker, quantity in stocks_data:
            stock_name, stock_price = self.get_stock_info(ticker)

            stocks_info_list.append(
                {
                    "ticker": ticker,
                    "quantity": quantity,
                    "name": stock_name,
                    "price": stock_price,
                }
            )

        return stocks_info_list

    def get_users_stocks(self, user_id):
        response_message = ""
        with self.get_connection() as conn:
            try:
                price_display = ""
                total_value = ""
                company_name = ""
                stock_name = ""
                stock_price = ""

                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stock_name, quantity FROM stocks WHERE user_id=?",
                    (user_id,)
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
                    company_name, stock_price = self.get_stock_info(stock_name)

                    if stock_price == "Error" or isinstance(stock_price, str):
                        total_value = 0
                        price_display = "N/A"

                    else:
                        try:
                            stock_price = float(stock_price)
                            total_value = round(quantity * stock_price, 2)
                            price_display = f"{stock_price}$"
                        except (ValueError, TypeError):
                            total_value = 0
                            price_display = "N/A"

                    response_message += (
                        f"**{stock_name} - {company_name}\nPrice: {price_display}**\n"
                        f"__💵 {quantity} stocks on {total_value}$__\n\n"
                    )
                    logger.info(
                        f"Stocks: {stock_name} - {price_display}: {quantity} = {total_value}"
                    )

                    percent_complete = (index + 1) / total_stocks * 100
                    logger.debug(f"Progress: {percent_complete:.2f}%")

            except Exception as e:
                logger.error(f"Error '{e}' while getting user's stocks")

            return response_message

    def add_stock_to_db(self, user_id, stock_name, quantity):
        """Добавление акции в БД"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
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

    def remove_stock_from_db(self, user_id, stock_name):
        """Удаление акции из БД"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
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

    def update_stock_quantity(self, user_id, stock_name, quantity):
        """Обновление количества акций"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
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

    def id_by_user_id(self, user_id):
        """Получение ID по user_id"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"Error getting id: {e}")
                return None

    def add_city_to_db(self, user_id, city):
        """Добавление города в БД"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
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

    def get_city_from_db(self, user_id):
        """Получение города пользователя из БД"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"Error getting city: {e}")
                return None

db = DatabaseManager()
