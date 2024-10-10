from typing import Callable, Tuple
from telebot.types import Message, CallbackQuery


def set_ids(
        message_or_call: Message | Callable,
) -> Tuple[int | None, int | None, int | None]:
    """
    Извлекает и возвращает идентификаторы чата, пользователя и сообщения из объекта сообщения или вызова.

    Args:
        message_or_call (Message | Callable): Объект сообщения или вызова (например, `Message` или `CallbackQuery`),
        из которого извлекаются идентификаторы.

    Returns:
        Tuple[int | None, int | None, int | None]: Кортеж, содержащий:
            - chat_id (int | None): Идентификатор чата (None, если объект не соответствует `Message`
                или `CallbackQuery`).
            - user_id (int | None): Идентификатор пользователя (None, если объект не соответствует `Message`
                или `CallbackQuery`).
            - message_id (int | None): Идентификатор сообщения (None, если объект не соответствует `Message`
                или `CallbackQuery`).

    Raises:
        TypeError: Если `message_or_call` не является объектом типа `Message` или `CallbackQuery`.
    """
    if isinstance(message_or_call, Message):
        chat_id = message_or_call.chat.id
        user_id = message_or_call.from_user.id
        message_id = message_or_call.message_id
    elif isinstance(message_or_call, CallbackQuery):
        chat_id = message_or_call.message.chat.id
        user_id = message_or_call.from_user.id
        message_id = message_or_call.message.message_id
    else:
        raise TypeError("Аргумент должен быть объектом `Message` или `CallbackQuery`.")

    return chat_id, user_id, message_id
