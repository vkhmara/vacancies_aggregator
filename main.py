import asyncio
import logging
import os
from telegram.ext import Application
from message_handlers import get_all_message_handlers
from message_handlers.base import set_commands
from utilities.list import join_lists


def main():
    if os.getenv("DEBUG"):
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))
        debugpy.wait_for_client()
    logging.basicConfig(level=logging.INFO)
    tg_token = os.getenv("TG_TOKEN")

    message_handlers = get_all_message_handlers()
    app: Application = Application.builder().token(tg_token).build()

    app.add_handlers(
        join_lists(
            message_handler.get_handlers() for message_handler in message_handlers
        )
    )
    # Cannot be replaced with asyncio.run(set_commands(app))
    #  because of RuntimeError('Event loop is closed')
    asyncio.get_event_loop().run_until_complete(set_commands(app))

    app.run_polling()


if __name__ == "__main__":
    main()
