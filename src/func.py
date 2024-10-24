import time

from pyrogram import enums

from config import logger
from db import check_user_account, create_connection, registering_user
from kb_builder.user_panel import main_kb
from resources.messages import WELCOME_MESSAGE, register_message


async def register_user(user_id, username, callback_query):
    try:
        connection = create_connection()

        registering_user(connection, user_id, username)

        await callback_query.message.edit_text(
            register_message,
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        time.sleep(2)
        if check_user_account(connection, user_id):
            await callback_query.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=main_kb,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            logger.info(f"User {user_id} - {username} registered")
        else:
            await callback_query.message.edit_text(
                "**Error while registering user. Try again later**",
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            logger.error(f"Error while registering user")
    except Exception as e:
        logger.error(f"Error '{e}' while registering user")
