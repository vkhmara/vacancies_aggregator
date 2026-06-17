import itertools

from telegram import LinkPreviewOptions, constants
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, timezone

from services.redis import ChatSettingsField, RedisDateTimeField
from services.vacancies import TelegramVacancies, Vacancy
from utilities.config import CONFIG
from utilities.datetime import datetime_to_text


class BaseJob:
    @classmethod
    async def handler(cls, context):
        raise NotImplementedError


class VacancyCheckJob(BaseJob):
    @classmethod
    def vacancy_to_str(cls, vacancy: Vacancy, channel_username: str) -> list[str]:
        header = "\n".join(
            [
                f"Date: {datetime_to_text(vacancy.date)}",
                f'<a href="{vacancy.link}">Link</a> [@{channel_username}]',
                "----",
            ]
        )
        texts = []
        vacancy_format = "<blockquote expandable>{0}</blockquote>"
        max_first_block_len = (
            constants.MessageLimit.MAX_TEXT_LENGTH
            - len(header)
            - 1
            - len(vacancy_format.format(""))
        )
        texts.append(
            f"{header}\n{vacancy_format.format(vacancy.text[:max_first_block_len])}"
        )
        if len(vacancy.text) <= max_first_block_len:
            return texts
        for batched_message in itertools.batched(
            vacancy.text[max_first_block_len:],
            constants.MessageLimit.MAX_TEXT_LENGTH - len(vacancy_format.format("")),
        ):
            texts.append(vacancy_format.format(batched_message))
        return texts

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
        for chat in ChatSettingsField(name="chat_settings").get():
            channel_username = chat.get("username")
            if not channel_username:
                continue
            async for vacancy in TelegramVacancies(
                channel_username=channel_username,
                included_words=chat.get("included_words", []),
                excluded_words=chat.get("excluded_words", []),
            ).get_vacancies(from_datetime=last_checked_date):
                for message_batch in cls.vacancy_to_str(
                    vacancy=vacancy,
                    channel_username=channel_username,
                ):
                    await bot.send_message(
                        chat_id=job.chat_id,
                        text=message_batch,
                        parse_mode="HTML",
                        link_preview_options=LinkPreviewOptions(
                            is_disabled=True,
                        ),
                    )
        redis_field.set(datetime.now(tz=timezone(timedelta(hours=3))))
