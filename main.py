import datetime
import os
import telebot
from dotenv import load_dotenv

from purchases import extract_data, convert_to_rub
from stats_api import StatisticsAPI
from errors import UserError, ValidationError

load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
statistics_api = StatisticsAPI(
    os.environ.get('API_URL'),
    os.environ.get('MONEY_TEMPLATE_ID'),
    os.environ.get('BASIC_USERNAME'),
    os.environ.get('BASIC_PASSWORD'),
    os.environ.get('APP_USERNAME'),
    os.environ.get('APP_PASSWORD')
)


@bot.message_handler(func=lambda msg: True)
def receive_data(message):
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message.text}")
    try:
        price, name = extract_data(message.text)
    except ValidationError as e:
        bot.reply_to(message, f"Validation failed: {e}")
        return

    try:
        converted_price = convert_to_rub(price)
        statistics_api.send_data(converted_price, name)
        bot.reply_to(
            message, f"Successfully sent. Amount in RUB: {converted_price}")
    except UserError as e:
        bot.reply_to(message, f"Data has not been sent to stats app: {e}")


bot.infinity_polling()
