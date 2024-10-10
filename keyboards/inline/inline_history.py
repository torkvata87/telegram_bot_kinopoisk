from typing import Dict

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import Query

from config_data.config import DATE_FORMAT, DATE_FORMAT_STRING
from keyboards.inline.inline_keyboard import create_inline_keyboard
from services.services_logging import error_logger_func, raises_keyboard

from logs.logging_config import log


@error_logger_func
def create_date_selection_keyboard(
        date_query: Query, buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора дат.

    Эта функция принимает результаты запроса на получение уникальных дат из базы данных и создает инлайн-клавиатуру
    с кнопками, представляющими эти даты. Каждая кнопка отображает дату в формате `DATE_FORMAT_STRING` и передает
    её в формате `DATE_FORMAT` через `callback_data`.

    Args:
        date_query (Query): Запрос, возвращающий набор уникальных дат для отображения на кнопках.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора дат.

    Raises:
        TypeError: Если `date_query` не является запросом `Query`, либо если `buttons_per_row` не является целым числом.
        ValueError: Если `buttons_per_row` меньше или равен нулю.
        AttributeError: Если объект `dates.date_search` не имеет метода `strftime.
    """

    if not isinstance(date_query, Query):
        raise TypeError("date_query должен быть экземпляром класса Query")
    if not isinstance(buttons_per_row, int):
        raise TypeError("buttons_per_row должен быть целым числом")
    if buttons_per_row <= 0:
        raise ValueError("buttons_per_row должен быть положительным числом больше нуля")
    keyboard = InlineKeyboardMarkup()
    buttons = []
    try:

        for dates in date_query:
            button = InlineKeyboardButton(
                text=dates.date_search.strftime(DATE_FORMAT_STRING),
                callback_data=f"date#{dates.date_search.strftime(DATE_FORMAT)}",
            )
            buttons.append(button)

        for i in range(0, len(buttons), buttons_per_row):
            keyboard.row(*buttons[i: i + buttons_per_row])
        return keyboard
    except AttributeError as exc:
        log.error(f"Ошибка при работе с датой: {str(exc)}")


@error_logger_func
def history_clear_select(
        button_labels: Dict[str, str], buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для очистки истории с возможностью возврата в меню.

    Args:
        button_labels (Dict[str, str]): Запрос, возвращающий набор уникальных дат для отображения на кнопках.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора вариантов очистки истории.

     Raises:
        TypeError: Если `button_labels` не является словарем или если `buttons_per_row` не является целым числом.
        ValueError: Если `buttons_per_row` меньше или равен нулю.
        KeyError: Если `button_labels` содержит некорректные ключи для создания кнопок.
    """
    raises_keyboard(button_labels, buttons_per_row)
    keyboard = create_inline_keyboard(button_labels, buttons_per_row)
    button = InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="history_menu")
    keyboard.add(button)

    return keyboard
