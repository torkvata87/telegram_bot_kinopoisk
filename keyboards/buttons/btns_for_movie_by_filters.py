from typing import Dict, List


btns_filters: Dict[str, str] = {
    "type_filter": "🎞️ Тип",
    "genre_filter": "🎭 Жанр",
    "country_filter": "🌍 Страна",
    "year_filter": "🗓️ ️️️️Год",
    "rating_filter": "🏆 Рейтинг",
    "sort_filter": "↕️ Сортировка",
}

btns_movies_type: Dict[str, str] = {
    "movie": "фильм",
    "tv-series": "сериал",
    "cartoon": "мультфильм",
    "anime": "аниме",
    "animated-series": "мультсериал",
}

buttons_genres: Dict[str, str] = {
    "biografiya": "биография",
    "boevik": "боевик",
    "vestern": "вестерн",
    "voennyy": "военный",
    "detektiv": "детектив",
    "detskiy": "детский",
    "dlya-vzroslyh": "18+",
    "dokumentalnyy": "д/ф",
    "drama": "драма",
    "igra": "игра",
    "istoriya": "история",
    "komediya": "комедия",
    "kriminal": "криминал",
    "melodrama": "мелодрама",
    "myuzikl": "мюзикл",
    "muzyka": "музыка",
    "priklyucheniya": "приключения",
    "semeynyy": "семейный",
    "sport": "спорт",
    "triller": "триллер",
    "uzhasy": "ужасы",
    "fantastika": "фантастика",
    "fentezi": "фэнтези",
    "film-nuar": "фильм-нуар",
}

buttons_countries: Dict[str, str] = {
    "Avstraliya": "Австралия",
    "Argentina": "Аргентина",
    "Belarus": "Беларусь",
    "Velikobritaniya": "Великобритания",
    "Vengriya": "Венгрия",
    "Germaniya": "Германия",
    "Gonkong": "Гонконг",
    "Izrail": "Израиль",
    "Indiya": "Индия",
    "Ispaniya": "Испания",
    "Islandiya": "Исландия",
    "Italiya": "Италия",
    "Kazahstan": "Казахстан",
    "Kanada": "Канада",
    "Kitay": "Китай",
    "Koreya-Yuzhnaya": "Корея Южная",
    "Meksika": "Мексика",
    "Niderlandy": "Нидерланды",
    "Norvegiya": "Норвегия",
    "Polsha": "Польша",
    "Rossiya": "Россия",
    "SSSR": "СССР",
    "SShA": "США",
    "Turciya": "Турция",
    "Ukraina": "Украина",
    "Franciya": "Франция",
    "Yaponiya": "Япония",
}

buttons_other_countries: Dict[str, str] = {
    "Avstriya": "Австрия",
    "Armeniya": "Армения",
    "Belgiya": "Бельгия",
    "Bolgariya": "Болгария",
    "Braziliya": "Бразилия",
    "Greciya": "Греция",
    "Gruziya": "Грузия",
    "Daniya": "Дания",
    "Egipet": "Египет",
    "Iran": "Иран",
    "Irlandiya": "Ирландия",
    "Latviya": "Латвия",
    "Litva": "Литва",
    "Portugaliya": "Португалия",
    "Rumyniya": "Румыния",
    "Serbiya": "Сербия",
    "Singapur": "Сингапур",
    "Slovakiya": "Словакия",
    "Sloveniya": "Словения",
    "Tadzhikistan": "Таджикистан",
    "Tailand": "Таиланд",
    "Uzbekistan": "Узбекистан",
    "Finlyandiya": "Финляндия",
    "Horvatiya": "Хорватия",
    "Chehiya": "Чехия",
    "Shveycariya": "Швейцария",
    "Shveciya": "Швеция",
}

all_countries = buttons_countries.copy()
all_countries.update(buttons_other_countries)

buttons_re_entry_year: Dict[str, str] = {"skip_year": "❌ Не задавать год"}

list_ratings: List[str] = [str(index) for index in range(1, 11)]

buttons_sorting: Dict[str, str] = {
    "type_sorting": "🔃 Тип",
    "direction_sorting": "↕️ Направление",
}

buttons_sort_type: Dict[str, str] = {
    "name": "по названию",
    "year": "по году выпуска",
    "rating.kp": "по рейтингу",
    "ageRating": "по возрасту+",
    "top10": "Топ-10",
    "top250": "Топ-250",
}

buttons_sort_direction: Dict[str, str] = {
    "descending": "⬇️ По убыванию",
    "ascending": "⬆️ По возрастанию",
}

btn_filters_default: Dict[str, str] = {"filters_default": "Посмотреть заданные фильтры"}
