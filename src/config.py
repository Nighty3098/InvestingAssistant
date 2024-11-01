import os

import loguru
from dotenv import load_dotenv
from pyrogram import Client, filters

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("IPSA", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

home_dir = os.environ["HOME"]
log_file = home_dir + "/logs/IPSA.log"

data_file = home_dir + "IPSA/IPSA.db"

logger = loguru.logger

logger.level("DEBUG", color="<green>")
logger.level("INFO", color="<cyan>")
logger.level("WARNING", color="<yellow>")
logger.level("CRITICAL", color="<red>")

logger.add(
    log_file,
    level="DEBUG",
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    backtrace=True,
    diagnose=True,
)

logger.debug("Loading: " + log_file)
