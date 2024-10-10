from datetime import datetime, timedelta

from peewee import fn
from telebot.types import Message, CallbackQuery

from config_data.config import DATE_FORMAT, DATE_FORMAT_STRING, IMAGE_HISTORY

from keyboards.inline.inline_history import (
    history_clear_select,
    create_date_selection_keyboard
)
from keyboards.inline.inline_keyboard import create_inline_keyboard
from keyboards.buttons.btns_history import (
    buttons_history,
    btns_history_period,
    btns_history_type,
    btns_history_clear,
    btns_history_filters,
    btns_clear_confirm
)

from services.services_pagination_handlers import send_history_pagination
from services.services_database import sending_to_history_pagination
from services.services_history import (
    get_history_query_type,
    get_history_query_string,
    history_query_type_clear
)

from services.services_logging import error_logger_bot

from logs.logging_config import log

from loader import bot
from states.search_fields import HistoryStates, PaginationStates
from database.common.models_movies import BaseMovie, QueryString
from database.core import crud_images


@bot.message_handler(commands=["history"])
@error_logger_bot
def menu_history(message: Message) -> None:
    """
    Обработчик команды /history.

    Действия:
        - Выполняет сброс состояния и всех данных, связанных с текущей сессией пользователя.
        - Устанавливает состояние пользователя `HistoryStates.query`.
        - Сохраняет изображение для команды `history` в базе данных ImageFile для быстрого к нему доступа
        при повторном использовании.
        - Проверяет наличие истории запросов в базе данных BaseMovie.
        - Отправляет сообщение с изображением и сообщение в чат с инлайн-клавиатурой.
        - Сохраняет кнопки инлайн-клавиатуры для последующей их обработки.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения с командой `history`.

    Raises:
        FileNotFoundError: Если файл изображения не найден, отправляется сообщение с ошибкой.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, HistoryStates.query, chat_id)

    db_get_image = crud_images.get_image()
    db_save = crud_images.save_image()
    image_name = "history"
    file_id = db_get_image(chat_id, image_name)

    caption = "📚 <b>Управление историей поисковых запросов</b>."

    try:
        if file_id:
            bot.send_photo(
                chat_id,
                file_id,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            with open(IMAGE_HISTORY, "rb") as image:
                sent_message = bot.send_photo(
                    chat_id,
                    image,
                    caption=caption,
                    parse_mode="HTML",
                )
                db_save(chat_id, image_name, sent_message.photo[-1].file_id)
    except FileNotFoundError as exc:
        log.error(f"Ошибка при обработке изображения: {type(exc)} - {exc}")
        bot.send_message(chat_id, caption, parse_mode="HTML")

    user = BaseMovie.get_or_none(BaseMovie.user_id == user_id)
    if user is None:
        text = (
            "🗑️ Сейчас <b>история</b> ваших поисковых запросов <b><i>пуста</i></b>.\n\n"
            "🔍 Создавайте новые поисковые запросы и возвращайтесь сюда позднее ⌛."
        )
        keyboard = None
    else:
        text = (
            "📖 Ознакомьтесь с <b><i>историей</i></b> своих поисковых запросов "
            "либо 🗑️ <b><i>очистите хранилище</i></b>."
        )
        keyboard = create_inline_keyboard(buttons_history, buttons_per_row=1)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "query_history")
@error_logger_bot
def history_setting_filters(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку "История запросов".

    Действия:
        - Устанавливает состояние пользователя "HistoryStates.filters".
        - Отправляет сообщение с инлайн-клавиатурой фильтров в чат.
        - Сохраняет кнопки инлайн-клавиатуры для последующей их обработки.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "История запросов".
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id

    bot.set_state(user_id, HistoryStates.filters, chat_id)

    text = "✔️ Задайте <b><i>фильтры</i></b> отображения поисковых запросов."
    keyboard = create_inline_keyboard(btns_history_filters, buttons_per_row=2)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "viewing_period")
@error_logger_bot
def history_filter_period(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку фильтра "Период".

    Действия:
        - Отправляет сообщение с инлайн-клавиатурой параметров заданного фильтра в чат.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Период", позволяющей задать период просмотра поисковых запросов.
    """
    chat_id = call.message.chat.id
    text = "✔️ Задайте <b><i>период</i></b> отображения своей истории поисков:"
    keyboard = create_inline_keyboard(btns_history_period, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(btns_history_period))
