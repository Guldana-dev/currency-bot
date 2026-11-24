
import urllib.error
import telebot

from config import TOKEN
from database import (
    init_db,
    get_user,
    save_user,
    get_balance,
    verify_user,
    is_user_verified,
    get_user_by_phone,
)
from currency_service import get_exchange_rate
from keyboards import (
    PROFILE,
    BALANCE,
    TRANSFER,
    EDIT_PROFILE,
    MAIN_MENU,
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
    phone_keyboard,
    transfer_keyboard,
)

bot = telebot.TeleBot(TOKEN)

# Запоминаем валюту для каждого чата
user_currencies = {}

# Запоминаем, на каком этапе находится пользователь
user_states = {}

# Запоминаем получателя перевода
transfer_recipients = {}

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

    elif not is_user_verified(telegram_id):
        user_states[telegram_id] = "verify_phone"
        bot.send_message(
            message.chat.id,
            f"С возвращением, {user[0]}! 😊\n\n"
            "Чтобы продолжить, подтверди свой номер телефона.\n"
            "Нажми кнопку ниже:",
            reply_markup=phone_keyboard()
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

    # Сохраняем ФИО
    save_user(telegram_id, first_name, last_name)

    user_states.pop(f"{telegram_id}_first_name", None)
    user_states[telegram_id] = "verify_phone"

    bot.send_message(
        message.chat.id,
        f"Готово, {first_name}! 🎉\n"
        "Твои данные сохранены.\n\n"
        "Теперь подтверди свой номер телефона:",
        reply_markup=phone_keyboard()
    )


# Пользователь открывает свой профиль
@bot.message_handler(
    func=lambda message: message.text == PROFILE
)
def show_profile(message):
    telegram_id = message.from_user.id
    user = get_user(telegram_id)

    if user is None:
        bot.send_message(
            message.chat.id,
            "Сначала давай познакомимся!"
        )
        return

    bot.send_message(
        message.chat.id,
        f"👤 Твой профиль\n\n"
        f"Имя: {user[0]}\n"
        f"Фамилия: {user[1]}",
        reply_markup=profile_keyboard()
    )


# Пользователь подтверждает номер телефона
@bot.message_handler(
    content_types=["contact"],
    func=lambda message:
    user_states.get(message.from_user.id) == "verify_phone"
)
def verify_phone(message):
    contact = message.contact
    telegram_id = message.from_user.id

    # Не позволяем повторно верифицировать пользователя
    if is_user_verified(telegram_id):
        user_states.pop(telegram_id, None)
        bot.send_message(
            message.chat.id,
            "✅ Твой номер телефона уже подтверждён!",
            reply_markup=main_keyboard()
        )
        return

    # Проверяем, что пользователь отправил собственный контакт
    if contact.user_id is None or contact.user_id != telegram_id:
        bot.send_message(
            message.chat.id,
            "❌ Нужно отправить свой собственный номер телефона.",
            reply_markup=phone_keyboard()
        )
        return

    # Проверяем наличие ФИО
    user = get_user(telegram_id)

    if user is None or not user[0] or not user[1]:
        bot.send_message(
            message.chat.id,
            "Сначала необходимо заполнить имя и фамилию."
        )
        return

    # Сохраняем номер и подтверждаем пользователя
    if not verify_user(telegram_id, contact.phone_number):
        bot.send_message(
            message.chat.id,
            "❌ Не удалось подтвердить номер. Попробуй ещё раз.",
            reply_markup=phone_keyboard()
        )
        return

    user_states.pop(telegram_id, None)
    bot.send_message(
        message.chat.id,
        "✅ Номер телефона успешно подтверждён!\n"
        "Теперь тебе доступны функции бота.",
        reply_markup=main_keyboard()
    )

# Пользователь просматривает свой баланс
@bot.message_handler(
    func=lambda message: message.text == BALANCE
)
def show_balance(message):
    telegram_id = message.from_user.id
    balance = get_balance(telegram_id)

    if balance is None:
        bot.send_message(
            message.chat.id,
            "Сначала зарегистрируйся через /start."
        )
        return

    bot.send_message(
        message.chat.id,
        f"💰 Твой баланс: {balance} единиц"
    )
# Пользователь начинает поиск получателя перевода
@bot.message_handler(
    func=lambda message: message.text == TRANSFER
)

def start_transfer(message):
    telegram_id = message.from_user.id

    if not is_user_verified(telegram_id):
        user_states[telegram_id] = "verify_phone"

        bot.send_message(
            message.chat.id,
            "❌ Для переводов необходимо подтвердить "
            "свой номер телефона.\n\n"
            "Нажми кнопку ниже 👇",
            reply_markup=phone_keyboard()
        )
        return

    user_states[telegram_id] = "transfer_phone"

    bot.send_message(
        message.chat.id,
        "💸 Перевод денег\n\n"
        "Введи номер телефона получателя:\n"
        "Например: +77001234567"
    )

# Поиск получателя перевода по номеру телефона
@bot.message_handler(
    func=lambda message: (
        message.content_type == "text"
        and user_states.get(message.from_user.id) == "transfer_phone"
    )
)
def find_transfer_recipient(message):
    telegram_id = message.from_user.id
    phone_number = (message.text or "").strip()

    if phone_number == MAIN_MENU:
        user_states.pop(telegram_id, None)
        bot.send_message(
            message.chat.id,
            "🏠 Главное меню",
            reply_markup=main_keyboard()
        )
        return

    if not phone_number.startswith("+") or not phone_number[1:].isdigit():
        bot.send_message(
            message.chat.id,
            "❌ Введи номер в формате +77001234567."
        )
        return

    recipient = get_user_by_phone(phone_number)

    if recipient is None:
        bot.send_message(
            message.chat.id,
            "❌ Пользователь с таким номером не найден."
        )
        return

    recipient_id, first_name, last_name, balance, is_verified = recipient

    if recipient_id == telegram_id:
        bot.send_message(
            message.chat.id,
            "❌ Нельзя перевести деньги самому себе."
        )
        return

    if not is_verified:
        bot.send_message(
            message.chat.id,
            "❌ Получатель ещё не прошёл верификацию."
        )
        return

    transfer_recipients[telegram_id] = recipient_id
    user_states[telegram_id] = "transfer_amount"

    bot.send_message(
        message.chat.id,
        f"✅ Получатель найден!\n\n"
        f"👤 {first_name} {last_name}\n"
        f"📱 {phone_number}\n\n"
        "Введи сумму перевода:",
        reply_markup=transfer_keyboard()
    )

# Проверка суммы перевода
@bot.message_handler(
    func=lambda message: (
        message.content_type == "text"
        and user_states.get(message.from_user.id) == "transfer_amount"
    )
)
def validate_transfer_amount(message):
    telegram_id = message.from_user.id

    if message.text == MAIN_MENU:
        user_states.pop(telegram_id, None)
        transfer_recipients.pop(telegram_id, None)

        bot.send_message(
            message.chat.id,
            "Перевод отменён. 🏠 Главное меню",
            reply_markup=main_keyboard()
        )
        return

    try:
        amount = int(message.text.strip())
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Введи целое число."
        )
        return

    if amount <= 0:
        bot.send_message(
            message.chat.id,
            "❌ Сумма должна быть больше нуля."
        )
        return

    balance = get_balance(telegram_id)

    if balance is None or amount > balance:
        bot.send_message(
            message.chat.id,
            "❌ Недостаточно средств на балансе."
        )
        return

    recipient_id = transfer_recipients.get(telegram_id)

    if recipient_id is None or not is_user_verified(recipient_id):
        bot.send_message(
            message.chat.id,
            "❌ Получатель недоступен для перевода.",
            reply_markup=main_keyboard()
        )
        user_states.pop(telegram_id, None)
        transfer_recipients.pop(telegram_id, None)
        return

    user_states.pop(telegram_id, None)
    transfer_recipients.pop(telegram_id, None)

    bot.send_message(
        message.chat.id,
        "✅ Проверка перевода успешно пройдена!",
        reply_markup=main_keyboard()
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
# Возврат в главное меню из конвертера
@bot.message_handler(
    func=lambda message: message.text == MAIN_MENU
)
def return_to_main_menu(message):
    bot.send_message(
        message.chat.id,
        "🏠 Главное меню. Выбери нужный раздел:",
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
    func=lambda message: (
        message.text is not None
        and message.chat.id in user_currencies
        and user_states.get(message.from_user.id) not in [
            "register_first_name",
            "register_last_name",
            "verify_phone",
            "transfer_phone",
        ]

        and message.text not in CURRENCIES
        and message.text not in [OTHER_CURRENCY, ANOTHER_AMOUNT]
    )
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


if __name__ == "__main__":
    init_db()
    print("Бот запущен!")
    bot.infinity_polling()
