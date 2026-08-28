from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models import Character

def select_character_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="ВЫБРАТЬ ПЕРСОНАЖА",
                    callback_data="select_character",
                )
            ]
        ]
    )
    
def start_game_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="НАЧАТЬ ИГРУ",
                    callback_data="continue",
                )
            ]
        ]
    )

def character_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            
            [
                InlineKeyboardButton(
                    text="💅 ЛЕРА",
                    callback_data="character:lera",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏛️ САША",
                    callback_data="character:sasha",
                ),
            ],
            [
               InlineKeyboardButton(
                    text="☕ ТЁТЯ ТАНЯ",
                    callback_data="character:tanya",
                    ), 
            ],
            [
                InlineKeyboardButton(
                    text="📣 АНТОН",
                    callback_data="character:anton",
                ),
            ],
                
        ]
    )
    
    
def character_confirm_keyboard (character : Character) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ ПОДТВЕРДИТЬ ВЫБОР",
                    callback_data=f"confirm:{character.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="characters",
                ),
            ],
            
        ]
    )
    
def choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="А",
                    callback_data="choice:0",
                ),
                InlineKeyboardButton(
                    text="Б",
                    callback_data="choice:1",
                ),
            ],
        ]
    )
    
def continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="ПРОДОЛЖИТЬ",
                    callback_data="continue",
                )
            ]
        ]
    )
    
def ending_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                 InlineKeyboardButton(
                    text="🔄 ИГРАТЬ ЗАНОВО",
                    callback_data="restart",
                ),
            ]
        ]
    )