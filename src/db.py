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


def create_table(connection):
    """Create tables if they do not exist"""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_id TEXT,
            assets TEXT
            )"""  # Убрана лишняя запятая
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
            "INSERT INTO users (user_id, username, assets) VALUES (?, ?, ?)",
            (user_id, username, ""),
        )

        connection.commit()

        cursor.close()

        logger.info(f"Registered new user: {username} ({user_id})")
    except Exeption as e:
        logger.error(f"Error '{e}' while registering user")


def add_asset(connection, user_id, asset_name, quantity):
    """Add new asset to user's assets in DB"""
    try:
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE users SET assets = ? WHERE user_id = ?",
            (f"{asset_name} {quantity}", user_id),
        )
    except Exception as e:
        logger.error(f"Error '{e}' while adding new asset")
