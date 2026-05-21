from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler

from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler
from services.redis import ChatSettingsField


class BaseWordsMessageHandler(BaseMessageHandler):
    WORDS_FIELD: str = ""
    WORDS_TYPE: str = ""
    LIST_COMMAND: BotCommandType
    ADD_COMMAND: BotCommandType
    DELETE_COMMAND: BotCommandType
    _SELECT_USERNAME_STATE = 0
    _ADD_WORD_STATE = 1
    _DELETE_WORD_STATE = 2

    @classmethod
    def _chat_settings(cls) -> ChatSettingsField:
        return ChatSettingsField(name="chat_settings")

    @classmethod
    def _selected_username(cls, context: ContextTypes.DEFAULT_TYPE) -> str | None:
        return context.user_data.get("selected_username")

    @classmethod
    async def _prompt_username_selection(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        prompt: str,
    ):
        usernames = cls._chat_settings().get_usernames()
        if not usernames:
            await update.message.reply_text(
                "No chats configured in chat_settings.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        keyboard = [[username] for username in usernames]
        await update.message.reply_text(
            prompt,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return cls._SELECT_USERNAME_STATE

    @classmethod
    @state_handler
    async def _on_username_selected(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = update.message.text.strip()
        if username not in cls._chat_settings().get_usernames():
            await update.message.reply_text(
                "Invalid chat. Select a username from the keyboard.",
            )
            return cls._SELECT_USERNAME_STATE

        context.user_data["selected_username"] = username
        action = context.user_data.get("words_action")
        if action == "list":
            return await cls._list_words(update, context)
        if action == "add":
            return await cls._start_add_word(update, context)
        if action == "delete":
            return await cls._start_delete_word(update, context)
        return ConversationHandler.END

    @classmethod
    @state_handler
    async def _start_list_words(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        context.user_data["words_action"] = "list"
        return await cls._prompt_username_selection(
            update,
            context,
            "Select chat to view words:",
        )

    @classmethod
    @state_handler
    async def _list_words(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = cls._selected_username(context)
        words = cls._chat_settings().get_words(username, cls.WORDS_FIELD)
        if not words:
            await update.message.reply_text(
                f"No {cls.WORDS_TYPE} words configured for '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        words_text = "\n".join(f"- {word}" for word in words)
        await update.message.reply_text(
            f"{cls.WORDS_TYPE.capitalize()} words for '{username}':\n{words_text}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    @state_handler
    async def _start_add_word_flow(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        context.user_data["words_action"] = "add"
        return await cls._prompt_username_selection(
            update,
            context,
            "Select chat to add a word:",
        )

    @classmethod
    @state_handler
    async def _start_add_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = cls._selected_username(context)
        await update.message.reply_text(
            f"Send {cls.WORDS_TYPE} word to add for '{username}'.",
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
        username = cls._selected_username(context)
        value = update.message.text.strip().lower()
        if not value:
            await update.message.reply_text(
                "Word can't be empty. Send a non-empty value."
            )
            return cls._ADD_WORD_STATE

        chat_settings = cls._chat_settings()
        words = chat_settings.get_words(username, cls.WORDS_FIELD)
        if value in words:
            await update.message.reply_text(
                f"'{value}' is already in {cls.WORDS_TYPE} words for '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        chat_settings.add_word(username, cls.WORDS_FIELD, value)
        await update.message.reply_text(
            f"Added '{value}' to {cls.WORDS_TYPE} words for '{username}'.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    @state_handler
    async def _start_delete_word_flow(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        context.user_data["words_action"] = "delete"
        return await cls._prompt_username_selection(
            update,
            context,
            "Select chat to delete a word:",
        )

    @classmethod
    @state_handler
    async def _start_delete_word(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = cls._selected_username(context)
        words = cls._chat_settings().get_words(username, cls.WORDS_FIELD)
        if not words:
            await update.message.reply_text(
                f"No {cls.WORDS_TYPE} words to delete for '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        keyboard = [[word] for word in words]
        await update.message.reply_text(
            f"Choose {cls.WORDS_TYPE} word to delete for '{username}':",
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
        username = cls._selected_username(context)
        value = update.message.text.strip().lower()
        removed = cls._chat_settings().remove_word(username, cls.WORDS_FIELD, value)
        if removed:
            await update.message.reply_text(
                f"Deleted '{value}' from {cls.WORDS_TYPE} words for '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"'{value}' not found in {cls.WORDS_TYPE} words for '{username}'. Select value from the keyboard.",
        )
        return cls._DELETE_WORD_STATE

    @classmethod
    def get_handlers(cls) -> list:
        if not all(
            [
                cls.WORDS_FIELD,
                cls.WORDS_TYPE,
                getattr(cls, "LIST_COMMAND", None),
                getattr(cls, "ADD_COMMAND", None),
                getattr(cls, "DELETE_COMMAND", None),
            ]
        ):
            return []
        username_state_handlers = {
            cls._SELECT_USERNAME_STATE: [
                cls._get_message_handler(cls._on_username_selected)
            ],
        }
        return [
            ConversationHandler(
                entry_points=[CommandHandler(cls.LIST_COMMAND, cls._start_list_words)],
                states=username_state_handlers,
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
            ConversationHandler(
                entry_points=[
                    CommandHandler(cls.ADD_COMMAND, cls._start_add_word_flow)
                ],
                states={
                    **username_state_handlers,
                    cls._ADD_WORD_STATE: [cls._get_message_handler(cls._add_word)],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
            ConversationHandler(
                entry_points=[
                    CommandHandler(cls.DELETE_COMMAND, cls._start_delete_word_flow)
                ],
                states={
                    **username_state_handlers,
                    cls._DELETE_WORD_STATE: [
                        cls._get_message_handler(cls._delete_word)
                    ],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
        ]


class IncludedWordsMessageHandler(BaseWordsMessageHandler):
    WORDS_FIELD = "included_words"
    WORDS_TYPE = "included"
    LIST_COMMAND = BotCommandType.INCLUDED_WORDS
    ADD_COMMAND = BotCommandType.ADD_INCLUDED_WORD
    DELETE_COMMAND = BotCommandType.DELETE_INCLUDED_WORD


class ExcludedWordsMessageHandler(BaseWordsMessageHandler):
    WORDS_FIELD = "excluded_words"
    WORDS_TYPE = "excluded"
    LIST_COMMAND = BotCommandType.EXCLUDED_WORDS
    ADD_COMMAND = BotCommandType.ADD_EXCLUDED_WORD
    DELETE_COMMAND = BotCommandType.DELETE_EXCLUDED_WORD
