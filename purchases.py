import requests

from errors import ValidationError, UserError
from utils import memoize

FORMAT_ERROR_MESSAGE = "Purchase data entered wrong. Use mask: {price: int} {purchase name: 3 chars at least}"
EXCHANGE_RATE_ERROR_MESSAGE = "Exchange rates are not available"
RSD_TO_RUB_EXCHANGE_RATE_URL = "https://kurs.resenje.org/api/v1/currencies/rub/rates/today"


def extract_data(chat_message):
    message = chat_message.split()

    try:
        price = float(message[0])
    except ValueError:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    name = " ".join(message[1:])
    if len(name) < 3:
        raise ValidationError(FORMAT_ERROR_MESSAGE)

    return price, name


def convert_to_rub(price_in_rsd):
    return round(price_in_rsd / exchange_rate())


@memoize(3600)
def exchange_rate():
    response = requests.get(RSD_TO_RUB_EXCHANGE_RATE_URL)
    if response.status_code != 200 or "exchange_middle" not in response.json():
        raise UserError(EXCHANGE_RATE_ERROR_MESSAGE)

    return response.json()["exchange_middle"]
