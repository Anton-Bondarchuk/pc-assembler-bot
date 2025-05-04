
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_goals_keyboard():
    """
    Creates an inline keyboard with PC usage goal options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Игры", callback_data="goal_games"),
        ],
        [
            InlineKeyboardButton(text="📚 Офис и учеба",
                                 callback_data="goal_office"),
        ],
        [
            InlineKeyboardButton(
                text="🎨 Работа с графикой и 3д", callback_data="goal_graphics"),
        ],
        [
            InlineKeyboardButton(
                text="🎬 Видомонтаж и стримминг", callback_data="goal_video"),
        ],
        [
            InlineKeyboardButton(text="💻 Программирование",
                                 callback_data="goal_programming"),
        ],
        [
            InlineKeyboardButton(text="🔄 Универсальный пк",
                                 callback_data="goal_universal"),
        ]
    ])
    return keyboard
