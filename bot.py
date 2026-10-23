
import urllib.error
import telebot

from config import TOKEN
from currency_service import get_exchange_rate
from keyboards import (
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


# Запуск бота
@bot.message_handler(commands=["start"])
def start(message):
    user_currencies.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        "Привет! \nВыбери валюту для перевода в тенге:",
        reply_markup=currency_keyboard()
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


print("Бот запущен!")

bot.infinity_polling()
