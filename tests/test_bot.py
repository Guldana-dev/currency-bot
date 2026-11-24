
from types import SimpleNamespace
from unittest.mock import patch

import bot


def test_unverified_user_gets_phone_button():
    # Создаём ненастоящее сообщение Telegram
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text=bot.TRANSFER,
    )

    bot.user_states.clear()

    try:
        # Имитируем неподтверждённого пользователя
        with patch.object(bot, "is_user_verified", return_value=False), \
             patch.object(bot, "phone_keyboard") as mock_keyboard, \
             patch.object(bot.bot, "send_message") as mock_send:

            mock_keyboard.return_value = "TEST_PHONE_BUTTON"

            # Запускаем функцию перевода
            bot.start_transfer(message)

            # Проверяем состояние пользователя
            assert bot.user_states[12345] == "verify_phone"

            # Проверяем, что появилась нужная кнопка
            mock_keyboard.assert_called_once()

            assert mock_send.call_args.kwargs["reply_markup"] == (
                "TEST_PHONE_BUTTON"
            )

            # Проверяем текст сообщения
            assert "подтвердить" in mock_send.call_args.args[1]
    finally:
        bot.user_states.clear()

def test_transfer_insufficient_balance():
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text="1500",
    )

    bot.user_states[12345] = "transfer_amount"
    bot.transfer_recipients[12345] = 67890

    try:
        with patch.object(bot, "get_balance", return_value=1000), \
             patch.object(bot.bot, "send_message") as mock_send:

            bot.validate_transfer_amount(message)

            assert "Недостаточно средств" in mock_send.call_args.args[1]

            assert bot.user_states[12345] == "transfer_amount"

    finally:
        bot.user_states.clear()
        bot.transfer_recipients.clear()

def test_transfer_invalid_amount():
    for amount in ["0", "-100"]:
        message = SimpleNamespace(
            chat=SimpleNamespace(id=12345),
            from_user=SimpleNamespace(id=12345),
            text=amount,
        )

        bot.user_states[12345] = "transfer_amount"

        try:
            with patch.object(
                bot.bot, "send_message"
            ) as mock_send:

                bot.validate_transfer_amount(message)

                assert "больше нуля" in mock_send.call_args.args[1]

        finally:
            bot.user_states.clear()
            bot.transfer_recipients.clear()

def test_transfer_invalid_text():
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text="abc",
    )

    bot.user_states[12345] = "transfer_amount"

    try:
        with patch.object(
            bot.bot, "send_message"
        ) as mock_send:

            bot.validate_transfer_amount(message)

            assert "Введи целое число" in mock_send.call_args.args[1]

    finally:
        bot.user_states.clear()
        bot.transfer_recipients.clear()

def test_transfer_unavailable_recipient():
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text="500",
    )

    bot.user_states[12345] = "transfer_amount"
    bot.transfer_recipients[12345] = 67890

    try:
        with patch.object(bot, "get_balance", return_value=1000), \
             patch.object(bot, "is_user_verified", return_value=False), \
             patch.object(bot.bot, "send_message") as mock_send:

            bot.validate_transfer_amount(message)

            assert "Получатель недоступен" in mock_send.call_args.args[1]

            assert 12345 not in bot.user_states
            assert 12345 not in bot.transfer_recipients

    finally:
        bot.user_states.clear()
        bot.transfer_recipients.clear()

def test_transfer_successful_validation():
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text="500",
    )

    bot.user_states[12345] = "transfer_amount"
    bot.transfer_recipients[12345] = 67890

    try:
        with patch.object(bot, "get_balance", return_value=1000), \
             patch.object(bot, "is_user_verified", return_value=True), \
             patch.object(bot.bot, "send_message") as mock_send:

            bot.validate_transfer_amount(message)

            assert "успешно пройдена" in mock_send.call_args.args[1]

            assert 12345 not in bot.user_states
            assert 12345 not in bot.transfer_recipients

    finally:
        bot.user_states.clear()
        bot.transfer_recipients.clear()

def test_transfer_cancellation():
    message = SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(id=12345),
        text=bot.MAIN_MENU,
    )

    bot.user_states[12345] = "transfer_amount"
    bot.transfer_recipients[12345] = 67890

    try:
        with patch.object(
            bot.bot, "send_message"
        ) as mock_send:

            bot.validate_transfer_amount(message)

            assert "Перевод отменён" in mock_send.call_args.args[1]

            assert 12345 not in bot.user_states
            assert 12345 not in bot.transfer_recipients

    finally:
        bot.user_states.clear()
        bot.transfer_recipients.clear()
