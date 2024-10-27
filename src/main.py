from config import API_ID, API_HASH, BOT_TOKEN, data_file, log_file, logger
from handlers import app
from db import create_connection, create_users_table, create_table

if __name__ == "__main__":
    connection = create_connection()
    create_users_table(connection)
    create_table(connection)

    app.run()
