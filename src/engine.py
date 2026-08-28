import json
from models import PlayerState, Character

class GameEngine:
    def __init__(self):
        self.players : dict[int, PlayerState] ={}
        
        with open("story/text/scenes.json", "r", encoding="utf-8") as file:
            self.scenes = json.load(file)
            
            
    def start_game(self, user_id : int, character: Character):
        self.players[user_id] = PlayerState(
            user_id=user_id, 
            character=character,
            scene_num=0,
            points=0,
        )

    def get_player(self, user_id: int) -> PlayerState:
        return self.players[user_id]
