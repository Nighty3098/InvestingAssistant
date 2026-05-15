import os
import random
from urllib.parse import urlparse

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

PROXIES_FILE = os.path.join(os.path.dirname(__file__), "..", "proxies.txt")


def load_proxies():
    proxies = []
    try:
        with open(PROXIES_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and (line.startswith("socks5://") or line.startswith("socks5h://")):
                    proxies.append(line)
        if proxies:
            logger.info(f"Loaded {len(proxies)} proxy(ies) from {PROXIES_FILE}")
    except FileNotFoundError:
        logger.info("proxies.txt not found, running without proxy")
    return proxies


def parse_socks5_url(url: str):
    parsed = urlparse(url)
    config = {
        "scheme": "socks5",
        "hostname": parsed.hostname,
        "port": parsed.port,
    }
    if parsed.username:
        config["username"] = parsed.username
    if parsed.password:
        config["password"] = parsed.password
    return config


proxy_url = None
proxies = load_proxies()
if proxies:
    proxy_url = random.choice(proxies)
    logger.info(f"Using SOCKS5 proxy: {proxy_url}")

try:
    app = Client(
        name="IPSA",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=False,
        proxy=parse_socks5_url(proxy_url) if proxy_url else None,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize the Pyrogram Client: {e}")

if proxy_url:
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    os.environ["ALL_PROXY"] = proxy_url
    logger.info("Proxy environment variables set for requests/yfinance")
