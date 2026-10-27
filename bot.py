
import urllib.error
import telebot

from config import TOKEN
from database import init_db, get_user, save_user
from currency_service import get_exchange_rate
from keyboards import (
    PROFILE,
    EDIT_PROFILE,
    main_keyboard,
    profile_keyboard,
    USD,
    EUR,
    RUB,
    CNY,
    OTHER_CURRENCY,
    ANOTHER_AMOUNT,
    CURRENCIES,
    currency_keyboard,
    action_keyboard,
)

bot = telebot.TeleBot(TOKEN)

# Запоминаем валюту для каждого чата
user_currencies = {}

# Запоминаем, на каком этапе находится пользователь
user_states = {}

# Запуск бота

@bot.message_handler(commands=["start"])
def start(message):
    telegram_id = message.from_user.id
    user = get_user(telegram_id)

    if user is None:
        user_states[telegram_id] = "register_first_name"
        bot.send_message(
            message.chat.id,
            "Привет! Давай познакомимся 😊\n"
            "Как тебя зовут? Введи своё имя:"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"С возвращением, {user[0]}! 😊\n"
            "Выбери валюту или открой свой профиль:",
            reply_markup=main_keyboard()
        )


# Пользователь вводит имя
@bot.message_handler(
    func=lambda message:
    user_states.get(message.from_user.id) == "register_first_name"
)
def register_first_name(message):
    first_name = (message.text or "").strip()

    if not first_name or len(first_name) > 50:
        bot.send_message(
            message.chat.id,
            "Введи имя текстом, не длиннее 50 символов."
        )
        return

    user_states[message.from_user.id] = "register_last_name"
    user_states[f"{message.from_user.id}_first_name"] = first_name

    bot.send_message(
        message.chat.id,
        "Приятно познакомиться! 😊\n"
        "Теперь введи свою фамилию:"
    )


# Пользователь вводит фамилию
@bot.message_handler(
    func=lambda message:
    user_states.get(message.from_user.id) == "register_last_name"
)
def register_last_name(message):
    last_name = (message.text or "").strip()

    if not last_name or len(last_name) > 50:
        bot.send_message(
            message.chat.id,
            "Введи фамилию текстом, не длиннее 50 символов."
        )
        return

    telegram_id = message.from_user.id
    first_name = user_states.get(f"{telegram_id}_first_name")

    if not first_name:
        user_states[telegram_id] = "register_first_name"
        bot.send_message(message.chat.id, "Введи своё имя:")
        return

    save_user(telegram_id, first_name, last_name)

    user_states.pop(telegram_id, None)
    user_states.pop(f"{telegram_id}_first_name", None)

    bot.send_message(
        message.chat.id,
        f"Готово, {first_name}! 🎉\n"
        "Твои данные сохранены.\n"
        "Теперь можешь пользоваться конвертером валют.",
        reply_markup=main_keyboard()
    )

# Пользователь открывает свой профиль
@bot.message_handler(
    func=lambda message: message.text == PROFILE
)
def show_profile(message):
    telegram_id = message.from_user.id
    user = get_user(telegram_id)

    if user is None:
        user_states[telegram_id] = "register_first_name"
        bot.send_message(
            message.chat.id,
            "Сначала давай познакомимся! Как тебя зовут?"
        )
        return

    bot.send_message(
        message.chat.id,
        f"👤 Твой профиль\n\n"
        f"Имя: {user[0]}\n"
        f"Фамилия: {user[1]}",
        reply_markup=profile_keyboard()
    )


# Пользователь начинает редактирование профиля
@bot.message_handler(
    func=lambda message: message.text == EDIT_PROFILE
)
def edit_profile(message):
    telegram_id = message.from_user.id
    user_states[telegram_id] = "register_first_name"

    bot.send_message(
        message.chat.id,
        "Давай обновим данные.\n"
        "Введи новое имя:"
    )


# Возврат в главное меню
@bot.message_handler(
    func=lambda message: message.text == "⬅️ Назад"
)
def back_to_main(message):
    bot.send_message(
        message.chat.id,
        "Главное меню. Выбери валюту или свой профиль:",
        reply_markup=main_keyboard()
    )

# Пользователь выбирает валюту
@bot.message_handler(func=lambda message: message.text in CURRENCIES)
def choose_currency(message):
    currency = message.text[-3:]
    user_currencies[message.chat.id] = currency

    bot.send_message(
        message.chat.id,
        f"Выбрана валюта {currency}.\n"
        "Введи сумму.",
        reply_markup=action_keyboard()
    )


# Пользователь хочет ввести ещё одну сумму
@bot.message_handler(func=lambda message: message.text == ANOTHER_AMOUNT)
def another_amount(message):
    if message.chat.id not in user_currencies:
        bot.send_message(
            message.chat.id,
            "Сначала выбери валюту через /start.",
            reply_markup=currency_keyboard()
        )
        return

    currency = user_currencies[message.chat.id]

    bot.send_message(
        message.chat.id,
        f"Введи новую сумму в {currency}:",
        reply_markup=action_keyboard()
    )


# Пользователь хочет выбрать другую валюту
@bot.message_handler(func=lambda message: message.text == OTHER_CURRENCY)
def other_currency(message):
    bot.send_message(
        message.chat.id,
        "Выбери другую валюту:",
        reply_markup=currency_keyboard()
    )


# Обработка введённой суммы
@bot.message_handler(
    func=lambda message:
    message.text is not None
    and message.chat.id in user_currencies
    and message.text not in CURRENCIES
    and message.text not in [OTHER_CURRENCY, ANOTHER_AMOUNT]
)
def convert_currency(message):
    try:
        amount = float(message.text.replace(",", "."))

        if amount <= 0:
            bot.send_message(
                message.chat.id,
                "Сумма должна быть больше нуля. Попробуй ещё раз."
            )
            return

        currency = user_currencies[message.chat.id]
        rate, updated = get_exchange_rate(currency)
        result = amount * rate

        bot.send_message(
            message.chat.id,
            f"💱 Результат перевода\n\n"
            f"{amount:,.2f} {currency} = {result:,.2f} KZT\n\n"
            f"Курс: 1 {currency} = {rate:.4f} KZT\n"
            f"Обновлено: {updated}\n\n"
            "Курс справочный; курс банка может отличаться.",
            reply_markup=action_keyboard()
        )

    except ValueError:
        bot.send_message(
            message.chat.id,
            "Не получилось распознать сумму. "
            "Введи число, например 500 или 12,5."
        )

    except (urllib.error.URLError, TimeoutError, OSError):
        bot.send_message(
            message.chat.id,
            "Не удалось получить курс. "
            "Проверь интернет и попробуй ещё раз.",
            reply_markup=action_keyboard()
        )


init_db()

print("Бот запущен!")

bot.infinity_polling()
