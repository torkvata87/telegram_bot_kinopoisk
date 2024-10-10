from typing import Dict

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.services_logging import error_logger_func, raises_keyboard

from .inline_keyboard import create_inline_keyboard
from ..buttons.btns_for_movie_by_filters import list_ratings


@error_logger_func
def select_type_keyboard(
    button_labels: Dict[str, str], buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора типов фильма с кнопкой `Завершить ввод`.

    Args:
        button_labels (Dict[str, str]): Словарь, где ключи - данные для обратного вызова (`callback_data`),
            а значения - текст кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора типов фильма.
    """
    raises_keyboard(button_labels, buttons_per_row)
    keyboard = create_inline_keyboard(button_labels, buttons_per_row)

    button = InlineKeyboardButton(text="✅ Завершить ввод", callback_data="end_type")

    keyboard.add(button)
    return keyboard


@error_logger_func
def select_genres_keyboard(
    button_labels: Dict[str, str], buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора жанров фильма с кнопкой `Завершить ввод`.

    Args:
        button_labels (Dict[str, str]): Словарь, где ключи - данные для обратного вызова (`callback_data`),
            а значения - текст кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора жанров фильма.
    """
    raises_keyboard(button_labels, buttons_per_row)
    keyboard = create_inline_keyboard(button_labels, buttons_per_row)

    button_1 = InlineKeyboardButton(text="❌ Исключить", callback_data="exclude_genres")
    button_2 = InlineKeyboardButton(
        text="✅ Завершить ввод", callback_data="end_genres"
    )

    keyboard.add(button_1, button_2)
    return keyboard


@error_logger_func
def select_countries_keyboard(
    button_labels: Dict[str, str],
    buttons_per_row: int,
    include_other_option: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора стран, участвовавших в создании фильма,
    с возможностью добавления кнопки `Задать другие` и кнопкой `Завершить ввод`.

    Args:
        button_labels (Dict[str, str]): Словарь, где ключи - данные для обратного вызова (`callback_data`),
            а значения - текст кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.
        include_other_option (bool): Флаг, указывающий, следует ли добавлять кнопку `Задать другие`.
            По умолчанию `False`.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора стран, участвовавших в создании фильма.
    """
    raises_keyboard(button_labels, buttons_per_row)
    keyboard = create_inline_keyboard(button_labels, buttons_per_row)

    button_1 = InlineKeyboardButton(
        text="➡️ Задать другие", callback_data="other_countries"
    )
    button_2 = InlineKeyboardButton(
        text="✅ Завершить ввод", callback_data="end_countries"
    )
    if include_other_option:
        keyboard.add(button_1, button_2)
        return keyboard

    keyboard.add(button_2)
    return keyboard


@error_logger_func
def select_rating_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора рейтинга фильма с кнопкой `Завершить ввод`.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора рейтинга фильма.
    """
    buttons = [InlineKeyboardButton(elem, callback_data=elem) for elem in list_ratings]
    keyboard = InlineKeyboardMarkup(row_width=5)

    for i in range(0, len(buttons), 5):
        keyboard.row(*buttons[i : i + 5])

    button = InlineKeyboardButton(text="✅ Завершить ввод", callback_data="end_rating")
    keyboard.add(button)

    return keyboard


@error_logger_func
def select_filters_keyboard(
    button_labels: Dict[str, str], buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопками для выбора фильтров для создания запроса для поиска фильмов
    с кнопками `Посмотреть заданные фильтры` и `Выполнить поиск`.

    Args:
        button_labels (Dict[str, str]): Словарь, где ключи - данные для обратного вызова (`callback_data`),
            а значения - текст кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для выбора жанров фильма.
    """
    raises_keyboard(button_labels, buttons_per_row)
    keyboard = create_inline_keyboard(button_labels, buttons_per_row)

    button_1 = InlineKeyboardButton(
        text="📋 Посмотреть заданные фильтры", callback_data="filters_default"
    )
    button_2 = InlineKeyboardButton(
        text="🔍 Выполнить поиск", callback_data="search_start"
    )
    keyboard.add(button_1)
    keyboard.add(button_2)

    return keyboard
