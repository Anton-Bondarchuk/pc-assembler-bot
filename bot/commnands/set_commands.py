from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from bot.config_data import config_dict


async def set_bot_commands(bot: Bot):
    usercommands = [
        BotCommand(command="start", description="Комманда запуска бота"),
        BotCommand(command="help", description="Справка по использованию бота"),

        BotCommand(command="start_assembly", description="Начать сборку пк"),
    ]

    await bot.set_my_commands(usercommands, scope=BotCommandScopeDefault())