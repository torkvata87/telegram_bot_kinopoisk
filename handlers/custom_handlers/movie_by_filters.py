from datetime import datetime

from telebot.util import content_type_media
from telebot.types import Message, CallbackQuery

from config_data.config import IMAGE_MOVIE_BY_FILTERS

from keyboards.inline.inline_keyboard import create_inline_keyboard
from keyboards.inline.inline_movie_by_filters import (
    select_filters_keyboard,
    select_type_keyboard,
    select_genres_keyboard,
    select_countries_keyboard
)
from keyboards.buttons.btns_for_movie_by_filters import (
    btns_filters,
    btns_movies_type,
    buttons_re_entry_year,
    buttons_countries,
    buttons_other_countries,
    buttons_sorting,
    buttons_sort_type,
    buttons_sort_direction,
    buttons_genres,
    all_countries,
    list_ratings
)

from services.services_api import run_search_query
from services.services_pagination_handlers import send_movie_pagination
from services.services_movie_by_filters import (
    format_genres_string,
    format_filters_to_string,
    format_filter_data,
    generate_filter_parameters,
    data_filters,
    is_valid_year,
    set_letter,
    format_genres_list,
    normalize_year_range
)
from services.services_database import (
    update_database,
    update_database_query
)
from services.services_logging import error_logger_bot

from logs.logging_config import log

from loader import bot
from states.search_fields import SearchStates, PaginationStates
from database.common.models_movies import BaseMovie
from database.core import crud_images


