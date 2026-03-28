import os
from typing import Optional

import requests

from constants import SupportedCurrencies
from errors import ValidationError, UserError
from utils import memoize

FORMAT_ERROR_MESSAGE = f"Purchase data entered wrong. Use mask: {{currency: {SupportedCurrencies.all()}}} {{price: int}} {{purchase name: 3 chars at least}}"
EXCHANGE_RATE_ERROR_MESSAGE = "Exchange rates are not available"
RSD_TO_RUB_EXCHANGE_RATE_URL = "https://kurs.resenje.org/api/v1/currencies/{currency}/rates/today"


def extract_data(chat_message: str, default_currency: Optional[str] = None) -> tuple[str, float, str]:
    message = chat_message.split()

    if not message:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    currency = default_currency
    if message[0].upper() in SupportedCurrencies.all():
        currency = message[0].upper()
        message.pop(0)

    if currency is None:
        raise ValidationError("Currency is required")

    if not message:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    try:
        price = float(message[0].replace(",", "."))
    except ValueError:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    name = " ".join(message[1:])
    if len(name.strip()) < 3:
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
