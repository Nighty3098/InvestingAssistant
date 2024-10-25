import asyncio
import os
import sqlite3

from config import home_dir, logger


def create_connection():
    """Creates connection to SQL DB"""
    tech_support_dir = os.path.join(home_dir, "IPSA")

    if not os.path.exists(tech_support_dir):
        os.makedirs(tech_support_dir)
        logger.info(f"Created directory: {tech_support_dir}")

    db_path = os.path.join(tech_support_dir, "IPSA.db")
    try:
        connection = sqlite3.connect(db_path)
        logger.info(f"Connected to SQL DB at {db_path}")
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
            username TEXT)"""
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
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )

        connection.commit()

        cursor.close()

        logger.info(f"Registered new user: {username} ({user_id})")
    except Exception as e:
        logger.error(f"Error '{e}' while registering user")


def get_users_stocks(connection, user_id):
    response_message = ""
    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT stock_name, quantity FROM stocks WHERE user_id=?", (user_id,)
        )
        rows = cursor.fetchall()

        response_message += "Your stocks:\n"

        for row in rows:
            response_message += f"{row[0]}: {row[1]}\n"
            logger.info(f"Stocks: {row[0]} - {row[1]} for {user_id}")

        if not rows:
            response_message += "You don't have any stock."

        connection.close()
    except Exception as e:
        logger.error(f"Error '{e}' while get users stocks")

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
