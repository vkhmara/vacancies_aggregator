import traceback
from functools import wraps
from telegram import BotCommand, Update, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown
from enums.settings import BotCommandType
from exceptions.finish_conversation import FinishConversation


def state_handler(func):
    @wraps(func)
    async def wrapped(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs,
    ):
        try:
            return await func(cls, update, context, *args, **kwargs)
        except FinishConversation as e:
            await update.message.reply_text(
                str(e),
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        except Exception as e:
            traceback.print_exc()
            error_text = escape_markdown(str(e), version=2)
            await update.message.reply_text(
                f"Something went wrong\n||{error_text}||",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return ConversationHandler.END

    return wrapped


class BaseMessageHandler:
    @classmethod
    def _get_message_handler(
        cls,
        state_handler,
    ):
        return MessageHandler(
            filters=filters.TEXT & ~filters.COMMAND,
            callback=state_handler,
        )

    @classmethod
    async def _cancel(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await update.message.reply_text(
            "Operation cancelled",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    def get_handlers(cls) -> list:
        raise NotImplementedError


async def set_commands(app):
    command_descriptions = {
        BotCommandType.HELP: "Help",
        BotCommandType.START: "Start receiving vacancies",
        BotCommandType.STOP: "Stop receiving vacancies",
        BotCommandType.LAST_VACANCY_CHECK_DATE: "Last check date",
        BotCommandType.VACANCIES: "Manually receive last vacancies",
        BotCommandType.INCLUDED_WORDS: "Show included words",
        BotCommandType.ADD_INCLUDED_WORD: "Add included word",
        BotCommandType.DELETE_INCLUDED_WORD: "Delete included word",
        BotCommandType.EXCLUDED_WORDS: "Show excluded words",
        BotCommandType.ADD_EXCLUDED_WORD: "Add excluded word",
        BotCommandType.DELETE_EXCLUDED_WORD: "Delete excluded word",
        BotCommandType.CHATS: "Show chat usernames",
        BotCommandType.ADD_CHAT: "Add chat username",
        BotCommandType.DELETE_CHAT: "Delete chat username",
    }
    commands = [
        BotCommand(
            command=command_type,
            description=command_descriptions.get(
                command_type,
                "TODO: provide description",
            ),
        )
        for command_type in BotCommandType
    ]
    await app.bot.set_my_commands(commands)