@bot.message_handler(commands=["movie_by_filters"])
@error_logger_bot
def menu_movie_by_filters(message: Message) -> None:
    """
    Обработчик команды /movie_by_filters.

    Действия:
        - Выполняет сброс состояния и всех данных, связанных с текущей сессией пользователя.
        - Устанавливает состояние пользователя на `SearchStates.query`.
        - Сохраняет изображение для команды `movie_by_filters` в базе данных ImageFile для быстрого к нему доступа
        при повторном использовании.
        - Отправляет в чат изображение с пояснительным текстом и инлайн-клавиатуру для выбора фильтров.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения с командой `movie_by_filters`.

    Raises:
        FileNotFoundError: Если файл изображения не найден, отправляется сообщение с ошибкой.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, SearchStates.query, chat_id)

    db_get_image = crud_images.get_image()
    db_save = crud_images.save_image()

    image_name = "movie_by_filters"
    file_id = db_get_image(chat_id, image_name)
    caption = "🔍 <b>Поиск фильма <i>по фильтрам</i></b>."
    try:
        if file_id:
            bot.send_photo(
                chat_id,
                file_id,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            with open(IMAGE_MOVIE_BY_FILTERS, "rb") as image:
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

    text = (
        "✔️ Задайте <b><i>фильтры</i></b> с помощью кнопок ниже "
        "либо сразу перейдите к 🔍 <b><i>поиску</i></b>."
    )
    keyboard = select_filters_keyboard(btns_filters, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data in list(btns_filters))
@error_logger_bot
def movie_setting_filters(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки фильтров для задания поиска фильмов по фильтрам.

    Действия:
        - Устанавливает состояние пользователя на основе выбранного фильтра.
        - Отправляет сообщение с параметрами выбранного фильтра и обновленной инлайн-клавиатурой.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного фильтра из списка фильтров.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    state, text, keyboard = data_filters(call.data)

    bot.set_state(user_id, state, chat_id)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(btns_movies_type))
@error_logger_bot
def movie_select_type(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для настройки типа поиска фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.type`, если оно не задано.
        - Обновляет инлайн-клавиатуру при каждом нажатии на заданный параметр фильтра.
        - Сохраняет в хранилище выбранные параметры фильтра `Тип`.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного типа из заданного перечня типов.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.type, chat_id)
        log.info("Состояние 'SearchStates.type' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_movies_type", btns_movies_type.copy())
        data.setdefault("selected_type", [])
        data.setdefault("type", [])
        type_movie = data["buttons_movies_type"].pop(call.data, None)

        if type_movie:
            data["selected_type"].append(type_movie)
            data["type"].append(call.data)

    keyboard = select_type_keyboard(data["buttons_movies_type"], buttons_per_row=3)
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "end_type")
@error_logger_bot
def movie_setting_type(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку фильтра `Завершить ввод` для задания выбранного типа фильма.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Сохраняет выбранные параметры фильтра `Тип` в виде кортежа данных.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Завершить ввод".
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, SearchStates.query, chat_id)
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.type, chat_id)
        log.info("Состояние 'SearchStates.type' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("type_filter", None)

        data.setdefault("type", [])
        data.setdefault("selected_type", ["фильм, сериал"])

    if len(data["type"]) > 0:
        letter = set_letter(data["type"], letter="")
        text = f"📌 Задан{letter} <b><i>тип{letter}</i></b>: <i>{', '.join(data['selected_type'])}</i>"
    else:
        text = "✖️ <b><i>Тип</i></b> не был задан.\n\n📌 По умолчанию выбраны <i>фильм, сериал</i>."
        data["type"] = ["movie", "tv-series"]

    keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(buttons_genres))
@error_logger_bot
def movie_select_genres(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для настройки жанра фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.genres`, если оно не задано.
        - Обновляет инлайн-клавиатуру жанров при каждом нажатии на конкретный жанр.
        - Сохраняет выбранные жанры в данные пользователя.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного жанра из заданного перечня жанров.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.genres, chat_id)
        log.info("Состояние 'SearchStates.genres' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_genres", buttons_genres.copy())
        data.setdefault("selected_genres", [])

        genres = data["buttons_genres"].pop(call.data, None)
        if genres:
            data["selected_genres"].append(f"+{genres}")

    keyboard = select_genres_keyboard(data["buttons_genres"], buttons_per_row=4)
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "exclude_genres")
@error_logger_bot
def movie_exclude_genres(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Исключить` для конкретного жанра фильма.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.genres`, если оно не задано.
        - Сохраняет исключающий паттерн для конкретного жанра в данные пользователя.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Исключить`, добавляющей выбранный жанр фильма в исключенные.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.genres, chat_id)
        log.info("Состояние 'SearchStates.genres' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("selected_genres", [])
        data["selected_genres"].append("!")


@bot.callback_query_handler(func=lambda call: call.data == "end_genres")
@error_logger_bot
def movie_setting_genres(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку фильтра `Завершить ввод` для задания выбранных жанров фильма.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Сохраняет выбранные жанры в виде кортежа в данные пользователя.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Завершить ввод", завершающей выбор жанра.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, SearchStates.query, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("genre_filter", None)

        data.setdefault("selected_genres", [])

        if not data["selected_genres"] or data["selected_genres"] == ["!"]:
            data["genres"] = ["+драма"]
            text = "✖️ <b><i>Жанр</i></b> не был задан.\n\n📌 По умолчанию выбрана <i>драма</i>."
        else:
            data["genres"] = format_genres_list(data["selected_genres"])
            text = f'📌 {format_genres_string(data["genres"])}'

    keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(all_countries))
@error_logger_bot
def movie_select_countries(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора основного списка стран.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.countries`, если оно не задано.
        - Обновляет инлайн-клавиатуру стран при каждом нажатии на заданную страну.
        - Сохраняет выбранные страны в данные пользователя.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранной страны из заданного перечня стран.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.countries, chat_id)
        log.info("Состояние 'SearchStates.countries' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_countries", buttons_countries.copy())
        data.setdefault("buttons_other_countries", buttons_other_countries.copy())
        data.setdefault("selected_countries", [])

    if call.data in data["buttons_countries"]:
        country = data["buttons_countries"].pop(call.data, None)
        keyboard = select_countries_keyboard(
            data["buttons_countries"], buttons_per_row=3, include_other_option=True
        )
    else:
        country = data["buttons_other_countries"].pop(call.data, None)
        keyboard = select_countries_keyboard(
            data["buttons_other_countries"], buttons_per_row=3
        )

    data["selected_countries"].append(country)
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "other_countries")
@error_logger_bot
def movie_select_other_countries(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора дополнительного перечня стран производства фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.countries_input`, если оно не задано.
        - Обновляет инлайн-клавиатуру стран при каждом нажатии на заданную страну.
        - Сохраняет выбранные страны в данные пользователя.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Задать другие", обновляющей перечень стран.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.countries_input, chat_id)
        log.info("Состояние 'SearchStates.countries_input' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("selected_countries", [])

    countries_string = ", ".join(data["selected_countries"])
    letter = set_letter(data["selected_countries"])
    text_input = f"📌 Уже задан{letter}: " if len(countries_string) > 0 else ""
    text = (
        f"{text_input}<i>{countries_string}</>\n\n"
        "✔️ Ознакомьтесь с перечнем <b><i>остальных стран</i></b>:"
    )
    keyboard = select_countries_keyboard(buttons_other_countries, buttons_per_row=3)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "end_countries")
@error_logger_bot
def movie_setting_countries(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку фильтра `Завершить ввод` для задания выбранных стран.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Сохраняет выбранные страны в виде кортежа данных.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Завершить ввод", завершающей выбор стран.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(
        user_id,
        SearchStates.query,
        chat_id,
    )
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data.setdefault("selected_countries", [])
        data["buttons_filters"].pop("country_filter", None)

        if len(data["selected_countries"]) > 0:
            data["countries"] = data["selected_countries"]
            letter = set_letter(data["countries"])
            text = f"📌 Задан{letter} <b><i>стран{letter}</i></b>: <i>{', '.join(data['countries'])}</i>."
        else:
            data["countries"] = None
            text = "✖️ <b><i>Страна</i></b> не была задана."

    keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.message_handler(
    state=SearchStates.year,
    content_types=["text"],
    func=is_valid_year,
)
@error_logger_bot
def movie_setting_year(message: Message) -> None:
    """
    Обработчик ввода текста с заданием года или диапазона лет производства фильмов в состоянии `SearchStates.year`.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Сохраняет заданный год или диапазон лет в данные пользователя в виде строки.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос, и предыдущее сообщение.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения, содержащего год в формате `ГГГГ` или `ГГГГ-ГГГГ` и в диапазоне
            лет от 1920 до текущего года.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    year = normalize_year_range(message.text.strip())

    bot.set_state(user_id, SearchStates.query, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("year_filter", None)
        data["year"] = year

    text_year = "диапазон лет" if "-" in year else "год"
    text = f"Введен <b><i>{text_year}</i></b>: <i>{data['year']}</i>"
    keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, message.message_id)
    bot.delete_message(chat_id, message.message_id - 1)


