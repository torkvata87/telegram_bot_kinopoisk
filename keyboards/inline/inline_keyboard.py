from typing import Dict

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from logs.logging_config import log


def create_inline_keyboard(
    button_labels: Dict[str, str], buttons_per_row: int
) -> InlineKeyboardMarkup:
    """
    Создает универсальную инлайн-клавиатуру с заданным количеством кнопок в строке.

    Args:
        button_labels (Dict[str, str]): Словарь, где ключи - данные для обратного вызова (`callback_data`),
            а значения - текст кнопок.
        buttons_per_row (int): Количество кнопок в одной строке клавиатуры.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура, содержащая кнопки с указанными названиями и callback-данными.
    """
    try:
        if not isinstance(button_labels, dict):
            raise TypeError("button_labels должен быть словарем типа Dict[str, str]")
        if not isinstance(buttons_per_row, int):
            raise TypeError("buttons_per_row должен быть целым числом")
        if buttons_per_row <= 0:
            raise ValueError("buttons_per_row должен быть положительным числом больше нуля")
        buttons = [
            InlineKeyboardButton(value, callback_data=key)
            for key, value in button_labels.items()
        ]
        keyboard = InlineKeyboardMarkup(row_width=buttons_per_row)

        for i in range(0, len(buttons), buttons_per_row):
            keyboard.row(*buttons[i: i + buttons_per_row])

        return keyboard
    except Exception as exc:
        log.error(f"{type(exc).__name__}: {str(exc)}.")
