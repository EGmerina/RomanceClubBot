import json
from models import PlayerState, Character

class GameEngine:
    def __init__(self):
        self.players : dict[int, PlayerState] ={}
        
        with open("story/text/scenes.json", "r", encoding="utf-8") as scenes_file:
            self.scenes = json.load(scenes_file)
        
        with open("story/text/characters.json", "r", encoding="utf-8") as characters_file:
            self.characters = json.load(characters_file)
            
        with open("story/text/endings.json", "r", encoding="utf-8") as endings_file:
            self.endings = json.load(endings_file)
            
            
    def start_game(self, user_id : int, character: Character):
        self.players[user_id] = PlayerState(
            user_id=user_id, 
            character=character,
            scene_num=0,
            points=0,
        )

    def get_player(self, user_id: int) -> PlayerState:
        return self.players[user_id]
    
    def get_intro(self) :
        return self.scenes.get("intro")
    
    def get_character(self, character : Character) :
        return self.characters.get(character.value)
    
    def get_current_scene(self, user_id: int):
        player_state = self.players[user_id]
        steps = self.scenes.get("characters").get(player_state.character.value).get("steps")
        scene = steps[player_state.scene_num]
        return scene
    
    def get_character_intro(self, character: Character):
        return self.scenes.get("characters").get(character.value).get("description")

    def get_ending(self, user_id: int):
        player_state = self.players[user_id]
        return self.endings[player_state.points-1]
    
    def is_game_finished(self, user_id : int):
        player_state = self.players[user_id]
        steps = self.scenes.get("characters").get(player_state.character.value).get("steps")
        return player_state.scene_num >= len(steps)
    
    def make_choice(self, user_id: int , option_index: int):
        player_state = self.players[user_id]
        option = self.scenes.get("characters").get(player_state.character.value).get("steps")[player_state.scene_num].get("options")[option_index]
        player_state.points += option.get("success")
        player_state.scene_num+=1
        return option
    
    def reset_player(self, user_id: int):
        player_state = self.players[user_id]
        player_state.scene_num =0
        player_state.points=0