@error_logger_bot
def history_setting_period(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для настройки периода истории поиска.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.period`.
        - Сохраняет параметры выбранного фильтра в данные пользователя.
        - Отправляет сообщение с выбранным периодом в чат.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного периода поисковых запросов из заданного перечня периодов.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id

    bot.set_state(user_id, HistoryStates.period, chat_id)

    if call.data != "by_date":
        with bot.retrieve_data(user_id, chat_id) as data:
            data.setdefault("btns_history_filters", btns_history_filters.copy())
            data["btns_history_filters"].pop("viewing_period", None)

            data["history_period"] = btns_history_period[call.data]

        text = f'📌 Задан <b><i>фильтр</i></b> <i>"{data["history_period"]}"</i>'
        keyboard = create_inline_keyboard(
            data["btns_history_filters"], buttons_per_row=1
        )
    else:
        history_dates = (
            QueryString.select(fn.DATE(QueryString.date_search).alias("date_search"))
            .distinct()
            .where(
                (QueryString.user_id == user_id)
                & (QueryString.date_search >= datetime.now() - timedelta(weeks=2))
            )
            .order_by(fn.DATE(QueryString.date_search).desc())
        )

        text = "✔️ Задайте <b><i>дату</i></b> поискового запроса:"
        keyboard = create_date_selection_keyboard(history_dates, buttons_per_row=3)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split("#")[0] == "date")
@error_logger_bot
def history_period_by_date(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку периода истории поиска `по дате`.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.date`.
        - Сохраняет параметры периода дат с необходимым форматом в данные пользователя.
        - Отправляет сообщение с выбранным периодом пользователю с обновленной инлайн-клавиатурой параметров
        заданного фильтра.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки выбранной даты поискового запроса.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    date_str = call.data.split("#")[1]
    bot.set_state(user_id, HistoryStates.date, chat_id)
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("btns_history_filters", btns_history_filters.copy())
        data["btns_history_filters"].pop("viewing_period")

        data["history_period"] = "по дате"
        data["history_date"] = datetime.strptime(date_str, DATE_FORMAT).date()
        display_date = data["history_date"].strftime(DATE_FORMAT_STRING)

    text = (
        f'📌 Задан <b><i>период</i></b> поисковых запросов <i>"по дате"</i> '
        f"за <i>{display_date}</i>"
    )
    keyboard = create_inline_keyboard(data["btns_history_filters"], buttons_per_row=1)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "view_by_type")
@error_logger_bot
def history_filter_tipe(call: CallbackQuery) -> None:
    """
    Обрабатывает нажатие на инлайн-кнопку фильтра `Тип`.

    Действия:
        - Отправляет сообщение с выбранным типом в чат с инлайн-клавиатурой параметров заданного фильтра.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Тип`, позволяющей задать тип просмотра поисковых запросов.
    """
    chat_id = call.message.chat.id
    text = "✔️ Задайте <b><i>тип</i></b> просмотра истории поисков:"
    keyboard = create_inline_keyboard(btns_history_type, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(btns_history_type))
