import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from engine.parser import DrawioParser
from engine.engine import StoryEngine, PlayerState


# ============================================================
# НАСТРОЙКИ
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
STORY_DIR = BASE_DIR / "story" / "plot"

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


# ============================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "Не найдена переменная окружения BOT_TOKEN."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

parser = DrawioParser()


# ============================================================
# СОСТОЯНИЕ ИГРОКОВ
# ============================================================

players: dict[int, dict[str, PlayerState]] = {}
engines: dict[int, dict[str, StoryEngine]] = {}


# ============================================================
# ЗАГРУЗКА ИСТОРИЙ
# ============================================================

def get_story_files() -> list[Path]:
    """Возвращает все .drawio файлы из story/plot."""

    return sorted(STORY_DIR.glob("*.drawio"))


def load_story(story_file: Path):
    """Загружает drawio и превращает его в Story."""

    return parser.parse_file(story_file)


# ============================================================
# СПИСОК ИСТОРИЙ
# ============================================================

def build_story_keyboard() -> InlineKeyboardMarkup:

    files = get_story_files()

    buttons = []

    for index, file in enumerate(files):

        name = file.stem.replace("_", " ").title()

        buttons.append(
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"story:{index}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


async def show_story_list(message: Message):

    files = get_story_files()

    if not files:
        await message.answer(
            "Пока нет доступных историй."
        )
        return

    await message.answer(
        "📖 Выбери историю:",
        reply_markup=build_story_keyboard(),
    )


# ============================================================
# /START
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id

    # При /start возвращаем пользователя
    # в меню выбора историй.
    players.pop(user_id, None)
    engines.pop(user_id, None)

    await show_story_list(message)


# ============================================================
# ПОЛЬЗОВАТЕЛЬ ВЫБРАЛ ИСТОРИЮ
# ============================================================

@dp.callback_query(F.data.startswith("story:"))
async def story_selected(callback: CallbackQuery):

    user_id = callback.from_user.id

    index = int(
        callback.data.split(":")[1]
    )

    files = get_story_files()

    if index < 0 or index >= len(files):

        await callback.answer(
            "История не найдена.",
            show_alert=True,
        )

        return

    story_file = files[index]

    try:

        story = load_story(story_file)

        engine = StoryEngine(story)

        player = engine.new_player()

    except Exception as error:

        logging.exception(
            "Ошибка загрузки истории"
        )

        await callback.answer(
            "Не удалось загрузить историю.",
            show_alert=True,
        )

        await callback.message.answer(
            f"Ошибка загрузки:\n{error}"
        )

        return

    story_name = story_file.stem

    if user_id not in players:
        players[user_id] = {}

    if user_id not in engines:
        engines[user_id] = {}

    players[user_id][story_name] = player
    engines[user_id][story_name] = engine

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await play_story(
        callback.message,
        user_id,
        story_name,
    )


# ============================================================
# ПОКАЗ ИСТОРИИ
# ============================================================

async def play_story(
    message: Message,
    user_id: int,
    story_name: str,
):
    """
    Показывает текущую сцену игроку.

    Линейные сцены проходят автоматически.

    Если встречается выбор — останавливаемся
    и ждем нажатия кнопки.

    Если встречается конец — возвращаем меню.
    """

    player = players[user_id][story_name]
    engine = engines[user_id][story_name]

    while True:

        screen = engine.get_screen(player)

        # ----------------------------------------------------
        # ЕСЛИ ЕСТЬ ВЫБОР
        # ----------------------------------------------------

        if screen.choices:

            keyboard = []

            for text, target in screen.choices:

                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=text,
                            callback_data=(
                                f"choice:"
                                f"{story_name}:"
                                f"{target}"
                            ),
                        )
                    ]
                )

            markup = InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )

            await message.answer(
                screen.text,
                reply_markup=markup,
            )

            return

        # ----------------------------------------------------
        # КОНЕЦ ИСТОРИИ
        # ----------------------------------------------------

        if screen.ending:

            await message.answer(
                screen.text
            )

            await message.answer(
                "✨ История закончена!\n\n"
                "Выбери другую историю:",
                reply_markup=build_story_keyboard(),
            )

            players[user_id].pop(
                story_name,
                None,
            )

            engines[user_id].pop(
                story_name,
                None,
            )

            return

        # ----------------------------------------------------
        # ОБЫЧНАЯ СЦЕНА
        # ----------------------------------------------------

        await message.answer(
            screen.text
        )

        engine.advance(player)


# ============================================================
# ПОЛЬЗОВАТЕЛЬ СДЕЛАЛ ВЫБОР
# ============================================================

@dp.callback_query(F.data.startswith("choice:"))
async def choice_handler(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    # Формат:
    #
    # choice:love_story:scene_id

    parts = callback.data.split(":", 2)

    if len(parts) != 3:

        await callback.answer(
            "Некорректный выбор.",
            show_alert=True,
        )

        return

    _, story_name, target = parts

    if user_id not in players:

        await callback.answer(
            "Игра не найдена. Нажми /start.",
            show_alert=True,
        )

        return

    if story_name not in players[user_id]:

        await callback.answer(
            "Игра не найдена. Нажми /start.",
            show_alert=True,
        )

        return

    player = players[user_id][story_name]
    engine = engines[user_id][story_name]

    try:

        engine.choose(
            player,
            target,
        )

    except ValueError:

        await callback.answer(
            "Этот выбор больше недоступен.",
            show_alert=True,
        )

        return

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await play_story(
        callback.message,
        user_id,
        story_name,
    )


# ============================================================
# ЗАПУСК
# ============================================================

async def main():

    logging.basicConfig(
        level=logging.INFO
    )

    print(
        f"Истории найдены в: {STORY_DIR}"
    )

    files = get_story_files()

    for file in files:
        print(
            f"  - {file.name}"
        )

    print(
        "\nБот запущен."
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())