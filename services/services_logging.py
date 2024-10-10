from typing import Any, Callable, Dict, Tuple
from functools import wraps
import traceback

from telebot.types import Message, CallbackQuery
from telebot.apihelper import ApiTelegramException

from loader import bot
from logs.exception_description import exception_type
from logs.exceptions import BotStatePaginationNotFoundError, ServerRequestError
from logs.logging_config import log

from services.services_utils import set_ids
from states.search_fields import SearchStates


def raises_keyboard(button_labels: Dict[str, str], buttons_per_row: int) -> None:
    """
    Обработка исключений для инлайн-клавиатуры.

    Args:
        button_labels (Dict[str, str]): Словарь с данными для кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        Any | None: Возвращает результат выполнения декорируемой функции или None при возникновении ошибки.

    Raises:
        TypeError: Если `button_labels` не является словарем или `buttons_per_row` не является целым числом.
        ValueError: Если `buttons_per_row` меньше или равен нулю.
    """
    if not isinstance(button_labels, dict):
        raise TypeError("button_labels должен быть словарем типа Dict[str, str]")
    if not isinstance(buttons_per_row, int):
        raise TypeError("buttons_per_row должен быть целым числом")
    if buttons_per_row <= 0:
        raise ValueError("buttons_per_row должен быть положительным числом больше нуля")


def extract_ids(args) -> Tuple[int | None | Any, int | None, int | None]:
    """
    Вспомогательная функция для извлечения chat_id, user_id и message_id из аргументов.

    Args:
        *args: Список аргументов, переданных в декорируемую функцию.

    Returns:
        Tuple[int | None, int | None, int | None]: Кортеж из chat_id, user_id и message_id. Если id не найдены,
            возвращает None.
    """
    if len(args) > 0 and isinstance(args[0], (Message, CallbackQuery, int)):
        if isinstance(args[0], int):
            chat_id = args[0]
            return chat_id, None, None
        else:
            chat_id, user_id, message_id = set_ids(args[0])
        return chat_id, user_id, message_id
    return None, None, None


def handle_exception(func: Callable, exc: Exception) -> None:
    """
    Формирует текст ошибки для логирования.

    Args:
        func (Callable): Декорируемая функция.
        exc (Exception): Исключение.
    """
    line_number = traceback.extract_tb(exc.__traceback__)[-1].lineno

    message = exception_type.get(type(exc), f"Произошла ошибка")
    log.error(
        f"{func.__module__}.{func.__name__}: {line_number} - {type(exc).__name__}: {message} ({exc})."
    )


def error_logger_bot(func: Callable) -> Callable:
    """
        Декоратор для обработки исключений и логирования ошибок в функции-обработчике команд бота.

        Обрабатывает ошибки, возникающие при выполнении функции-обработчика. Он отправляет пользователю
        сообщение об ошибке и очищает сообщение, вызвавшее ошибку. Также устанавливается состояние бота,
        если ошибка связана с истечением сессии отображения фильмов.

        Args:
            func (Callable): Функция-обработчик команды бота, которая может вызывать исключения.

        Returns:
            Callable: Обертка вокруг функции-обработчика, которая включает обработку ошибок и логирование.

        Raises:
            BotStatePaginationNotFoundError: Если возникла ошибка состояния пагинации бота, например, истечение сессии
                отображения фильмов.
            Exception: Для обработки и логирования любых других исключений, которые могут возникнуть при выполнении
                функции-обработчика.
        """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any | None:
        chat_id, user_id, message_id = extract_ids(args)
        try:
            return func(*args, **kwargs)
        except BotStatePaginationNotFoundError as exc:
            handle_exception(func, exc)
            text = (
                "🚫 <b>Сессия отображения фильмов истекла.</b>\n\n"
                "✍️ Введите <b><i>название</i></b> фильма 🎬 "
                "в строку ввода для нового поиска или обратитесь в /help."
            )
            bot.set_state(user_id, SearchStates.movie_name, chat_id)
            bot.send_message(chat_id, text, parse_mode="HTML")
            bot.delete_message(chat_id, message_id)
            return None
        except Exception as exc:
            handle_exception(func, exc)
            text = (
                f"🚫 <b>Произошла ошибка <i>{type(exc).__name__}</i></b>.\n\n"
                "⌛ Зайдите сюда позже или \n✍️ обратитесь в службу поддержки телеграм-бота /help."
            )
            bot.send_message(chat_id, text, parse_mode="HTML")
            try:
                bot.delete_message(chat_id, message_id)
            except ApiTelegramException:
                handle_exception(func, exc)
                return
            return None

    return wrapper


def error_logger_func(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any | None:
        """
        Обёртка для выполнения функции с обработкой исключений.

        Returns:
            Any | None: Возвращает результат выполнения декорируемой функции или None при возникновении ошибки.

        Raises:
            Exception: Пробрасывает исключение, произошедшее в декорируемой функции.
        """
        try:
            return func(*args, **kwargs)
        except ConnectionError as exc:
            handle_exception(func, exc)
            return str(exc)
        except ServerRequestError as exc:
            log.error(f"{type(exc).__name__}: {exc}")
            return str(exc)
        except Exception as exc:
            handle_exception(func, exc)
        return None

    return wrapper
