
import os
import json
import urllib.request
import urllib.error
import telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден!")

bot = telebot.TeleBot(TOKEN)

# Запоминаем валюту для каждого чата
user_currencies = {}

# Названия кнопок
USD = "🇺🇸 USD"
EUR = "🇪🇺 EUR"
RUB = "🇷🇺 RUB"
CNY = "🇨🇳 CNY"

OTHER_CURRENCY = "🔄 Другая валюта"
ANOTHER_AMOUNT = "🔢 Ещё сумма"

CURRENCIES = [USD, EUR, RUB, CNY]


# Клавиатура выбора валюты
def currency_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(USD, EUR, RUB, CNY)
    return keyboard


# Клавиатура после выбора валюты
def action_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(ANOTHER_AMOUNT, OTHER_CURRENCY)
    return keyboard


# Получаем актуальный доступный курс
def get_exchange_rate(currency):
    url = f"https://open.er-api.com/v6/latest/{currency}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CurrencyBot/1.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("result") != "success":
        raise ValueError("Сервис не вернул курс.")

    rates = data.get("rates", {})

    if "KZT" not in rates:
        raise ValueError("Курс тенге не найден.")

    return rates["KZT"], data.get(
        "time_last_update_utc", "не указано"
    )


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
