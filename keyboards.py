
from telebot import types

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