@error_logger_bot
def history_setting_type(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для настройки типа истории поиска.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.type`.
        - Сохраняет параметры выбранного фильтра в данные пользователя.
        - Отправляет сообщение с выбранным типом в чат с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного типа поискового запроса из заданного перечня типа.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, HistoryStates.type, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("btns_history_filters", btns_history_filters.copy())
        data["btns_history_filters"].pop("view_by_type")

        data["history_type"] = btns_history_type[call.data]

    text = f"📌 Задан <b><i>фильтр</i></b> <i>{data['history_type']}</i>"
    keyboard = create_inline_keyboard(data["btns_history_filters"], buttons_per_row=1)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "apply_filters")
@error_logger_bot
def history_apply_filters(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на инлайн-кнопку `Посмотреть историю` с выводом истории поиска по заданным пользователем
    параметрам.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.query`.
        - Обрабатывает заданные пользователем параметров для вывода истории поиска.
        - Если данные по заданным параметрам в базе данных отсутствуют, устанавливает параметр вывода поисковых
        запросов за все время.
        - На основе заданных параметров считывает информацию из базы данных QueryString и формирует словарь поисковых
        запросов.
        - Устанавливает состояние пользователя `PaginationStates.history`.
        - Выводит историю поисковых запросов по заданным параметрам в виде пагинации.
        - При отсутствии истории поиска по заданным параметрам отправляет в чат сообщение с инлайн-клавиатурой меню
        команды /history с очисткой хранилища от сохраненных данных.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Посмотреть историю`.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id

    bot.set_state(user_id, HistoryStates.query, chat_id)
    history_users = (
        QueryString.select()
        .where(QueryString.user_id == user_id)
        .order_by(QueryString.id.desc())
    )
    with bot.retrieve_data(user_id, chat_id) as data:
        list_filters_history = []

        history_query_type = get_history_query_type(data, history_users)
        history_query_string = get_history_query_string(data, history_query_type)

        if "history_period" in data:
            list_filters_history.append(data["history_period"])
        if "history_type" in data:
            list_filters_history.append(data["history_type"])

        response_query_string = sending_to_history_pagination(history_query_string)
        number = 7

        history_list_page = [
            response_query_string[i : (i + number)]
            for i in range(0, len(response_query_string), number)
        ]
        data.setdefault("history_list_page", history_list_page)
        data.setdefault("page_history", 1)

        data["string_response"] = list_filters_history

        if response_query_string:
            bot.set_state(user_id, PaginationStates.history, chat_id)
            send_history_pagination(
                chat_id,
                data["history_list_page"],
                number_queries_on_page=number,
                string_response=data["string_response"],
                current_page=1,
            )
        else:
            data.clear()
            data["buttons_history"] = buttons_history
            text = (
                "✖️ По указанным фильтрам <b>история просмотров <i>не найдена</i></b>.\n\n"
                "✔️ Задайте другие фильтры."
            )
            keyboard = create_inline_keyboard(
                data["buttons_history"], buttons_per_row=1
            )
            bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
        bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "clear_storage")
@error_logger_bot
def history_clear_storage(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Очистить хранилище`.

    Действия:
        - Отправляет сообщение в чат с инлайн-клавиатурой параметров очистки хранилища.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Очистить хранилище`.
    """
    chat_id = call.message.chat.id
    text = "✔️ Задайте <b><i>параметр</i></b> очистки истории:"
    keyboard = history_clear_select(btns_history_clear, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(btns_history_clear))
@error_logger_bot
def history_setting_clear_storage(call: CallbackQuery) -> None:
    """
    Обрабатывает нажатия на кнопки инлайн-клавиатуры для настройки очистки хранилища.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.clear`.
        - Отправляет сообщение с фильтрами в чат с инлайн-клавиатурой с запросом подтверждения очистки хранилища.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки выбранного варианта очистки хранилища из заданного перечня
            вариантов очистки.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(
        user_id,
        HistoryStates.clear,
        chat_id,
    )
    with bot.retrieve_data(user_id, chat_id) as data:
        data["btns_history_clear"] = btns_history_clear[call.data]

    text = f"❓ Вы действительно хотите <b><i>очистить историю</i></b> <i>{data['btns_history_clear']}</i>?"
    keyboard = create_inline_keyboard(btns_clear_confirm, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "clear_confirm")
@error_logger_bot
def history_clear_confirm(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Подтвердить`.

    Действия:
        - Выполняет очистку хранилища по заданным параметрам.
        - Устанавливает состояние пользователя `HistoryStates.clear`, если оно не было задано.
        - Отправляет сообщение в чат с обновленной инлайн-клавиатурой команды /history.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Подтвердить`.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)
    if not current_state:
        bot.set_state(user_id, HistoryStates.clear, chat_id)
        log.info(
            "Состояние 'HistoryStates.clear' у пользователя отсутствовало и было задано вновь."
        )
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_history", buttons_history.copy())
        data.setdefault("btns_history_clear", None)
        history_query_type_clear(user_id, data)
        history_clear = data["btns_history_clear"]

        if BaseMovie.get_or_none(BaseMovie.user_id == user_id):
            data["buttons_history"].pop("clear_storage")

            text_add = ""
            keyboard = create_inline_keyboard(
                data["buttons_history"], buttons_per_row=1
            )
        else:
            text_add = "\n\n🔍 Создавайте новые поисковые запросы и возвращайтесь сюда позднее ⌛."
            keyboard = None
        text = f"🗑️ Ваша история <b><i>очищена</i></b> <i>{history_clear}</i>.{text_add}"
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "history_menu")
@error_logger_bot
def history_back_menu(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Назад в меню`.

    Действия:
        - Устанавливает состояние пользователя `HistoryStates.query`.
        - Очищает хранилище.
        - Отправляет сообщение в чат с инлайн-клавиатурой меню команды /history.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Назад в меню".
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, HistoryStates.query, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data["buttons_history"] = buttons_history

    text = (
        "📖 Ознакомьтесь с <b><i>историей</i></b> своих поисковых запросов "
        "либо 🗑️ <b><i>очистите хранилище</i></b>."
    )
    keyboard = create_inline_keyboard(buttons_history, buttons_per_row=1)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)
