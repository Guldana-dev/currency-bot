
from telebot import types

# Названия кнопок
USD = "🇺🇸 USD"
EUR = "🇪🇺 EUR"
RUB = "🇷🇺 RUB"
CNY = "🇨🇳 CNY"

OTHER_CURRENCY = "🔄 Другая валюта"
ANOTHER_AMOUNT = "🔢 Ещё сумма"

PROFILE = "👤 Мой профиль"
EDIT_PROFILE = "✏️ Изменить профиль"
BACK = "⬅️ Назад"

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


# Главное меню
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(PROFILE)
    keyboard.add(USD, EUR, RUB, CNY)
    return keyboard


# Меню профиля
def profile_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(EDIT_PROFILE)
    keyboard.add(BACK)
    return keyboard