@bot.message_handler(
    state=SearchStates.year,
    func=lambda message: not message.text.startswith("/"),
    content_types=content_type_media,
)
@error_logger_bot
def handle_not_text_year(message) -> None:
    """
    Обработчик ввода любого текстового контекста, не являющегося командой в состоянии `SearchStates.year`.

    Действия:
    - Отправляет в чат сообщение с инлайн-клавиатурой с предложением пропуска ввод года.
    - Удаляет сообщение, вызвавшее запрос, и предыдущее сообщение.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения, не содержащего год в формате `ГГГГ` или `ГГГГ-ГГГГ` и в диапазоне
            лет от 1920 до текущего года.
    """
    chat_id = message.chat.id
    text = (
        'Год должен быть задан в формате <b>"ГГГГ"</b> или <b>"ГГГГ-ГГГГ"</b> '
        f"и соответствовать диапазону <b>1920-{datetime.now().year}</b>.\n\n"
        'Повторите ✍️ <b><i>ввод</i></b> или выберите <b><i>"❌ Не задавать год"</i></b>'
    )
    keyboard = create_inline_keyboard(buttons_re_entry_year, buttons_per_row=1)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, message.message_id)
    bot.delete_message(chat_id, message.message_id - 1)


@bot.callback_query_handler(func=lambda call: call.data == "skip_year")
@error_logger_bot
def movie_setting_skip_year(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Не задавать год` при вводе года производства фильмов.

    Действия:
    - Устанавливает состояние пользователя `SearchStates.query`.
    - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
    - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Не задавать год", позволяющей пользователю пропустить ввод года.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(
        user_id,
        SearchStates.query,
        chat_id,
    )
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("year_filter", None)

    text = "✖️ <b><i>Год</i></b> не был задан."
    keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list_ratings)
@error_logger_bot
def movie_setting_rating(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора рейтинга фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.rating`, если оно не было задано.
        - Сохраняет при необходимости первый клик по инлайн-кнопке с номером рейтинга, а при втором клике устанавливает
        диапазон рейтинга в данные пользователя в виде строки.
        - Удаляет сохраненный первый клик по инлайн-кнопке с номером рейтинга.
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранной кнопки с цифрой от 0 до 10 для выбора рейтинга фильма.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.rating, chat_id)
        log.info("Состояние 'SearchStates.rating' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("rating_filter", None)

        if data.get("first_click") is None:
            data["first_click"] = call.data
        else:
            first_click = data["first_click"]
            second_click = call.data
            rating = f"{min(int(first_click), int(second_click))}-{max(int(first_click), int(second_click))}"
            data["rating"] = rating
            del data["first_click"]

            bot.set_state(
                user_id,
                SearchStates.query,
                chat_id,
            )
            text = f"📌 Задан <b><i>рейтинг</i></b>: <i>{rating}</i>."
            keyboard = select_filters_keyboard(
                data["buttons_filters"], buttons_per_row=3
            )
            bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
            bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "end_rating")
