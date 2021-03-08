import numpy as np

from src.reinforcement_learning.memory import Memory
from src.reinforcement_learning.player import Player
from src.environment import Environment

class Runner:

    def __init__(self, player_1: Player, player_2: Player):
        self.player_1 = player_1
        self.player_2 = player_2
        
        self.environment = Environment()
        self.first_player = None
    
    def run(self):
        self.environment.generate_map()

        if self.first_player is None:
            self.first_player = np.random.randint(0, 2)
        else:
            self.first_player = 1 - self.first_player
        


