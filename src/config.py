import os

import loguru
from dotenv import load_dotenv
from pyrogram import Client, errors
from pyrogram.enums import parse_mode

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER = os.getenv("DEVELOPER_USERNAME")

home_dir = os.path.expanduser("~")
log_file = os.path.join(home_dir, "logs", "IPSA.log")
data_file = os.path.join(home_dir, "IPSA", "IPSA.db")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError(
        "Missing one or more required environment variables: API_ID, API_HASH, BOT_TOKEN."
    )

try:
    app = Client(
        name="IPSA",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=False,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize the Pyrogram Client: {e}")

logger = loguru.logger

try:
    logger.add(
        log_file,
        level="DEBUG",
        rotation="100000 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
except Exception as e:
    raise RuntimeError(f"Failed to configure the logger: {e}")
logger.debug(f"Loading: {log_file}")
try:
    with open(log_file, "a"):
        logger.info(f"Log file is accessible: {log_file}")
except IOError as e:
    logger.error(f"Error accessing log file: {e}")
except errors.FloodWait as e:
    logger.error(f"Flood wait error: {e.x} seconds until next request.")
except errors.RPCError as e:
    logger.error(f"An RPC error occurred: {e}")
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")
