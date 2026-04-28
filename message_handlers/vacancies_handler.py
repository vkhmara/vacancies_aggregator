from datetime import datetime, timedelta, timezone

from telegram import LinkPreviewOptions, Update
from telegram.ext import CommandHandler, ContextTypes
from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler
from services.periodic_tasks import VacancyCheckJob
from services.redis import RedisDateTimeField
from services.vacancies import TelegramVacancies, Vacancy
from utilities.config import CONFIG
from utilities.datetime import datetime_to_text


class VacanciesMessageHandler(BaseMessageHandler):
    @classmethod
    def vacancy_to_str(cls, vacancy: Vacancy):
        return f'Date: {datetime_to_text(vacancy.date)}\n<a href="{vacancy.link}">Link</a>\n----\n<blockquote expandable>{vacancy.text}</blockquote>'

    @classmethod
    @state_handler
    async def __vacancies(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        redis_field = RedisDateTimeField(
            name=CONFIG.REDIS.LAST_VACANCY_CHECKED_DATE_FIELD
        )
        found_any = False
        async for vacancy in TelegramVacancies().get_vacancies(
            from_datetime=redis_field.get()
        ):
            found_any = True
            await update.message.reply_text(
                text=cls.vacancy_to_str(vacancy),
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(
                    is_disabled=True,
                ),
            )

        redis_field.set(datetime.now(tz=timezone(timedelta(hours=3))))

        if not found_any:
            await update.message.reply_text(
                text="Hi bitches",
                parse_mode="HTML",
            )

    @classmethod
    def get_handlers(cls) -> list:
        return [
            CommandHandler(
                BotCommandType.VACANCIES,
                cls.__vacancies,
            ),
        ]


class VacancyCheckHandler(BaseMessageHandler):
    @classmethod
    def vacancy_to_str(cls, vacancy: Vacancy):
        return f'Date: {datetime_to_text(vacancy.date)}\n<a href="{vacancy.link}">Link</a>\n----\n{vacancy.text}'

    @classmethod
    @state_handler
    async def __start(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        chat_id = update.effective_chat.id
        if not context.job_queue:
            await update.message.reply_text(
                "Unable to start receiving vacancies: context doesn't contain job_queue",
            )
            return

        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        context.job_queue.run_repeating(
            callback=VacancyCheckJob.handler,
            interval=timedelta(minutes=1),
            chat_id=chat_id,
        )
        await update.message.reply_text("Receiving vacancies started")

    @classmethod
    @state_handler
    async def __stop(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        chat_id = update.effective_chat.id
        if not context.job_queue:
            await update.message.reply_text(
                "Unable to stop receiving vacancies: context doesn't contain job_queue",
            )
            return

        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("Receiving vacancies stopped")

    @classmethod
    def get_handlers(cls) -> list:
        return [
            CommandHandler(BotCommandType.START, cls.__start),
            CommandHandler(BotCommandType.STOP, cls.__stop),
        ]
