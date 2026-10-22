
import json
import urllib.request


# Получаем актуальный курс валюты к тенге
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
