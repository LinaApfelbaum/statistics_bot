from constants import Buttons, SupportedCurrencies
from errors import UserError, ValidationError
from stats_api import StatisticsAPI
from purchases import extract_data, convert_to_rub
import datetime
import os
import telebot
from telebot import types
from dotenv import load_dotenv

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

AUTH_USER_IDS = {
    int(user_id.strip())
    for user_id in os.environ.get("AUTH_USER_IDS", "").split(",")
    if user_id.strip()
}

user_settings = {}

def auth_required(func):
    def wrapper(message, *args, **kwargs):
        if not is_authorized(message):
            bot.send_message(
                message.chat.id,
                "Not authorised"
            )
            return None
        return func(message, *args, **kwargs)
    return wrapper


def is_authorized(message) -> bool:
    return message.from_user.id in AUTH_USER_IDS


def log_message(message):
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}")


def get_user_currency(user_id: int) -> str:
    return user_settings.get(user_id, {}).get("currency")


def set_user_currency(user_id: int, currency: str) -> None:
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["currency"] = currency


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.ADD_SPEND),
        types.KeyboardButton(Buttons.CHANGE_CURRENCY),
    )
    markup.add(types.KeyboardButton(Buttons.LAST_ENTRIES))
    return markup


def currency_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    buttons = [types.KeyboardButton(currency) for currency in SupportedCurrencies.all()]
    markup.add(*buttons)

    markup.add(types.KeyboardButton(Buttons.CANCEL))
    return markup


def cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(Buttons.CANCEL))
    return markup


@bot.message_handler(commands=['start'])
@auth_required
def start_command(message):
    current_currency = get_user_currency(message.from_user.id)
    currency_text = current_currency if current_currency else "not set"

    bot.send_message(
        message.chat.id,
        f"Choose an action.\nCurrent currency: {currency_text}",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=['last'])
@auth_required
def get_last_entries(message):
    log_message(message.text)
    try:
        bot.reply_to(message, statistics_api.get_last_entries(), reply_markup=main_menu())
    except UserError as e:
        error_message = f"Command failed: {e}"
        log_message(error_message)
        bot.reply_to(message, error_message, reply_markup=main_menu())


@bot.message_handler(func=lambda message: message.text == Buttons.LAST_ENTRIES)
@auth_required
def get_last_entries_button(message):
    log_message(message.text)
    try:
        bot.send_message(message.chat.id, statistics_api.get_last_entries(), reply_markup=main_menu())
    except UserError as e:
        error_message = f"Command failed: {e}"
        log_message(error_message)
        bot.send_message(message.chat.id, error_message, reply_markup=main_menu())


@bot.message_handler(func=lambda message: message.text == Buttons.CHANGE_CURRENCY)
@auth_required
def change_currency_start(message):
    log_message(message.text)
    current_currency = get_user_currency(message.from_user.id)
    currency_text = current_currency if current_currency else "not set"

    msg = bot.send_message(
        message.chat.id,
        f"Current currency: {currency_text}\nChoose currency:",
        reply_markup=currency_menu()
    )
    bot.register_next_step_handler(msg, process_change_currency_step)


def process_change_currency_step(message):
    log_message(message.text)
    user_id = message.from_user.id
    text = message.text.strip().upper()

    if message.text == Buttons.CANCEL:
        bot.send_message(
            message.chat.id,
            "Currency update has been cancelled.",
            reply_markup=main_menu()
        )
        return

    if text not in SupportedCurrencies.all():
        msg = bot.send_message(
            message.chat.id,
            "Wrong currency. Choose currency with a button.",
            reply_markup=currency_menu()
        )
        bot.register_next_step_handler(msg, process_change_currency_step)
        return

    set_user_currency(user_id, text)
    bot.send_message(
        message.chat.id,
        f"Currency has been set to {text}.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: message.text == Buttons.ADD_SPEND)
@auth_required
def add_expense_start(message):
    log_message(message.text)
    current_currency = get_user_currency(message.from_user.id)

    if not current_currency:
        msg = bot.send_message(
            message.chat.id,
            "Currency is not set.\nChoose currency first:",
            reply_markup=currency_menu()
        )
        bot.register_next_step_handler(msg, process_currency_for_expense_step)
        return

    msg = bot.send_message(
        message.chat.id,
        f"Currency: {current_currency}\n"
        f"Enter spend in one message.\n\n"
        f"Examples:\n"
        f"100 coffee\n"
        f"12.5 taxi airport\n"
        f"EUR 20 hotel",
        reply_markup=cancel_menu()
    )
    bot.register_next_step_handler(msg, process_expense_input)


def process_currency_for_expense_step(message):
    log_message(message.text)
    user_id = message.from_user.id
    text = message.text.strip().upper()

    if message.text == Buttons.CANCEL:
        bot.send_message(
            message.chat.id,
            "Spend add has been cancelled.",
            reply_markup=main_menu()
        )
        return

    if text not in SupportedCurrencies.all():
        msg = bot.send_message(
            message.chat.id,
            "Wrong currency. Choose currency with a button.",
            reply_markup=currency_menu()
        )
        bot.register_next_step_handler(msg, process_currency_for_expense_step)
        return

    set_user_currency(user_id, text)

    msg = bot.send_message(
        message.chat.id,
        f"Currency: {text}\n"
        f"Enter spend in one message.\n\n"
        f"Examples:\n"
        f"100 coffee\n"
        f"12.5 taxi airport\n"
        f"{text} 20 hotel",
        reply_markup=cancel_menu()
    )
    bot.register_next_step_handler(msg, process_expense_input)


def handle_expense(message, reply_markup):
    user_id = message.from_user.id
    current_currency = get_user_currency(user_id)

    try:
        currency, price, name = extract_data(
            message.text,
            default_currency=current_currency
        )
    except ValidationError as e:
        bot.send_message(
            message.chat.id,
            f"Validation failed: {e}",
            reply_markup=reply_markup
        )
        return False

    try:
        if currency == SupportedCurrencies.RUB:
            converted_price = price
        else:
            converted_price = convert_to_rub(price, currency)

        statistics_api.send_data(price, name, currency, converted_price)

        bot.send_message(
            message.chat.id,
            f"Successfully sent: {price} {currency}\n"
            f"{name}\n"
            f"Amount in RUB: {converted_price}",
            reply_markup=main_menu()
        )
        return True

    except UserError as e:
        error_message = f"Data has not been sent: {e}"
        log_message(error_message)
        bot.send_message(message.chat.id, error_message, reply_markup=main_menu())
        return False


def process_expense_input(message):
    log_message(message.text)

    if message.text == Buttons.CANCEL:
        bot.send_message(message.chat.id, "Cancelled", reply_markup=main_menu())
        return

    success = handle_expense(message, cancel_menu())

    if not success:
        bot.register_next_step_handler(message, process_expense_input)


@bot.message_handler(func=lambda msg: True)
@auth_required
def receive_data(message):
    log_message(message.text)

    if message.text in Buttons.all():
        return

    handle_expense(message, main_menu())

bot.infinity_polling()
