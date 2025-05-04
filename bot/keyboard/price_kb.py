from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_price_keyboard():
    """
    Creates an inline keyboard with price options from $500 to $2500 with $500 step
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="$1000", callback_data="price_1000"),
            InlineKeyboardButton(text="$1500", callback_data="price_1500"),
        ],
        [
            InlineKeyboardButton(text="$2000", callback_data="price_2000"),
            InlineKeyboardButton(text="$2500", callback_data="price_2500"),
        ],
        [
            InlineKeyboardButton(text="$3000", callback_data="price_3000"),
            InlineKeyboardButton(text="$3500", callback_data="price_3500"),
        ],
        [
            InlineKeyboardButton(text="$4000", callback_data="price_4000"),
            InlineKeyboardButton(text="$4500", callback_data="price_4500"),
        ],
        [
            InlineKeyboardButton(text="$5000", callback_data="price_5000"),
        ]
    ])
    return keyboard
