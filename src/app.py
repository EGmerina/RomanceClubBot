import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    Message,
)
from aiogram.types import BotCommand, ErrorEvent
from dotenv import load_dotenv

from keyboards import (
    character_keyboard,
    character_confirm_keyboard,
    choice_keyboard,
    continue_keyboard,
    ending_keyboard,
    select_character_keyboard,
    start_game_keyboard,
)
from engine import GameEngine
from models import Character

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не задан BOT_TOKEN в .env")


BASE_DIR = Path(__file__).resolve().parent.parent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


router = Router()
engine = GameEngine()


async def send_start_screen(message: Message):
    intro = engine.get_intro()

    text = intro.get("description")
    image_path = intro.get("image")

    try:
        await message.edit_reply_markup(
            reply_markup=None
        )
    except Exception as error:
        logger.warning(
            "Не удалось убрать кнопки: %s",
            error,
        )

    if image_path:
        image = BASE_DIR / image_path

        if image.exists():
            await message.answer_photo(
                photo=FSInputFile(image),
                caption=text,
                reply_markup=select_character_keyboard(),
            )
            return

    await message.answer(
        text,
        reply_markup=select_character_keyboard(),
    )

@router.message(CommandStart())
async def start_handler(message: Message):
    logger.info(
        "Пользователь %s запустил игру",
        message.from_user.id,
    )

    await send_start_screen(message)


@router.callback_query(F.data == "select_character")
async def select_character_handler(callback: CallbackQuery):

    await callback.answer()

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception as error:
        logger.warning(
            "Не удалось убрать кнопки: %s",
            error,
        )
    await callback.message.answer(
        "Выберите персонажа",
        reply_markup=character_keyboard(),
    )

@router.callback_query(F.data == "characters")
async def characters_handler(callback: CallbackQuery):

    await callback.answer()

    logger.info(
        "Пользователь %s вернулся к выбору персонажа",
        callback.from_user.id,
    )

    try:
        await callback.message.delete()
    except Exception as error:
        logger.warning(
            "Не удалось удалить сообщение: %s",
            error,
        )

   
    await callback.message.answer(
        "Выберите персонажа",
        reply_markup=character_keyboard(),
    )



@router.callback_query(F.data.startswith("character:"))
async def character_handler(callback: CallbackQuery):

    await callback.answer()

    character_value = callback.data.split(":", 1)[1]

    try:
        character = Character(character_value)
    except ValueError:

        logger.warning(
            "Пользователь %s выбрал неизвестного персонажа: %s",
            callback.from_user.id,
            character_value,
        )

        await callback.answer(
            "Такого персонажа нет.",
            show_alert=True,
        )
        return

    logger.info(
        "Пользователь %s выбрал персонажа %s",
        callback.from_user.id,
        character.value,
    )

    character_data = engine.get_character(character)

    text = (
        f"{character_data.get('description')}\n\n"
        "Вы уверены, что хотите играть за этого персонажа?"
    )

    image_path = character_data.get("image")

 
    if image_path:

        image = BASE_DIR / image_path

        if image.exists():

            try:
                await callback.message.delete()
            except Exception as error:
                logger.warning(
                    "Не удалось удалить сообщение: %s",
                    error,
                )

            await callback.message.answer_photo(
                photo=FSInputFile(image),
                caption=text,
                reply_markup=character_confirm_keyboard(character),
            )

            return

        logger.warning(
            "Картинка персонажа не найдена: %s",
            image,
        )

    # Если картинки нет
    await callback.message.edit_caption(
        caption=text,
        reply_markup=character_confirm_keyboard(character),
    )


