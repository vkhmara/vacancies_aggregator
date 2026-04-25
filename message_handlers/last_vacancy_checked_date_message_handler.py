from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler
from services.redis import RedisDateTimeField
from utilities.config import CONFIG
from utilities.datetime import datetime_to_text


class LastVacancyCheckedDateMessageHandler(BaseMessageHandler):
    @classmethod
    @state_handler
    async def __last_check_date(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        redis_field = RedisDateTimeField(
            name=CONFIG.REDIS.LAST_VACANCY_CHECKED_DATE_FIELD
        )

        await update.message.reply_text(
            text=f"Last check date: {datetime_to_text(redis_field.get())}",
        )

    @classmethod
    def get_handlers(cls) -> list:
        return [
            CommandHandler(
                BotCommandType.LAST_VACANCY_CHECK_DATE,
                cls.__last_check_date,
            ),
        ]
