from message_handlers.base import BaseMessageHandler
from utilities.imports import get_all_subclasses


def get_all_message_handlers() -> list[BaseMessageHandler]:
    return get_all_subclasses(
        base_class=BaseMessageHandler,
        package_name="message_handlers",
    )
