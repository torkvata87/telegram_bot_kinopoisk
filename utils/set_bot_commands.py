from typing import Any

from telebot.types import BotCommand

from config_data.config import DEFAULT_COMMANDS
from services.services_logging import error_logger_func


@error_logger_func
def set_default_commands(bot: Any) -> None:
    """
    Устанавливает команды по умолчанию для бота.

    Функция создает список команд для бота и устанавливает их с помощью метода `set_my_commands`.
    Каждая команда представлена в виде экземпляра `BotCommand`, который содержит название команды и её описание.

    Args:
        bot (Any): Объект бота, для которого устанавливаются команды. Этот объект должен поддерживать метод
            `set_my_commands`, который принимает список команд в виде объектов `BotCommand`.
    Raises:
        AttributeError: Если объект `bot` не поддерживает метод `set_my_commands`.
        TypeError: Если формат команд в `DEFAULT_COMMANDS` некорректный или объекты `BotCommand` не могут быть созданы.
    """
    try:
        bot.set_my_commands([BotCommand(*elem) for elem in DEFAULT_COMMANDS])
    except AttributeError:
        raise AttributeError("Объект `bot` должен поддерживать метод `set_my_commands`.")
    except TypeError:
        raise TypeError(
            "Формат команд в `DEFAULT_COMMANDS` некорректен или объекты `BotCommand` не могут быть созданы.")
