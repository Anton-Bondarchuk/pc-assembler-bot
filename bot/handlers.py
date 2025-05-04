import logging

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.state.pc_assember_fsm import PcAssemblerFSM
from bot.service import PcAssemblerService
from bot.keyboard import get_price_keyboard, get_goals_keyboard

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
    Handler to process the selected goal and generate PC configuration
    """
    # Extract the goal from the callback data
    goal_key = callback_query.data.split('_')[1]

    # Store the selected goal in state
    await state.update_data(goal=goal_key)

    # Get all the data stored in state
    data = await state.get_data()

    # Show loading message
    await callback_query.answer(f"Подбираем конфигурацию для: {goal_key}")
    await callback_query.message.edit_text("⏳ Подбираем оптимальную конфигурацию компьютера...")

    try:
        # Get the user's budget
        price_usd = float(data.get('price', '1000'))

        # Create service instance and get PC build
        pc_assembler = PcAssemblerService(
            data_dir="./bot/pc-part-dataset/data/json/")
        result = await pc_assembler.generate_pc_build(budget=price_usd, goal=goal_key)

        if result['status'] == 'OPTIMAL':
            # Format the message with the build details
            message_text = f"🖥️ <b>Оптимальная конфигурация ({result['goal_ru']})</b>\n\n"

            # Convert prices to RUB for display
            exchange_rate = 75.0  # Update this to get current exchange rate
            total_price_rub = pc_assembler.convert_usd_to_rub(
                result['total_price'], exchange_rate)

            # Add components to the message
            for comp in result['components_with_details']:
                price_rub = pc_assembler.convert_usd_to_rub(
                    comp['price'], exchange_rate)
                message_text += f"• <b>{comp['category_ru']}:</b> {comp['name']}\n"
                message_text += f"  💰 {pc_assembler.format_price(comp['price'])} / {pc_assembler.format_price(price_rub, 'RUB')}\n"

            message_text += f"\n<b>Общая стоимость:</b> {pc_assembler.format_price(result['total_price'])} / {pc_assembler.format_price(total_price_rub, 'RUB')}"
            message_text += f"\n<b>Остаток бюджета:</b> {pc_assembler.format_price(result['remaining_budget'])}"

            # Add buttons for actions
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="🔄 Подобрать другую конфигурацию", callback_data="restart")],
                [types.InlineKeyboardButton(
                    text="💾 Сохранить конфигурацию", callback_data="save_build")]
            ])

            await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")

            # Store the build in state for later use
            await state.update_data(build_result=result)

        elif result['status'] == 'INFEASIBLE':
            # No solution found
            await callback_query.message.edit_text(
                "❌ Не удалось подобрать оптимальную конфигурацию с заданным бюджетом.\n"
                "Попробуйте увеличить бюджет или выбрать другую цель.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🔄 Попробовать снова", callback_data="restart")]
                ])
            )
        else:
            # Error in optimization
            await callback_query.message.edit_text(
                f"❌ Ошибка при подборе конфигурации: {result['message']}\n"
                "Пожалуйста, попробуйте снова или выберите другие параметры.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🔄 Попробовать снова", callback_data="restart")]
                ])
            )
    except Exception as e:
        # Log the error
        import traceback
        logging.error(f"Error generating PC build: {e}")
        logging.error(traceback.format_exc())

        # Show error message to user
        await callback_query.message.edit_text(
            "❌ Произошла ошибка при подборе конфигурации.\n"
            "Пожалуйста, попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="🔄 Попробовать снова", callback_data="restart")]
            ])
        )


@assemby_router.callback_query(lambda c: c.data == "new_assembly")
async def start_new_assembly(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handler to start a new assembly process
    """
    await callback_query.answer("Начинаем новую сборку!")
    await state.set_state(PcAssemblerFSM.price)

    await callback_query.message.edit_text(
        text="Выберите диапазон цен:",
        reply_markup=get_price_keyboard()
    )
