from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler

from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler
from services.redis import RedisListField


class BaseWordsMessageHandler(BaseMessageHandler):
    WORDS_KEY: str = ""
    WORDS_TYPE: str = ""
    LIST_COMMAND: BotCommandType
    ADD_COMMAND: BotCommandType
    DELETE_COMMAND: BotCommandType
    _ADD_WORD_STATE = 0
    _DELETE_WORD_STATE = 1

    @classmethod
    def _field(cls) -> RedisListField:
        return RedisListField(name=cls.WORDS_KEY)

    @classmethod
    @state_handler
    async def _list_words(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        words = cls._field().get()
        if not words:
            await update.message.reply_text(f"No {cls.WORDS_TYPE} words configured.")
            return
        words_text = "\n".join(f"- {word}" for word in words)
        await update.message.reply_text(
            f"{cls.WORDS_TYPE.capitalize()} words:\n{words_text}"
        )

    @classmethod
    @state_handler
    async def _start_add_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await update.message.reply_text(
            f"Send {cls.WORDS_TYPE} word to add.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return cls._ADD_WORD_STATE

    @classmethod
    @state_handler
    async def _add_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        value = update.message.text.strip().lower()
        if not value:
            await update.message.reply_text(
                "Word can't be empty. Send a non-empty value."
            )
            return cls._ADD_WORD_STATE

        words_field = cls._field()
        words = words_field.get()
        if value in words:
            await update.message.reply_text(
                f"'{value}' is already in {cls.WORDS_TYPE} words.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        words_field.add(value)
        await update.message.reply_text(
            f"Added '{value}' to {cls.WORDS_TYPE} words.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    @state_handler
    async def _start_delete_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        words = cls._field().get()
        if not words:
            await update.message.reply_text(f"No {cls.WORDS_TYPE} words to delete.")
            return ConversationHandler.END

        keyboard = [[word] for word in words]
        await update.message.reply_text(
            f"Choose {cls.WORDS_TYPE} word to delete:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return cls._DELETE_WORD_STATE

    @classmethod
    @state_handler
    async def _delete_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        value = update.message.text.strip().lower()
        removed_count = cls._field().remove(value)
        if removed_count:
            await update.message.reply_text(
                f"Deleted '{value}' from {cls.WORDS_TYPE} words.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"'{value}' not found in {cls.WORDS_TYPE} words. Select value from the keyboard.",
        )
        return cls._DELETE_WORD_STATE

    @classmethod
    def get_handlers(cls) -> list:
        if not all(
            [
                cls.WORDS_KEY,
                cls.WORDS_TYPE,
                getattr(cls, "LIST_COMMAND", None),
                getattr(cls, "ADD_COMMAND", None),
                getattr(cls, "DELETE_COMMAND", None),
            ]
        ):
            return []
        return [
            CommandHandler(cls.LIST_COMMAND, cls._list_words),
            ConversationHandler(
                entry_points=[CommandHandler(cls.ADD_COMMAND, cls._start_add_word)],
                states={
                    cls._ADD_WORD_STATE: [cls._get_message_handler(cls._add_word)],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
            ConversationHandler(
                entry_points=[
                    CommandHandler(cls.DELETE_COMMAND, cls._start_delete_word)
                ],
                states={
                    cls._DELETE_WORD_STATE: [
                        cls._get_message_handler(cls._delete_word)
                    ],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
        ]


class IncludedWordsMessageHandler(BaseWordsMessageHandler):
    WORDS_KEY = "included_words"
    WORDS_TYPE = "included"
    LIST_COMMAND = BotCommandType.INCLUDED_WORDS
    ADD_COMMAND = BotCommandType.ADD_INCLUDED_WORD
    DELETE_COMMAND = BotCommandType.DELETE_INCLUDED_WORD


class ExcludedWordsMessageHandler(BaseWordsMessageHandler):
    WORDS_KEY = "excluded_words"
    WORDS_TYPE = "excluded"
    LIST_COMMAND = BotCommandType.EXCLUDED_WORDS
    ADD_COMMAND = BotCommandType.ADD_EXCLUDED_WORD
    DELETE_COMMAND = BotCommandType.DELETE_EXCLUDED_WORD
