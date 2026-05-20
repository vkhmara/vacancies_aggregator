import os

from telegram import LinkPreviewOptions
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, timezone

from telegram.ext import ContextTypes
from services.redis import RedisDateTimeField
from services.vacancies import TelegramVacancies, Vacancy
from utilities.config import CONFIG
from utilities.datetime import datetime_to_text


class BaseJob:
    @classmethod
    async def handler(cls, context):
        raise NotImplementedError


class VacancyCheckJob(BaseJob):
    @classmethod
    def vacancy_to_str(cls, vacancy: Vacancy):
        return "\n".join(
            [
                f"Date: {datetime_to_text(vacancy.date)}",
                f'<a href="{vacancy.link}">Link</a>',
                "----",
                f"<blockquote expandable>{vacancy.text}</blockquote>",
            ]
        )

    @classmethod
    async def handler(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        bot = context.bot
        job = context.job

        redis_field = RedisDateTimeField(
            name=CONFIG.REDIS.LAST_VACANCY_CHECKED_DATE_FIELD
        )
        last_checked_date = redis_field.get()
        if last_checked_date is None:
            last_checked_date = datetime.now(
                tz=timezone(timedelta(hours=3))
            ) - timedelta(weeks=1)
        channel_usernames = os.getenv("CHANNEL_USERNAMES", "").split(",")
        for channel_username in channel_usernames:
            async for vacancy in TelegramVacancies(channel_username=channel_username).get_vacancies(
                from_datetime=last_checked_date,
            ):
                await bot.send_message(
                    chat_id=job.chat_id,
                    text=cls.vacancy_to_str(vacancy),
                    parse_mode="HTML",
                    link_preview_options=LinkPreviewOptions(
                        is_disabled=True,
                    ),
                )
        redis_field.set(datetime.now(tz=timezone(timedelta(hours=3))))
