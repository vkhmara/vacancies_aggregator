from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler

from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler
from services.redis import ChatSettingsField


class ChatSettingsMessageHandler(BaseMessageHandler):
    _ADD_CHAT_STATE = 0
    _DELETE_CHAT_STATE = 1

    @classmethod
    def _chat_settings(cls) -> ChatSettingsField:
        return ChatSettingsField(name="chat_settings")

    @classmethod
    def _normalize_username(cls, raw: str) -> str:
        return raw.strip().lstrip("@").lower()

    @classmethod
    @state_handler
    async def _list_chats(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        usernames = cls._chat_settings().get_usernames()
        if not usernames:
            await update.message.reply_text("No chats configured in chat_settings.")
            return

        chats_text = "\n".join(f"- {username}" for username in usernames)
        await update.message.reply_text(f"Configured chats:\n{chats_text}")

    @classmethod
    @state_handler
    async def _start_add_chat(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await update.message.reply_text(
            "Send chat username to add (with or without @).",
            reply_markup=ReplyKeyboardRemove(),
        )
        return cls._ADD_CHAT_STATE

    @classmethod
    @state_handler
    async def _add_chat(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = cls._normalize_username(update.message.text)
        if not username:
            await update.message.reply_text(
                "Username can't be empty. Send a non-empty value."
            )
            return cls._ADD_CHAT_STATE

        chat_settings = cls._chat_settings()
        if chat_settings.add_chat(username):
            await update.message.reply_text(
                f"Added chat '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"Chat '{username}' already exists.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    @state_handler
    async def _start_delete_chat(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
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
            "Select chat username to delete:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return cls._DELETE_CHAT_STATE

    @classmethod
    @state_handler
    async def _delete_chat(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        username = cls._normalize_username(update.message.text)
        usernames = cls._chat_settings().get_usernames()
        if username not in usernames:
            await update.message.reply_text(
                "Invalid chat. Select a username from the keyboard.",
            )
            return cls._DELETE_CHAT_STATE

        if cls._chat_settings().remove_chat(username):
            await update.message.reply_text(
                f"Deleted chat '{username}'.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"Chat '{username}' not found.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @classmethod
    def get_handlers(cls) -> list:
        return [
            CommandHandler(BotCommandType.CHATS, cls._list_chats),
            ConversationHandler(
                entry_points=[
                    CommandHandler(BotCommandType.ADD_CHAT, cls._start_add_chat)
                ],
                states={
                    cls._ADD_CHAT_STATE: [cls._get_message_handler(cls._add_chat)],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
            ConversationHandler(
                entry_points=[
                    CommandHandler(BotCommandType.DELETE_CHAT, cls._start_delete_chat)
                ],
                states={
                    cls._DELETE_CHAT_STATE: [
                        cls._get_message_handler(cls._delete_chat)
                    ],
                },
                fallbacks=[CommandHandler("cancel", cls._cancel)],
            ),
        ]
