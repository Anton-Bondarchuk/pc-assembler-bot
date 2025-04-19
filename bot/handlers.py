from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.state.pc_assember_fsm import PcAssemblerFSM
from bot.yandex_market.api.service import PcAssemblerService

assemby_router = Router()


@assemby_router.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(
        text="""👋 Привет! Я — Сборщик ПК 🤖
Помогаю подобрать оптимальную сборку компьютера под твой бюджет и задачи.

Вот что я умею:

🧩 Учитываю твой бюджет
🎯 Спрашиваю, для чего нужен ПК (игры, работа, монтаж и т.д.)
⚙️ Подбираю совместимые комплектующие
💡 Могу предложить готовую сборку с ценами и ссылками

Готов начать?

Напиши  /start_assembly. — и соберём твой идеальный ПК 💻
""",
    )


def get_price_keyboard():
    """
    Creates an inline keyboard with price options from $500 to $2500 with $500 step
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="$500", callback_data="price_500"),
            InlineKeyboardButton(text="$1000", callback_data="price_1000"),
        ],
        [
            InlineKeyboardButton(text="$1500", callback_data="price_1500"),
            InlineKeyboardButton(text="$2000", callback_data="price_2000"),
        ],
        [
            InlineKeyboardButton(text="$2500", callback_data="price_2500"),
        ]
    ])
    return keyboard


def get_goals_keyboard():
    """
    Creates an inline keyboard with PC usage goal options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Игры", callback_data="goal_games"),
        ],
        [
            InlineKeyboardButton(text="📚 Офис и учеба", callback_data="goal_office"),
        ],
        [
            InlineKeyboardButton(text="🎨 Работа с графикой и 3д", callback_data="goal_graphics"),
        ],
        [
            InlineKeyboardButton(text="🎬 Видомонтаж и стримминг", callback_data="goal_video"),
        ],
        [
            InlineKeyboardButton(text="💻 Программирование", callback_data="goal_programming"),
        ],
        [
            InlineKeyboardButton(text="🔄 Универсальный пк", callback_data="goal_universal"),
        ]
    ])
    return keyboard


@assemby_router.message(Command("start_assembly"))
async def start_assembly(message: types.Message, state: FSMContext):
    # Reset the state at the beginning of the assembly process
    await state.clear()
    # Set state to price selection
    await state.set_state(PcAssemblerFSM.price)
    
    await message.answer(
        text="Выберите диапазон цен:",
        reply_markup=get_price_keyboard()
    )


@assemby_router.callback_query(PcAssemblerFSM.price, lambda c: c.data.startswith('price_'))
async def process_price_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handler to process the selected price
    """
    # Extract the price from the callback data
    selected_price = callback_query.data.split('_')[1]
    
    # Store the selected price in state
    await state.update_data(price=selected_price)
    
    # Move to the next state - selecting goal
    await state.set_state(PcAssemblerFSM.goals)
    
    await callback_query.answer(f"Вы выбрали ${selected_price}")
    await callback_query.message.edit_text(
        f"Бюджет: ${selected_price}.\n\nТеперь выберите назначение вашего ПК:",
        reply_markup=get_goals_keyboard()
    )



@assemby_router.callback_query(PcAssemblerFSM.goals, lambda c: c.data.startswith('goal_'))
async def process_goal_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handler to process the selected goal
    """
    # Extract the goal from the callback data
    goal_key = callback_query.data.split('_')[1]
    
    # Map goal keys to user-friendly names
    goal_names = {
        "games": "Игры",
        "office": "Офис и учеба",
        "graphics": "Работа с графикой и 3д",
        "video": "Видомонтаж и стримминг",
        "programming": "Программирование",
        "universal": "Универсальный пк"
    }
    
    selected_goal = goal_names.get(goal_key, goal_key)
    
    # Store the selected goal in state
    await state.update_data(goal=selected_goal)
    
    # Get all the data stored in state
    data = await state.get_data()
    
    await callback_query.answer(f"Вы выбрали: {selected_goal}")
    
    # Show loading message
    await callback_query.message.edit_text("⏳ Подбираем конфигурацию компьютера...")
    
    try:
        pc_service = PcAssemblerService()

        # Get PC build from service
        pc_build = await pc_service.create_pc_build(int(data['price']), selected_goal)
        
        # Format the response message
        components_text = ""
        for component_type, component in pc_build["components"].items():
            # Translate component type to Russian
            component_types_ru = {
                "cpu": "Процессор",
                "gpu": "Видеокарта",
                "ram": "Оперативная память",
                "storage": "Накопитель",
                "motherboard": "Материнская плата",
                "power_supply": "Блок питания",
                "case": "Корпус"
            }
            
            component_name_ru = component_types_ru.get(component_type, component_type)
            components_text += f"• {component_name_ru}: {component['name']} - {component['price']} ₽\n"
        
        result_message = (
            f"🖥️ <b>Собранная конфигурация ПК</b>\n\n"
            f"💰 Бюджет: ${data['price']}\n"
            f"🎯 Назначение: {selected_goal}\n\n"
            f"<b>Комплектующие:</b>\n"
            f"{components_text}\n"
            f"<b>Общая стоимость:</b> {pc_build['total_price_rub']} ₽ (${pc_build['total_price_usd']})"
        )
        
        await callback_query.message.edit_text(
            result_message,
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Произошла ошибка при подборе конфигурации: {str(e)}\n"
            f"Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
        )
    