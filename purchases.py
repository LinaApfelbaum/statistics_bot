import os

import requests

from errors import ValidationError, UserError
from utils import memoize

SUPPORTED_CURRENCIES = ["USD", "EUR", "RUB", "GBP", "RSD"]
FORMAT_ERROR_MESSAGE = f"Purchase data entered wrong. Use mask: {{currency: {SUPPORTED_CURRENCIES}}} {{price: int}} {{purchase name: 3 chars at least}}"
EXCHANGE_RATE_ERROR_MESSAGE = "Exchange rates are not available"
RSD_TO_RUB_EXCHANGE_RATE_URL = "https://kurs.resenje.org/api/v1/currencies/{currency}/rates/today"


def extract_data(chat_message: str) -> tuple[str, float, str]:
    message = chat_message.split()

    currency = "RSD"
    if message[0].upper() in SUPPORTED_CURRENCIES:
        currency = message[0].upper()
        message.pop(0)

    try:
        price = float(message[0])
    except ValueError:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    name = " ".join(message[1:])
    if len(name) < 3:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    return currency, price, name


def convert_to_rub(price: float, currency: str) -> float:
    exchange_rate_rub = exchange_rate("RUB")
    if currency != "RSD":
        price = round(price * exchange_rate(currency))

    return round(price / exchange_rate_rub)


@memoize(int(os.environ.get('CURRENCY_CACHE_TTL')))
def exchange_rate(currency) -> float:
    response = requests.get(RSD_TO_RUB_EXCHANGE_RATE_URL.format(currency=currency.lower()))
    if response.status_code != 200 or "exchange_middle" not in response.json():
        raise UserError(EXCHANGE_RATE_ERROR_MESSAGE)

    return response.json()["exchange_middle"]
