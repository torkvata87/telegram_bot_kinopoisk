# 🤖 Телеграм-бот для поиска фильмов на базе Кинопоиск
<div align="center">
    <img src="https://github.com/user-attachments/assets/d4024239-2b78-4119-b806-d781cd2c5a77" alt="Описание изображения" height="300"/>
    <img src="https://github.com/user-attachments/assets/b08d1bd4-0818-4489-bf6a-9fa7809ee61f" alt="Описание изображения" height="300"/>
    <img src="https://github.com/user-attachments/assets/960d0e78-e411-4d4d-a76e-7993b3cb0472" alt="Описание изображения" height="300"/>
    <img src="https://github.com/user-attachments/assets/f235c694-cbd0-4136-8392-09dead8bea10" alt="Описание изображения" height="300"/>
    <img src="https://github.com/user-attachments/assets/03ca70ac-8ae7-433d-8e91-4453f58aea32" alt="Описание изображения" height="300"/>
    <img src="https://github.com/user-attachments/assets/b5f17168-fb8c-4984-b2e6-3730382c7c0f" alt="Описание изображения" height="300"/>
</div>


## 🎬 Описание
Этот Телеграм-бот позволяет пользователям искать фильмы и сериалы на базе сайта Кинопоиск (http://www.kinopoisk.ru/). Он поддерживает несколько полезных функций, таких как поиск по названию или фильтрам, управление избранными и просмотренными фильмами, а также просмотр истории поисковых запросов.

## 📜 Основные команды
| Команда             | Описание                                   |
|---------------------|--------------------------------------------|
| `/start`            | Запустить бота                             |
| `/movie_search`     | Поиск фильма по названию                   |
| `/movie_by_filters` | Поиск фильмов/сериалов по фильтрам         |
| `/postponed_movies` | Просмотр избранных и просмотренных фильмов |
| `/history`          | Управление историей поисковых запросов     |
| `/help`             | Справка по использованию бота              |

## 🚀 Основные возможности

### Поиск фильмов по названию:
- Поисковый запрос обрабатывается для повышения точности: бот отбрасывает окончания слов и гласные буквы для более релевантных результатов.

### Поиск фильмов по фильтрам:
- Возможность поиска фильмов и сериалов по различным критериям, включая типы, жанры, страны, год выпуска, рейтинг и сортировка.
- Возможность исключения определенных жанров из поиска.

### Избранное и просмотренное:
- В базу данных сохраняются все фильмы, помеченные как "избранное" и "просмотренное".
- Динамическое обновление пагинации при смене статуса фильма просмотренного или избранного.

### История поисковых запросов:
- Все поисковые запросы сохраняются и обновляются по дате (от самого нового к самому старому).
- В истории можно фильтровать запросы по периоду (неделя, месяц, конкретная дата, вся история) и типу (по названию или по фильтрам).
- Возможность очистки истории по выбранным параметрам.

### Интерактивный интерфейс:
- Основной функционал реализован через инлайн-клавиатуру, что упрощает взаимодействие с ботом.
- Ввод через клавиатуру требуется только для указания названия фильма или года.

### Пагинация:
- Результаты поиска и история запросов отображаются с помощью пагинации, что делает их удобными для просмотра.
- При большом количестве результатов, выданных сервером, реализована возможность "бесконечного" просмотра фильмов. По умолчанию пагинация отображает до 15 фильмов, но на 15-й странице появляется кнопка "Дальше", которая позволяет загружать следующие результаты, если они предоставлены сервером.

### Фильтрация фильмов:
- Бот отображает только те фильмы, в чьих названиях содержится хотя бы одно слово из поискового запроса.
- Все фильмы, выдаваемые ботом, обязательно содержат описание.
- Если постер фильма недоступен, бот выводит изображение с надписью "Постер отсутствует".

### Забавные изображения:
- Каждая команда сопровождается изображением ежика, сгенерированным нейросетью Kandinsky.
- Изображения команд с ежиком сохраняются и загружаются повторно при необходимости.

### Обработка ошибок:
- Все ошибки логируются в файл, а пользователю показывается уведомление о проблеме.
- В случае истечения сессии просмотра фильмов бот предложит выполнить новый поиск фильмов.

## 🛠 Установка и настройка

### Установка зависимостей:
Перед запуском бота установите все необходимые библиотеки, выполнив команду:

```bash
pip install -r requirements.txt
```
### Настройка переменных окружения:
Создайте файл `.env` с необходимыми параметрами:
```bash
BOT_TOKEN=<Ваш токен Telegram Bot API (получить можно от BotFather в Телеграм)>
API_KEY=<Ваш токен Кинопоиск API (получить можно по ссылке https://kinopoisk.dev/)>
API_URL='https://api.kinopoisk.dev'
```
## Запуск
После настройки всех параметров, запустите бота:
```bash
python bot.py
```
## 🤖 Как пользоваться ботом
- При первом запуске используйте команду `/start` для начала работы.
- Для поиска фильма введите команду `/movie_search` и название фильма.
- Для фильтрации фильмов по параметрам используйте команду `/movie_by_filters`.
- Для просмотра избранных фильмов и управления просмотренным списком используйте `/postponed_movies`.
- Историей поиска можно управлять с помощью команды `/history`.

## 📚 Поддерживаемые библиотеки
- `pyTelegramBotAPI` — основная библиотека для работы с Telegram API.
- `loguru` — для логирования событий.
- `peewee` — ORM для работы с базами данных.
- `pydantic-settings` — для управления настройками и конфигурацией.
- `python-dotenv` — для работы с файлами `.env`.
- `python-telegram-bot-pagination` — для отображения сообщений в виде пагинации.
- `requests` — библиотека для выполнения HTTP-запросов.

## 📩 Обратная связь
Для обратной связи и вопросов по работе бота отправьте письмо на почту torkvata87@gmail.com.
