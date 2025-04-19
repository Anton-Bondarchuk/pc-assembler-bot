import asyncio
import logging
from enum import Enum

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.bot import DefaultBotProperties
# from pydantic import BaseModel
# from pydantic import RedisDsn

from bot.config_data import config_dict
from bot.commnands.set_commands import set_bot_commands
from bot.handlers import assemby_router

class FSMMode(str, Enum): 
    MEMORY = "memory"
    REDIS = "redis"


# class Redis(BaseModel): 
#     dsn: RedisDsn
#     fsm_db_int: int
#     data_db_id: int


async def main():

    asyncio.get_running_loop()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # if config_dict["fsm_mode"] == FSMMode.MEMORY:
    #     storage = MemoryStorage()
    # else:
    #     storage = RedisStorage.from_url(
    #         url=f"{config_dict['redis_dsn']}/{config_dict['redis_fsm_db_id']}",
    #         connection_kwargs={"decode_responses": True},
    #     )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    bot = Bot(config_dict["bot_token"], default=DefaultBotProperties(parse_mode="HTML"))

    dp.include_router(router=assemby_router)

    await set_bot_commands(bot=bot)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())