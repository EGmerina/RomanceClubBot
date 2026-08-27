from dataclasses import dataclass
from enum import Enum

class Character(Enum):
    LERA = "lera"
    SASHA = "sasha"
    TANYA = "tanya"
    ANTON = "anton"

@dataclass
class PlayerState:
    user_id : int
    character : Character
    scene_num: int = 0
    points: int = 0