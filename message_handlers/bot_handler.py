from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from enums.settings import BotCommandType
from message_handlers.base import BaseMessageHandler, state_handler


class GeneralBotHandler(BaseMessageHandler):
    @classmethod
    @state_handler
    async def __help_command(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        text = "\n".join(
            [
                f"/{command_type.value} - {command_type.replace("_", " ")}"
                for command_type in BotCommandType
            ]
        )
        await update.message.reply_text(text)

    @classmethod
    def get_handlers(cls) -> list:
        return [
            CommandHandler(BotCommandType.HELP.value, cls.__help_command),
        ]
