import os
from datetime import datetime
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from aiogram import F

from bot.service import PcAssemblerService
from bot.state.pc_assember_fsm import PcAssemblerFSM
from bot.keyboard import get_price_keyboard, get_goals_keyboard

# Create a router for these callbacks
callback_router = Router()

@callback_router.callback_query(F.data == "restart")
async def restart_configuration(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handler to restart the PC configuration process
    """
    # Reset the state
    await state.clear()
    
    # Go back to the initial state
    await state.set_state(PcAssemblerFSM.price)
    
    # Show the initial message with budget selection
    await callback_query.message.edit_text(
        text="Выберите диапазон цен:",
        reply_markup=get_price_keyboard()
    )
    
    # Answer the callback to remove the loading indicator
    await callback_query.answer("Начинаем подбор новой конфигурации")

@callback_router.callback_query(F.data == "save_build")
async def save_build_configuration(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handler to save the current PC configuration to a text file
    """
    # Get the build result from state
    data = await state.get_data()
    build_result = data.get("build_result")
    
    if not build_result or build_result.get("status") != "OPTIMAL":
        await callback_query.answer("Ошибка: конфигурация не найдена", show_alert=True)
        return
    
    # Answer the callback to show we're processing
    await callback_query.answer("Сохраняем конфигурацию...")
    
    try:
        # Create service instance for helper methods
        pc_assembler = PcAssemblerService()
        
        # Generate a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or f"user_{user_id}"
        filename = f"pc_build_{username}_{timestamp}.txt"
        
        # Convert prices to RUB for display
        exchange_rate = 75.0
        total_price_usd = build_result["total_price"]
        total_price_rub = pc_assembler.convert_usd_to_rub(total_price_usd, exchange_rate)
        
        # Create the content of the file
        content = []
        content.append("=" * 50)
        content.append(f"КОНФИГУРАЦИЯ ПК ({build_result['goal_ru'].upper()})")
        content.append(f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        content.append(f"Пользователь: {username}")
        content.append("=" * 50)
        content.append("")
        
        # Add components
        for comp in build_result["components_with_details"]:
            price_usd = comp["price"]
            price_rub = pc_assembler.convert_usd_to_rub(price_usd, exchange_rate)
            
            content.append(f"{comp['category_ru'].upper()}: {comp['name']}")
            content.append(f"Цена: {pc_assembler.format_price(price_usd)} / {pc_assembler.format_price(price_rub, 'RUB')}")
            
            # Add some detailed specs if available
            if comp["category"] == "cpu":
                details = comp["details"]
                if "core_count" in details:
                    content.append(f"Ядра: {details.get('core_count')}")
                if "boost_clock" in details:
                    content.append(f"Частота (Boost): {details.get('boost_clock')} GHz")
            
            elif comp["category"] == "memory":
                details = comp["details"]
                if "modules" in details and isinstance(details["modules"], list) and len(details["modules"]) >= 2:
                    modules = details["modules"]
                    content.append(f"Конфигурация: {modules[0]} x {modules[1]}GB")
                if "speed" in details and isinstance(details["speed"], list) and len(details["speed"]) >= 2:
                    speed = details["speed"]
                    content.append(f"Частота: {speed[1]} MHz")
            
            elif comp["category"] == "video_card":
                details = comp["details"]
                if "memory" in details:
                    content.append(f"Видеопамять: {details.get('memory')} GB")
                if "chipset" in details:
                    content.append(f"Чипсет: {details.get('chipset')}")
            
            content.append("")  # Empty line between components
        
        content.append("=" * 50)
        content.append(f"ОБЩАЯ СТОИМОСТЬ: {pc_assembler.format_price(total_price_usd)} / {pc_assembler.format_price(total_price_rub, 'RUB')}")
        content.append(f"Остаток бюджета: {pc_assembler.format_price(build_result['remaining_budget'])}")
        content.append("=" * 50)
        
        # Join all lines with newlines
        file_content = "\n".join(content)
        
        # Save the file temporarily (optional, you can skip this if not needed)
        temp_dir = "temp_builds"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        # Send the file to the user
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        # Create a BufferedInputFile object from the file data
        file_to_send = BufferedInputFile(file_data, filename=filename)
        
        # Send the file
        await callback_query.message.answer_document(
            document=file_to_send,
            caption="📋 Конфигурация вашего ПК сохранена в файл."
        )
        
        # Update the message to indicate the file was saved
        await callback_query.message.edit_text(
            callback_query.message.text + "\n\n✅ Конфигурация успешно сохранена!",
            reply_markup=callback_query.message.reply_markup,
            parse_mode="HTML"
        )
        
        # Cleanup the temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
    except Exception as e:
        # Log the error
        import logging
        import traceback
        logging.error(f"Error saving build configuration: {e}")
        logging.error(traceback.format_exc())
        
        # Notify the user
        await callback_query.message.answer(
            "❌ Произошла ошибка при сохранении конфигурации.\n"
            "Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
        )