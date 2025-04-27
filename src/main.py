from config import API_ID, API_HASH, BOT_TOKEN, data_file, log_file, logger
from handlers import app
from db import db
from func import start_monitoring_thread

if __name__ == "__main__":
    start_monitoring_thread()

    # Инициализация базы данных
    db._init_database()  # Создаст все необходимые таблицы

    app.run()
