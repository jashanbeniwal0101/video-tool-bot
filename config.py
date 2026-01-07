import os
import logging
from logging.handlers import RotatingFileHandler

# =========================
# BASIC PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "bot.log")

# =========================
# TELEGRAM CREDENTIALS
# =========================
API_ID = int(os.getenv("API_ID", "12345678"))  # from my.telegram.org
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# =========================
# BOT SETTINGS
# =========================
BOT_WORKERS = int(os.getenv("BOT_WORKERS", "8"))

OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
ADMINS = list(map(int, os.getenv("ADMINS", str(OWNER_ID)).split()))

# =========================
# CHANNEL SETTINGS
# =========================
# Force subscribe channel (set 0 or empty to disable)
FORCE_SUB_CHANNEL = int(os.getenv("FORCE_SUB_CHANNEL", "0"))

# Dump / DB channel (set 0 if not used)
DUMP_ID = int(os.getenv("DUMP_ID", "0"))

# =========================
# WEB SERVER
# =========================
PORT = int(os.getenv("PORT", "8000"))

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

def LOGGER(name: str):
    return logging.getLogger(name)