@router.callback_query(F.data.startswith("confirm:"))
async def confirm_character_handler(callback: CallbackQuery):

    await callback.answer()

    character_value = callback.data.split(":", 1)[1]

    try:
        character = Character(character_value)
    except ValueError:

        logger.warning(
            "Пользователь %s подтвердил неизвестного персонажа: %s",
            callback.from_user.id,
            character_value,
        )

        await callback.answer(
            "Такого персонажа нет.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id

    logger.info(
        "Пользователь %s начал игру за %s",
        user_id,
        character.value,
    )

    engine.start_game(
        user_id=user_id,
        character=character,
    )
    
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception as error:
        logger.warning(
            "Не удалось убрать кнопки: %s",
            error,
        )
    
    text = engine.get_character_intro(character)
    await callback.message.answer(
        text,
        reply_markup=start_game_keyboard()
    )
    

async def send_scene(message: Message, scene: dict):

    text = scene.get("text")
    option_A = scene.get("options")[0].get("text")
    option_B = scene.get("options")[1].get("text")
    image_path = scene.get("image")
    full_text = f"{text}\n\n{option_A}\n\n{option_B}\n\nЧто выберете?"
    
    if image_path:

        image = BASE_DIR / image_path

        if image.exists():

            await message.answer_photo(
                photo=FSInputFile(image),
                caption=full_text,
                reply_markup=choice_keyboard(),
            )
            
            return

        logger.warning(
            "Картинка сцены не найдена: %s",
            image,
        )

    await message.answer(
        caption=full_text,
        reply_markup=choice_keyboard(),
    )
   

@router.callback_query(F.data.startswith("choice:"))
async def choice_handler(callback: CallbackQuery):

    await callback.answer()

    user_id = callback.from_user.id

    option_index = int(
        callback.data.split(":", 1)[1]
    )

    logger.info(
        "Пользователь %s выбрал вариант %s",
        user_id,
        option_index,
    )

    try:

        choice = engine.make_choice(
            user_id=user_id,
            option_index=option_index,
        )

    except KeyError:

        logger.warning(
            "Не найден игрок %s",
            user_id,
        )

        await callback.message.answer(
            "Похоже, игра не найдена. Используйте /start."
        )

        return

    # Убираем старые кнопки А / Б
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception as error:
        logger.warning(
            "Не удалось убрать кнопки: %s",
            error,
        )

    logger.info(
        "Пользователь %s получил результат выбора",
        user_id,
    )

    await callback.message.answer(
        choice["result"],
        reply_markup=continue_keyboard(),
    )



@router.callback_query(F.data == "continue")
async def continue_handler(callback: CallbackQuery):

    await callback.answer()

    user_id = callback.from_user.id

    logger.info(
        "Пользователь %s нажал ПРОДОЛЖИТЬ",
        user_id,
    )

    try:
        player = engine.get_player(user_id)

    except KeyError:

        logger.warning(
            "Игрок %s не найден",
            user_id,
        )

        await callback.message.answer(
            "Игра не найдена. Используйте /start."
        )

        return

    # Убираем кнопку ПРОДОЛЖИТЬ
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    # Игра закончилась
    if engine.is_game_finished(user_id):

        logger.info(
            "Пользователь %s закончил игру. Очки: %s",
            user_id,
            player.points,
        )

        await send_ending(
            callback.message,
            user_id,
        )

        return

    # Следующая сцена
    scene = engine.get_current_scene(user_id)

    logger.info(
        "Пользователь %s переходит к сцене %s",
        user_id,
        player.scene_num,
    )

    await send_scene(
        callback.message,
        scene,
    )


async def send_ending(
    message: Message,
    user_id: int,
):

    ending = engine.get_ending(user_id)

    text = ending.get("description")
    image_path = ending.get("image")

    if image_path:

        image = BASE_DIR / image_path

        if image.exists():

            await message.answer_photo(
                photo=FSInputFile(image),
                caption=text,
                reply_markup=ending_keyboard(),
                parse_mode="HTML",
            )

            return

        logger.warning(
            "Картинка концовки не найдена: %s",
            image,
        )

    await message.answer(
        text,
        reply_markup=ending_keyboard(),
        parse_mode="HTML",
    )



@router.callback_query(F.data == "restart")
async def restart_handler(callback: CallbackQuery):

    await callback.answer()

    user_id = callback.from_user.id

    logger.info(
        "Пользователь %s начал игру заново",
        user_id,
    )

    engine.reset_player(user_id)

    await send_start_screen(callback.message)


async def main():

    logger.info("Запуск бота...")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    
    await bot.set_my_commands([
        BotCommand(
            command="start",
            description="Начать игру",
        ),
    ])

   
    bot_info = await bot.get_me()

    logger.info(
        "Бот запущен: @%s (id=%s)",
        bot_info.username,
        bot_info.id,
    )

    logger.info("Ожидание сообщений...")

    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())