@error_logger_bot
def movie_setting_rating(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора рейтинга фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.rating`, если оно не было задано.
        - Устанавливает рейтинг на основании первого клика по инлайн-кнопке с номером рейтинга, если он был сохранен,
         либо устанавливает по умолчанию диапазон рейтинга "7-10".
        - Удаляет сохраненный первый клик по инлайн-кнопке с номером рейтинга.
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Сохраняет рейтинг или диапазон рейтинга в данные пользователя в виде строки.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранной кнопки с цифрой от 0 до 10 для выбора рейтинга фильма.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.rating, chat_id)
        log.info("Состояние 'SearchStates.rating' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("rating_filter", None)

        data.setdefault("first_click", None)
        if data["first_click"]:
            rating = data["first_click"]
            text = f"📌 Задан <b><i>рейтинг</i></b>: <i>{rating}</i>."
        else:
            rating = "7-10"
            text = ("✖️ <b><i>Рейтинг</i></b> не был задан.\n\n📌 По умолчанию задан <b><i>рейтинг</i></b>: "
                    f"<i>{rating}</i>.")
        del data["first_click"]
        data["rating"] = rating

    bot.set_state(
        user_id,
        SearchStates.query,
        chat_id,
    )

    keyboard = select_filters_keyboard(
        data["buttons_filters"], buttons_per_row=3
    )
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(buttons_sorting))
@error_logger_bot
def movie_setting_sorting(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора вариантов сортировки фильмов.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.sorting`.
        - Отправляет в чат сообщение с инлайн-клавиатурой типа либо направления сортировки.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки с вариантом сортировки - типа либо направления сортировки.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, SearchStates.sorting, chat_id)

    text = f"✔️ Задайте <b><i>{buttons_sorting[call.data]}</i></b> <i>сортировки</i>."

    keyboard_1 = create_inline_keyboard(buttons_sort_type, buttons_per_row=2)
    keyboard_2 = create_inline_keyboard(buttons_sort_direction, buttons_per_row=1)
    keyboard = keyboard_1 if call.data == "type_sorting" else keyboard_2

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data
    in list(buttons_sort_type) + list(buttons_sort_direction)
)
@error_logger_bot
def movie_setting_type_or_direction_sort(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для выбора типа или направления сортировки.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.sorting`, если оно не задано.
        - В зависимости от инлайн-клавиатуры, устанавливается состояние `SearchStates.sort_type`
        или `SearchStates.sort_direction`.
        - Сохраняет заданные пользователем параметры сортировки.
        - Отправляет в чат сообщение с обновленной инлайн-клавиатурой сортировки или фильтров.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранного варианта сортировки из объединенных перечней типа
            и направления сортировки.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        bot.set_state(user_id, SearchStates.sorting, chat_id)
        log.info("Состояние 'SearchStates.sorting' было задано вновь.")

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("buttons_sorting", buttons_sorting.copy())

        if call.data in buttons_sort_type:
            data["type_sort"] = call.data
            data["sort"] = data.get("sort", "1")
            data["buttons_sorting"].pop("type_sorting", None)

            sorting = buttons_sort_type[call.data]
            text_click = "направление"
            state = SearchStates.sort_type

        elif call.data in buttons_sort_direction:
            data["sort"] = "1" if call.data == "ascending" else "-1"
            data["text_sort"] = (
                "по возрастанию" if data["sort"] == "1" else "по убыванию"
            )
            data["buttons_sorting"].pop("direction_sorting", None)

            sorting = data["text_sort"]
            text_click = "тип"
            state = SearchStates.sort_direction

    bot.set_state(user_id, state, chat_id)

    if data["buttons_sorting"]:
        text_add = f"\n\n✔️ Задайте <b><i>{text_click}</i></b> сортировки"
        keyboard = create_inline_keyboard(data["buttons_sorting"], buttons_per_row=1)
    else:
        bot.set_state(user_id, SearchStates.query, chat_id)
        data.setdefault("buttons_filters", btns_filters.copy())
        data["buttons_filters"].pop("sort_filter", None)
        sorting = f'{buttons_sort_type[data["type_sort"]]}, {data["text_sort"]}'
        text_add = ""
        keyboard = select_filters_keyboard(data["buttons_filters"], buttons_per_row=3)

    text = f"📌 Задана <b><i>сортировка</i></b>: <i>{sorting}</i>{text_add}."
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "filters_default")
@error_logger_bot
def movie_filters_default(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Посмотреть заданные фильтры`.

    Действия:
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Формирует данные для выполнения поиска и строковое представление заданных пользователем фильтров.
        - Отправляет в чат сообщение с инлайн-клавиатурой фильтров с возможностью задать все фильтры заново.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Посмотреть заданные фильтры`, позволяющей посмотреть фильтры, заданные
        пользователем или установленные по умолчанию.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, SearchStates.query, chat_id)

    with bot.retrieve_data(user_id, call.message.chat.id) as data:
        filters_movie = generate_filter_parameters(data)
        get_data = format_filter_data(filters_movie)
        string_data = format_filters_to_string(get_data)
    text = (
        f"📌 Заданы <b><i>фильтры</i></b>:\n\n{string_data}\n\n"
        "🔄️ Здесь вы можете также <b><i>перезаписать уже заданные фильтры</i></b>."
    )
    keyboard = select_filters_keyboard(btns_filters, buttons_per_row=2)
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "search_start")
@error_logger_bot
def search_universal_movies(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Выполнить поиск`.

    Действия:
        - Устанавливает состояние пользователя `PaginationStates.movies`.
        - Выполняет поиск по базе данных "base_movies".
        - Если поисковый запрос существует в базе данных BaseMovie, то старые данные по этому запросу
        удаляет и перезаписывает с новым `id` поискового запроса и текущей датой. Аналогично обновляет строку
        поискового запроса в базе данных QueryString.
        - Если поисковый запрос в базе данных BaseMovie не найден, то выполняет поиск фильмов по API
        сайта Кинопоиск. Поисковый запрос регистрирует в базе данных QueryString. Результаты поискового
        запроса записывает в базу данных BaseMovie.
        - На основе полученных результатов из базы данных или API формирует словарь фильмов, который передает
        в пагинацию.
        - Выводит результат поиска фильмов по названию в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос и предыдущее сообщение.
        - При отсутствии результатов поиска отправляет в чат сообщение с предложением заново ввести название фильма
        и устанавливает состояние SearchStates.movie_name.
        - Устанавливает состояние пользователя `SearchStates.query`.
        - Обрабатывает заданные пользователем фильтры для поиска фильмов и формирует запрос.
        - По сформированному запросу выполняет поиск по базе данных "base_movies" или API сайта Кинопоиск.
        - На основе полученных результатов из базы данных или API формирует словарь фильмов.
        - Устанавливает состояние пользователя `PaginationStates.movies`.
        - Выводит результат поиска фильмов по фильтрам в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.
        - При отсутствии результатов поиска отправляет в чат сообщение с инлайн-клавиатурой фильтров
        с очисткой хранилища от сохраненных данных.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки `Выполнить поиск`.

    Returns:
        None: Если результаты поиска не найдены, отправляется сообщение с предложением задать другие фильтры,
            и выполнение функции завершается.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.set_state(user_id, SearchStates.query, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        filters_movie = generate_filter_parameters(data, for_search=False)
        filters_false = generate_filter_parameters(data, for_search=True)
        get_data = format_filter_data(filters_movie, for_database=True)
        string_data_base = format_filters_to_string(get_data, for_database=True)
        data.clear()
        type_search = "movie_by_filters"

        bot.set_state(user_id, PaginationStates.movies, chat_id)
        text_search = string_data_base

        user_movies = BaseMovie.select().where(
            (BaseMovie.user_id == user_id) & (BaseMovie.text_search == text_search)
        )
        if user_movies:
            total_pages = 2
            movie_info = update_database(user_movies, type_search)
            update_database_query(user_id, text_search, type_search)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            movie_info, total_pages = run_search_query(
                call,
                search_criteria=filters_false,
                type_search=type_search,
                text_search=text_search,
            )
        if not movie_info:
            return

        data["search"] = filters_false
        data["page"] = 1
        data["pages"] = total_pages
        data["movie_info"] = movie_info
        send_movie_pagination(
            chat_id,
            movies_data=movie_info,
            total_pages=total_pages,
        )
