
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
